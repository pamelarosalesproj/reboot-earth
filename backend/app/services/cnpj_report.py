"""Agregación por CAR/CNPJ, nivel (status) y score.

Única fuente de verdad para el panel del productor y la ficha pública
(constitución IV; specs/002-cnpj-score-search/data-model.md).
"""

import asyncio
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.models import Producer, ProducerCar
from app.schemas import CarDetail, CarIndicators, PublicCnpjReport, Score, Status
from app.services.car_indicators import get_indicators
from app.services.car_service import get_detail
from app.services.level_rules import car_level, cnpj_level


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


def cnpj_codes(db: Session, cnpj: str) -> tuple[bool, list[str]]:
    """(registrado, CARs sem repetir de todas as contas com esse CNPJ) (research R4 da 002)."""
    producer_ids = db.exec(select(Producer.id).where(Producer.cnpj == cnpj)).all()
    if not producer_ids:
        return False, []
    return True, sorted(set(db.exec(
        select(ProducerCar.car_code).where(ProducerCar.producer_id.in_(producer_ids))  # type: ignore[union-attr]
    ).all()))


async def indicators_or_none(db: Session, client: MapBiomasClient, code: str) -> CarIndicators | None:
    try:
        return await get_indicators(db, client, code)
    except Exception:  # noqa: BLE001 — sem indicadores o nível marca dados parciais, nunca quebra
        return None


async def _inputs_one(bind: Engine, client: MapBiomasClient, code: str) -> tuple[CarDetail | None, CarIndicators | None]:
    detail = await _detail_or_none(bind, client, code)
    with Session(bind) as db:
        return detail, await indicators_or_none(db, client, code)


async def car_inputs(db: Session, client: MapBiomasClient,
                     codes: list[str]) -> list[tuple[CarDetail | None, CarIndicators | None]]:
    """Detalhe (001) e indicadores (003) de cada CAR, em paralelo: as entradas da regra de nível."""
    return list(await asyncio.gather(*(_inputs_one(db.get_bind(), client, c) for c in codes)))


async def car_status(db: Session, client: MapBiomasClient, detail: CarDetail) -> Status:
    """Nível de um CAR já carregado (feature 006)."""
    ind = await indicators_or_none(db, client, detail.summary.car_code)
    return car_level(detail, ind, date.today())


async def cnpj_status(db: Session, client: MapBiomasClient, cnpj: str) -> tuple[bool, Status, CarsAggregate]:
    """(registrado, nível, agregado) de um CNPJ normalizado. Nunca propaga erros das fontes."""
    registered, codes = cnpj_codes(db, cnpj)
    inputs = await car_inputs(db, client, codes)
    today = date.today()
    status = cnpj_level([car_level(d, i, today) for d, i in inputs], registered)
    return registered, status, aggregate_cars([d for d, _ in inputs], len(codes))


def format_cnpj(digits: str) -> str:
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


async def build_public_report(db: Session, client: MapBiomasClient, cnpj: str) -> PublicCnpjReport:
    registered, status, agg = await cnpj_status(db, client, cnpj)
    return PublicCnpjReport(
        cnpj=cnpj,
        cnpj_formatted=format_cnpj(cnpj),
        registered=registered,
        status=status,
        score=get_score(status),
        cars_count=agg.cars_count,
        cars_with_data=agg.cars_with_data,
        stale=agg.stale,
        data_as_of=agg.oldest_fetched_at,
    )
