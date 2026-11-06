"""Números del CNPJ para el Início (feature 005).

Reutiliza la situación de cada alerta de la feature 003 (`get_indicators` → `classify_alert`) y los
embargos de la feature 001 (`get_detail`): no hay una segunda implementación de las reglas
(constitución IV).
"""

import asyncio

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.models import Producer, ProducerCar
from app.schemas import OPEN_SITUACOES, CarDetail, CarIndicators, CnpjOverview, Count
from app.services.car_indicators import get_indicators
from app.services.car_service import get_detail


async def _car_data(bind: Engine, client: MapBiomasClient, code: str) -> tuple[CarIndicators | None, CarDetail | None]:
    with Session(bind) as db:  # una sesión por CAR: corren en paralelo
        try:
            detail = await get_detail(db, client, code)
        except (MapBiomasUnavailable, MapBiomasError):
            detail = None
        ind = await get_indicators(db, client, code)  # nunca propaga errores de fuentes
    return ind, detail


async def cnpj_overview(db: Session, client: MapBiomasClient, cnpj: str) -> CnpjOverview:
    ids = db.exec(select(Producer.id).where(Producer.cnpj == cnpj)).all()
    codes = sorted(set(db.exec(
        select(ProducerCar.car_code).where(ProducerCar.producer_id.in_(ids))  # type: ignore[union-attr]
    ).all())) if ids else []
    results = await asyncio.gather(*(_car_data(db.get_bind(), client, c) for c in codes))

    alerts: dict[int, bool] = {}  # código → abierta en algún CAR
    open_ha = superseded_ha = 0.0
    without_alerts = 0
    embargo_keys: set[tuple] = set()
    emb_known = emb_unknown = 0
    fetched = []
    for ind, detail in results:
        if ind is None or ind.sources["mapbiomas"].status != "ok":
            without_alerts += 1
        else:
            fetched.append(ind.fetched_at)
            for a in ind.alerts:
                is_open = a.status in OPEN_SITUACOES
                alerts[a.alert_code] = alerts.get(a.alert_code, False) or is_open
                if is_open:
                    open_ha += a.area_in_car_ha
                else:
                    superseded_ha += a.area_in_car_ha
        if detail is not None and detail.summary.embargoes_status == "ok":
            emb_known += 1
            embargo_keys |= {(e.source, e.process_code) for e in detail.embargoes if not e.expired_at}
        else:
            emb_unknown += 1

    has_alert_data = without_alerts < len(codes) or not codes
    n_open = sum(alerts.values())
    return CnpjOverview(
        cars_count=len(codes),
        alerts_total=len(alerts) if has_alert_data else None,
        open_alerts=Count(n=n_open, ha=round(open_ha, 4)) if has_alert_data else None,
        superseded_alerts=Count(n=len(alerts) - n_open, ha=round(superseded_ha, 4)) if has_alert_data else None,
        embargoes_active=len(embargo_keys) if emb_known or not codes else None,
        cars_without_alert_data=without_alerts,
        cars_embargoes_unknown=emb_unknown,
        data_as_of=min(fetched) if fetched else None,
    )
