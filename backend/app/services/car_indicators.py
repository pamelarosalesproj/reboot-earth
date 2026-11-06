"""Indicadores socioambientales por CAR (feature 003).

Única fuente de verdad (constitución IV) para la tarjeta y el detalle. Cada fuente se resuelve
de forma independiente; si una falla se reutiliza su bloque de la caché (stale) o queda
"indisponivel" — nunca se propaga el error (constitución II).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import date, timedelta

import httpx
from sqlmodel import Session

from app.config import settings
from app.db import as_utc, utcnow
from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.mapbiomas.queries import ALERT_INDICATORS_QUERY, JUDICIAL_ALERTS_QUERY
from app.models import CarIndicatorsSnapshot
from app.schemas import (
    OPEN_SITUACOES,
    SITUACOES,
    AlertIndicator,
    CarDetail,
    CarIndicators,
    Context,
    Count,
    Deter,
    Embargo,
    Hotspots,
    NativeVegetation,
    OpenRisks,
    Situacao,
    SourceStatus,
)
from app.services.car_service import get_detail
from app.sources import SourceUnavailable, inpe, sinaflor
from app.sources.geo import car_polygon

log = logging.getLogger("app.indicators")

EUDR_CUTOFF = date(2020, 12, 31)
SOURCES = ("mapbiomas", "prodes", "deter", "focos", "sinaflor")
# Qué campos del payload pertenecen a cada fuente (para reutilizarlos de la caché si falla).
MAPBIOMAS_CONTEXT = ("embargoes_lifted", "sustainable_use_ha", "sustainable_use_names")
CONTEXT_FIELD = {"prodes": "native_vegetation", "deter": "deter", "focos": "hotspots_12m",
                 "sinaflor": "forest_management"}


def _f(x) -> float:
    return float(x or 0)


# --------------------------------------------------------------------------- #
# Situación de la alerta (FR-301/302)
# --------------------------------------------------------------------------- #
def classify_alert(raw: dict, embargoes: list[Embargo] | None, embargoes_status: str,
                   judicial_codes: set[int]) -> Situacao:
    """Una sola situación; gana la primera que se cumple (data-model.md)."""
    crosses_embargo = _f(raw.get("crossedEmbargoesArea")) > 0
    all_lifted = embargoes_status == "ok" and bool(embargoes) and all(e.expired_at for e in embargoes)
    if raw.get("alertCode") in judicial_codes:
        return "suspensa_judicial"
    if crosses_embargo and not all_lifted:
        return "embargo_vigente"
    if _f(raw.get("crossedDeforestationAuthorizationsArea")) + _f(raw.get("crossedForestManagementsArea")) > 0:
        return "autorizada"
    if crosses_embargo:
        return "embargo_levantado"
    if raw.get("actionsList"):
        return "com_fiscalizacao"
    return "pendente"


def _sum(raw: dict, *keys: str) -> float:
    return sum(_f(raw.get(k)) for k in keys)


def _uc_names(raw: dict) -> list[str]:
    names = []
    for u in raw.get("crossedConservationUnitsList") or []:
        name = u.get("name") if isinstance(u, dict) else str(u)
        if name and name not in names:
            names.append(name)
    return names[:3]


def alert_indicator(raw: dict, code: str, status: Situacao) -> AlertIndicator:
    in_car = next((r.get("alertAreaInCar") for r in raw.get("crossedRuralProperties") or []
                   if r.get("code") == code and r.get("alertAreaInCar") is not None), None)
    detected = date.fromisoformat(raw["detectedAt"]) if raw.get("detectedAt") else None
    area = _f(in_car if in_car is not None else raw.get("areaHa"))

    def cap(v: float) -> float:
        # MapBiomas calcula RL/TI/UC sobre la alerta completa (puede incluir vecinos): se limita
        # al área de la alerta dentro de este CAR para no mostrar superposiciones imposibles.
        return round(min(v, area), 4)

    return AlertIndicator(
        alert_code=raw["alertCode"],
        detected_at=detected,
        area_in_car_ha=round(area, 4),
        status=status,
        post_2020=bool(detected and detected > EUDR_CUTOFF),
        authorized_ha=round(_sum(raw, "crossedDeforestationAuthorizationsArea", "crossedForestManagementsArea"), 4),
        legal_reserve_ha=cap(_f(raw.get("crossedLegalReservesArea"))),
        touches_app=bool(raw.get("crossedPermanentProtectedAreaTotal")),
        indigenous_land_ha=cap(_f(raw.get("crossedIndigenousLandsArea"))),
        integral_protection_ha=cap(_sum(raw, "crossedFederalProtectedAreaIntegralProtectionsArea",
                                        "crossedStateProtectedAreaIntegralProtectionsArea",
                                        "crossedMunicipalityProtectedAreaIntegralProtectionsArea")),
        sustainable_use_ha=cap(_sum(raw, "crossedFederalProtectedAreaSustainableUsesArea",
                                    "crossedStateProtectedAreaSustainableUsesArea",
                                    "crossedMunicipalityProtectedAreaSustainableUsesArea")),
        conservation_units=_uc_names(raw),
    )


async def mapbiomas_block(client: MapBiomasClient, code: str, detail: CarDetail | None) -> dict:
    """Alertas por situación + riesgos abiertos + contexto de MapBiomas. Propaga si MapBiomas falla."""
    data = await client.execute(ALERT_INDICATORS_QUERY, {"c": [code]})
    raws = ((data.get("alerts") or {}).get("collection")) or []
    try:
        j = await client.execute(JUDICIAL_ALERTS_QUERY, {"c": code})
        judicial = {a["alertCode"] for a in (j.get("findSuspendedJudicialAlert") or [])}
    except (MapBiomasError, MapBiomasUnavailable) as e:  # no fatal: se clasifica sin ella
        log.info("suspensión judicial no disponible para %s: %s", code, str(e)[:120])
        judicial = set()

    emb_status = detail.summary.embargoes_status if detail else "not_determinable"
    embargoes = detail.embargoes if detail else None
    alerts = [alert_indicator(r, code, classify_alert(r, embargoes, emb_status, judicial)) for r in raws]
    alerts.sort(key=lambda a: a.detected_at or date.min, reverse=True)

    by_status = {s: Count() for s in SITUACOES}
    for a in alerts:
        c = by_status[a.status]
        c.n += 1
        c.ha = round(c.ha + a.area_in_car_ha, 4)
    opened = [a for a in alerts if a.status in OPEN_SITUACOES]
    post = [a for a in alerts if a.post_2020]
    known = emb_status == "ok" and embargoes is not None
    names: list[str] = []
    for a in alerts:
        if a.sustainable_use_ha > 0:
            names += [n for n in a.conservation_units if n not in names]
    return {
        "alerts": alerts,
        "alerts_by_status": by_status,
        "open": OpenRisks(
            post_2020=Count(n=len(post), ha=round(sum(a.area_in_car_ha for a in post), 4)),
            legal_reserve_ha=round(sum(a.legal_reserve_ha for a in opened), 4),
            app_alerts=sum(a.touches_app for a in opened),
            embargoes_active=sum(1 for e in embargoes if not e.expired_at) if known else None,
            indigenous_land_ha=round(sum(a.indigenous_land_ha for a in alerts), 4),
            integral_protection_ha=round(sum(a.integral_protection_ha for a in alerts), 4),
        ),
        "context": {
            "embargoes_lifted": sum(1 for e in embargoes if e.expired_at) if known else None,
            "sustainable_use_ha": round(sum(a.sustainable_use_ha for a in alerts), 4),
            "sustainable_use_names": names[:5],
        },
    }


# --------------------------------------------------------------------------- #
# Ensamblado con caché y fallos por fuente (R5)
# --------------------------------------------------------------------------- #
class NotApplicable(Exception):
    pass


async def _run(fn: Callable[[], Awaitable]):
    try:
        return "ok", await fn()
    except NotApplicable:
        return "nao_se_aplica", None
    except (SourceUnavailable, MapBiomasError, MapBiomasUnavailable, httpx.HTTPError) as e:
        log.info("fuente no disponible: %s", str(e)[:160])
        return "indisponivel", None
    except Exception:  # una fuente nunca tumba la tarjeta (constitución II)
        log.exception("error inesperado en una fuente de indicadores")
        return "indisponivel", None


async def build_indicators(db: Session, client: MapBiomasClient, code: str, prev: CarIndicators | None,
                           today: date | None = None) -> CarIndicators:
    today = today or date.today()
    now = utcnow()
    try:
        detail = await get_detail(db, client, code)
    except (MapBiomasError, MapBiomasUnavailable):
        detail = None
    geom = None
    if detail and detail.summary.geometry:
        try:
            geom = car_polygon(detail.summary.geometry)
        except Exception:
            log.exception("geometría de %s no interpretable", code)

    async def need_geom():
        if geom is None:
            raise SourceUnavailable("sin geometría del CAR")
        return geom

    async with httpx.AsyncClient() as http:
        biomes_task = asyncio.ensure_future(_run(lambda: _biomes(http, need_geom)))

        async def prodes():
            status, b = await biomes_task
            if status != "ok":
                raise SourceUnavailable("biomas no disponibles")
            return NativeVegetation(**await inpe.prodes_loss(http, await need_geom(), b))

        async def deter():
            status, b = await biomes_task
            if status != "ok":
                raise SourceUnavailable("biomas no disponibles")
            if "Amazônia" not in b:
                raise NotApplicable
            return Deter(**await inpe.deter_by_class(http, await need_geom()))

        async def focos():
            return Hotspots(**await inpe.hotspots_12m(http, await need_geom(), today))

        async def forest():
            status, block = sinaflor.forest_management(db, code)
            if status == "nao_se_aplica":
                raise NotApplicable
            if status == "indisponivel":
                raise SourceUnavailable("SINAFLOR nunca sincronizado")
            return block

        results = dict(zip(SOURCES, await asyncio.gather(
            _run(lambda: mapbiomas_block(client, code, detail)), _run(prodes), _run(deter), _run(focos),
            _run(forest),
        )))

    sources: dict[str, SourceStatus] = {}
    out = {"alerts": [], "alerts_by_status": {}, "open": OpenRisks(), "context": Context()}
    for src, (status, value) in results.items():
        if status == "indisponivel" and prev and prev.sources.get(src) and prev.sources[src].status == "ok":
            sources[src] = SourceStatus(status="ok", fetched_at=prev.sources[src].fetched_at, stale=True)
            _copy_from_prev(out, prev, src)
            continue
        sources[src] = SourceStatus(status=status, fetched_at=now if status == "ok" else None)
        if status != "ok":
            continue
        if src == "mapbiomas":
            out["alerts"], out["alerts_by_status"], out["open"] = value["alerts"], value["alerts_by_status"], value["open"]
            for k, v in value["context"].items():
                setattr(out["context"], k, v)
        else:
            setattr(out["context"], CONTEXT_FIELD[src], value)
    return CarIndicators(car_code=code, fetched_at=now, stale=any(s.stale for s in sources.values()),
                         sources=sources, **out)


async def _biomes(http, need_geom):
    return await inpe.biomes(http, await need_geom())


def _copy_from_prev(out: dict, prev: CarIndicators, src: str) -> None:
    if src == "mapbiomas":
        out["alerts"], out["alerts_by_status"], out["open"] = prev.alerts, prev.alerts_by_status, prev.open
        for k in MAPBIOMAS_CONTEXT:
            setattr(out["context"], k, getattr(prev.context, k))
    else:
        setattr(out["context"], CONTEXT_FIELD[src], getattr(prev.context, CONTEXT_FIELD[src]))


def _with_fresh_sinaflor(db: Session, ind: CarIndicators) -> CarIndicators:
    """SINAFLOR es una tabla local (lectura instantánea): se lee siempre en el momento, para que
    una sincronización nueva se vea sin esperar a que caduque la caché de las fuentes externas."""
    status, block = sinaflor.forest_management(db, ind.car_code)
    ind.sources["sinaflor"] = SourceStatus(status=status, fetched_at=utcnow() if status == "ok" else None)
    ind.context.forest_management = block
    return ind


async def get_indicators(db: Session, client: MapBiomasClient, code: str, refresh: bool = False,
                         today: date | None = None) -> CarIndicators:
    """Caché `car_indicators_snapshot` de 24 h (como la de 001)."""
    snap = db.get(CarIndicatorsSnapshot, code)
    fresh_limit = utcnow() - timedelta(hours=settings.cache_ttl_hours)
    if snap and not refresh and as_utc(snap.fetched_at) >= fresh_limit:
        return _with_fresh_sinaflor(db, CarIndicators.model_validate(snap.payload))
    prev = CarIndicators.model_validate(snap.payload) if snap else None
    result = await build_indicators(db, client, code, prev, today)
    payload = result.model_dump(mode="json")
    if snap:
        snap.payload, snap.fetched_at = payload, result.fetched_at
    else:
        snap = CarIndicatorsSnapshot(car_code=code, payload=payload, fetched_at=result.fetched_at)
    db.add(snap)
    db.commit()
    return result
