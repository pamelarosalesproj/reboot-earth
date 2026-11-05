"""Agregación por CAR/CNPJ, nivel (status) y score.

Única fuente de verdad para el panel del productor y la ficha pública
(constitución IV; specs/002-cnpj-score-search/data-model.md).
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.models import Producer, ProducerCar
from app.schemas import CarDetail, PublicCnpjReport, Score, Status
from app.services.car_service import get_detail


@dataclass(frozen=True)
class CarsAggregate:
    cars_count: int
    cars_with_data: int
    cars_unavailable: int
    cars_embargoes_unknown: int
    alerts_count: int | None  # None: ningún CAR con datos (nunca 0 falso, constitución II)
    embargoes_count: int | None  # None: ningún CAR con embargos determinables
    stale: bool
    oldest_fetched_at: datetime | None


def aggregate_cars(details: list[CarDetail | None], cars_count: int) -> CarsAggregate:
    """Totales sobre detalles de CAR (None = sin datos). Alertas únicas por código y
    embargos únicos por (órgano, proceso): una alerta o embargo que cruza dos CARs cuenta una vez."""
    ok = [d for d in details if d is not None]
    alert_codes = {a.alert_code for d in ok for a in d.alerts}
    emb_known = [d for d in ok if d.summary.embargoes_status == "ok"]
    embargo_keys = {(e.source, e.process_code) for d in emb_known for e in d.embargoes}
    fetched = [d.summary.fetched_at for d in ok]
    return CarsAggregate(
        cars_count=cars_count,
        cars_with_data=len(ok),
        cars_unavailable=cars_count - len(ok),
        cars_embargoes_unknown=len(ok) - len(emb_known),
        alerts_count=len(alert_codes) if ok or not cars_count else None,
        embargoes_count=len(embargo_keys) if emb_known or not cars_count else None,
        stale=any(d.summary.stale for d in ok),
        oldest_fetched_at=min(fetched) if fetched else None,
    )


def compute_status(agg: CarsAggregate | None, registered: bool) -> Status:
    """Regla provisional FR-111a, evaluada en orden (gana la primera que se cumple)."""
    partial = bool(agg and (agg.cars_unavailable > 0 or agg.cars_embargoes_unknown > 0))

    def status(level, reason=None):
        return Status(level=level, reason=reason, partial=partial, basis="provisional")

    if not registered:
        return status("sem_dados", "not_registered")
    if agg is None or agg.cars_count == 0:
        return status("sem_dados", "no_properties")
    if agg.cars_with_data == 0:
        return status("sem_dados", "data_unavailable")
    if (agg.embargoes_count or 0) >= 1:
        return status("bronze")
    if (agg.alerts_count or 0) >= 1 or partial:
        return status("silver")
    return status("gold")


def get_score(status: Status) -> Score:
    """Score del CNPJ. Aún no existe método de cálculo: devuelve solo el estado.

    Punto de sustitución (FR-110, research R3): cuando exista el método, esta función
    devolverá state="disponivel" con value/computed_at/method_version, y el nivel pasará a
    derivarse del score (Status.basis="score", FR-111b) sin cambiar el contrato ni la UI.
    """
    state = "nao_calculavel" if status.level == "sem_dados" else "em_calculo"
    return Score(state=state, value=None, computed_at=None, method_version=None)


async def _detail_or_none(bind: Engine, client: MapBiomasClient, code: str) -> CarDetail | None:
    """Detalle de un CAR (con caché); None si MapBiomas no responde y no hay caché."""
    with Session(bind) as db:  # una sesión por CAR: las consultas corren en paralelo
        try:
            return await get_detail(db, client, code)
        except (MapBiomasUnavailable, MapBiomasError):
            return None


async def details_for(db: Session, client: MapBiomasClient, codes: list[str]) -> list[CarDetail | None]:
    return list(await asyncio.gather(*(_detail_or_none(db.get_bind(), client, c) for c in codes)))


async def cnpj_aggregate(db: Session, client: MapBiomasClient, cnpj: str) -> tuple[bool, CarsAggregate | None]:
    """(registrado, agregado) de un CNPJ normalizado, sumando los CARs sin repetir de todas
    las cuentas con ese CNPJ (research R4). Nunca propaga errores de MapBiomas."""
    producer_ids = db.exec(select(Producer.id).where(Producer.cnpj == cnpj)).all()
    if not producer_ids:
        return False, None
    codes = sorted(set(db.exec(
        select(ProducerCar.car_code).where(ProducerCar.producer_id.in_(producer_ids))  # type: ignore[union-attr]
    ).all()))
    return True, aggregate_cars(await details_for(db, client, codes), len(codes))


def format_cnpj(digits: str) -> str:
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


async def build_public_report(db: Session, client: MapBiomasClient, cnpj: str) -> PublicCnpjReport:
    registered, agg = await cnpj_aggregate(db, client, cnpj)
    status = compute_status(agg, registered)
    return PublicCnpjReport(
        cnpj=cnpj,
        cnpj_formatted=format_cnpj(cnpj),
        registered=registered,
        status=status,
        score=get_score(status),
        cars_count=agg.cars_count if agg else 0,
        cars_with_data=agg.cars_with_data if agg else 0,
        stale=agg.stale if agg else False,
        data_as_of=agg.oldest_fetched_at if agg else None,
    )
