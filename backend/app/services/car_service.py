"""Datos de un CAR desde MapBiomas Alerta + caché de 24 h (research.md R4–R7)."""

import logging
from datetime import timedelta
from typing import Literal

from sqlmodel import Session

from app.config import settings
from app.db import as_utc, utcnow
from app.mapbiomas.client import MapBiomasAuthError, MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.mapbiomas.geo import interior_point, parse_ewkt
from app.mapbiomas.queries import (
    CAR_EMBARGOES_VIA_ALERTS_QUERY,
    CAR_EMBARGOES_VIA_POINT_QUERY,
    CAR_EXISTS_QUERY,
    RURAL_PROPERTY_QUERY,
)
from app.models import CarSnapshot
from app.schemas import Alert, CarDetail, CarSummary, Embargo
from app.sources import SourceUnavailable, ibama

log = logging.getLogger("app.cars")

EmbargoStatus = Literal["ok", "not_determinable", "unavailable"]


# --------------------------------------------------------------------------- #
# Existencia (US1 / US4)
# --------------------------------------------------------------------------- #
async def verify_car_exists(client: MapBiomasClient, code: str) -> Literal["found", "not_in_mapbiomas"]:
    """`ruralProperty` solo devuelve CARs con alertas: null → se acepta igual (decisión R6)."""
    try:
        data = await client.execute(CAR_EXISTS_QUERY, {"code": code})
    except (MapBiomasUnavailable, MapBiomasAuthError):
        raise
    except MapBiomasError as e:
        log.info("verify_car_exists %s: %s", code, e)
        return "not_in_mapbiomas"
    return "found" if data.get("ruralProperty") else "not_in_mapbiomas"


# --------------------------------------------------------------------------- #
# Embargos
# --------------------------------------------------------------------------- #
def merge_embargo_items(items: list[dict]) -> list[Embargo]:
    """Única deduplicación de embargos (princípio IV), para MapBiomas e IBAMA.

    Cada item tem o formato de `embargoedAreas` do MapBiomas (`source`, `processCode`, `code`, `areaHa`,
    `sourceRegisteredAt`, `sourceExpiredAt`, `description`) e, do IBAMA, `term` e `overlap_ha`.
    Agrupa por (órgão, nº de processo) ou (órgão, código) sem processo; junta descrições e soma `overlap_ha`.
    """
    by_process: dict[tuple, dict] = {}
    for e in items:
        key = (e.get("source"), e.get("processCode") or f"code:{e.get('code')}")
        item = by_process.setdefault(key, {
            "source": e.get("source"),
            "process_code": e.get("processCode"),
            "area_ha": e.get("areaHa"),
            "registered_at": e.get("sourceRegisteredAt"),
            "expired_at": e.get("sourceExpiredAt"),
            "descriptions": [],
            "term": e.get("term"),
            "overlap_ha": None,
        })
        if e.get("overlap_ha") is not None:
            item["overlap_ha"] = round((item["overlap_ha"] or 0) + e["overlap_ha"], 2)
        desc = (e.get("description") or "").strip()
        if desc and desc not in item["descriptions"]:
            item["descriptions"].append(desc)
    items_out = sorted(by_process.values(), key=lambda x: str(x["registered_at"] or ""))
    return [Embargo(**i) for i in items_out]


def dedupe_embargoes(rural_properties: list[dict], car_code: str) -> list[Embargo]:
    """Embargos do CAR nas `ruralProperties` do MapBiomas; a API repete o mesmo embargo com outros `code`."""
    return merge_embargo_items([e for rp in rural_properties or [] if rp.get("carCode") == car_code
                                for e in rp.get("embargoedAreas") or []])


async def fetch_car_embargoes(
    client: MapBiomasClient, code: str, geometry: dict | None
) -> tuple[list[Embargo] | None, EmbargoStatus]:
    """Vía 1: a través de una alerta del CAR. Vía 2: pointInformation en un punto interior."""
    try:
        data = await client.execute(CAR_EMBARGOES_VIA_ALERTS_QUERY, {"c": [code], "code": code})
        collection = (data.get("alerts") or {}).get("collection") or []
        if collection:
            return dedupe_embargoes(collection[0].get("ruralProperties") or [], code), "ok"
        if not geometry:
            return None, "not_determinable"
        x, y = interior_point(geometry)
        d = 0.0001
        bbox = {"swLat": y - d, "swLng": x - d, "neLat": y + d, "neLng": x + d}
        data = await client.execute(CAR_EMBARGOES_VIA_POINT_QUERY, {"b": bbox})
        rps = (data.get("pointInformation") or {}).get("ruralProperties") or []
        return dedupe_embargoes(rps, code), "ok"
    except MapBiomasUnavailable:
        return None, "unavailable"
    except MapBiomasError as e:
        log.info("embargos %s no determinables: %s", code, e)
        return None, "not_determinable"


def alert_embargoes_count(alert: dict) -> int | None:
    """Embargos superpuestos a la alerta (research R5), sin repetir el mismo proceso."""
    lst = alert.get("crossedEmbargoesList")
    if isinstance(lst, list) and lst and all(isinstance(x, dict) for x in lst):
        keys = set()
        for x in lst:
            proc = x.get("process_code") or x.get("processCode") or x.get("num_processo")
            src = x.get("source") or x.get("source_name") or x.get("orgao")
            keys.add((src, proc) if proc else ("id", x.get("id") or x.get("code") or repr(x)))
        return len(keys)
    ids = alert.get("crossedEmbargoesIds")
    if ids:
        return len(set(ids))
    total = alert.get("crossedEmbargoesTotal")
    return total if total is not None else None


