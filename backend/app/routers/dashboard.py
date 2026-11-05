"""Inicio del panel: totales del productor (nº de CARs, alertas y embargos)."""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.auth import current_producer
from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable, get_mapbiomas_client
from app.models import Producer, ProducerCar
from app.schemas import CarDetail, DashboardSummary
from app.services.car_service import get_detail

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _detail_or_none(bind: Engine, client: MapBiomasClient, code: str) -> CarDetail | None:
    """Detalle de un CAR (con caché); None si MapBiomas no responde y no hay caché."""
    with Session(bind) as db:  # una sesión por CAR: las consultas corren en paralelo
        try:
            return await get_detail(db, client, code)
        except (MapBiomasUnavailable, MapBiomasError):
            return None


@router.get("", response_model=DashboardSummary)
async def dashboard(
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    codes = db.exec(select(ProducerCar.car_code).where(ProducerCar.producer_id == producer.id)).all()
    details = await asyncio.gather(*(_detail_or_none(db.get_bind(), client, c) for c in codes))
    ok = [d for d in details if d is not None]

    # Únicos entre todos los CARs: una alerta o embargo que cruza dos CARs cuenta una vez.
    alert_codes = {a.alert_code for d in ok for a in d.alerts}
    emb_known = [d for d in ok if d.summary.embargoes_status == "ok"]
    embargo_keys = {(e.source, e.process_code) for d in emb_known for e in d.embargoes}
    fetched = [d.summary.fetched_at for d in ok]

    return DashboardSummary(
        cars_count=len(codes),
        alerts_count=len(alert_codes) if ok or not codes else None,
        embargoes_count=len(embargo_keys) if emb_known or not codes else None,
        cars_with_data=len(ok),
        cars_unavailable=len(codes) - len(ok),
        cars_embargoes_unknown=len(ok) - len(emb_known),
        stale=any(d.summary.stale for d in ok),
        oldest_fetched_at=min(fetched) if fetched else None,
    )