# --------------------------------------------------------------------------- #
# Resumen + detalle
# --------------------------------------------------------------------------- #
async def build_detail(client: MapBiomasClient, code: str) -> CarDetail:
    """Consulta MapBiomas y construye detalle (incluye el resumen). Propaga MapBiomasUnavailable."""
    data = await client.execute(RURAL_PROPERTY_QUERY, {"code": code})
    prop = data.get("ruralProperty")
    now = utcnow()

    if not prop:
        summary = CarSummary(car_code=code, alerts_count=0, embargoes_count=None,
                             embargoes_status="not_determinable", fetched_at=now)
        return CarDetail(summary=summary, alerts=[], embargoes=[])

    geometry = None
    if prop.get("geomRuralProperty"):
        try:
            _, geometry = parse_ewkt(prop["geomRuralProperty"])
        except ValueError as e:
            log.warning("geometría de %s no interpretable: %s", code, e)

    alerts = []
    for a in prop.get("alerts") or []:
        in_car = sum((c.get("alertAreaInCar") or 0) for c in (a.get("crossedRuralProperties") or [])
                     if c.get("code") in (None, code))
        alerts.append(Alert(
            alert_code=a["alertCode"],
            detected_at=a.get("detectedAt"),
            area_ha=a.get("areaHa"),
            area_in_car_ha=round(in_car, 4),
            embargoes_count=alert_embargoes_count(a),
        ))
    alerts.sort(key=lambda x: x.detected_at.isoformat() if x.detected_at else "", reverse=True)

    embargoes, emb_status = await fetch_car_embargoes(client, code, geometry)
    emb_source = "mapbiomas" if emb_status == "ok" else None
    if emb_status != "ok" and geometry:
        # Feature 007: respaldo com as áreas embargadas do IBAMA (mesma regra de nível, outra fonte).
        try:
            embargoes, emb_status, emb_source = await ibama.fetch_embargoes(geometry), "ok", "ibama"
        except SourceUnavailable as e:
            log.info("embargos IBAMA %s indisponíveis: %s", code, e)
    summary = CarSummary(
        car_code=code,
        state=prop.get("stateAcronym"),
        area_ha=prop.get("areaHa"),
        car_type=prop.get("carType") or prop.get("propertyType"),
        geometry=geometry,
        alerts_count=len(alerts),
        # FR-011: 0 solo si es un dato confirmado.
        embargoes_count=len(embargoes) if emb_status == "ok" and embargoes is not None else None,
        embargoes_status=emb_status,
        embargoes_source=emb_source,
        embargoes_checked_at=now if emb_status == "ok" else None,
        fetched_at=now,
    )
    return CarDetail(summary=summary, alerts=alerts, embargoes=embargoes or [])


def keep_previous_embargoes(new: CarDetail, prev: CarDetail) -> CarDetail:
    """Princípio II: se agora nenhuma fonte determinou os embargos e a cópia anterior sim, mantém a cópia
    anterior marcada como desatualizada (com a data original) em vez de voltar a "indisponível"."""
    if new.summary.embargoes_status == "ok" or prev.summary.embargoes_status != "ok":
        return new
    p = prev.summary
    summary = new.summary.model_copy(update={
        "embargoes_status": "ok", "embargoes_count": p.embargoes_count, "embargoes_stale": True,
        "embargoes_source": p.embargoes_source, "embargoes_checked_at": p.embargoes_checked_at or p.fetched_at,
    })
    return new.model_copy(update={"summary": summary, "embargoes": prev.embargoes})


async def get_detail(db: Session, client: MapBiomasClient, code: str, refresh: bool = False) -> CarDetail:
    """Detalle con caché `CarSnapshot` (TTL 24 h). Si MapBiomas cae, sirve la caché con stale=true."""
    snap = db.get(CarSnapshot, code)
    fresh_limit = utcnow() - timedelta(hours=settings.cache_ttl_hours)
    if snap and snap.detail_json and not refresh and as_utc(snap.fetched_at) >= fresh_limit:
        return CarDetail.model_validate(snap.detail_json)
    try:
        detail = await build_detail(client, code)
    except MapBiomasUnavailable:
        if snap and snap.detail_json:
            cached = CarDetail.model_validate(snap.detail_json)
            cached.summary.stale = True
            return cached
        raise
    if snap and snap.detail_json:
        detail = keep_previous_embargoes(detail, CarDetail.model_validate(snap.detail_json))
    payload = detail.model_dump(mode="json")
    if snap:
        snap.summary_json, snap.detail_json, snap.fetched_at = payload["summary"], payload, detail.summary.fetched_at
    else:
        snap = CarSnapshot(car_code=code, summary_json=payload["summary"], detail_json=payload,
                           fetched_at=detail.summary.fetched_at)
    db.add(snap)
    db.commit()
    return detail


async def get_summary(db: Session, client: MapBiomasClient, code: str, refresh: bool = False) -> CarSummary:
    return (await get_detail(db, client, code, refresh)).summary
