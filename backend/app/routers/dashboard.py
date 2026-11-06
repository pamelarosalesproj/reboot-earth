"""Inicio del panel: totales del productor (nº de CARs, alertas y embargos)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import current_producer
from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.models import Producer, ProducerCar
from app.reports import get_report
from app.schemas import CnpjOverview, CnpjReport, DashboardSummary
from app.services.cnpj_overview import cnpj_overview
from app.services.cnpj_report import aggregate_cars, cnpj_aggregate, compute_status, details_for, get_score

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
async def dashboard(
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    codes = list(db.exec(select(ProducerCar.car_code).where(ProducerCar.producer_id == producer.id)).all())
    agg = aggregate_cars(await details_for(db, client, codes), len(codes))
    # Mismo código que la ficha pública: el nivel se calcula sobre todo el CNPJ (research R4).
    registered, cnpj_agg = await cnpj_aggregate(db, client, producer.cnpj)
    status = compute_status(cnpj_agg, registered)
    return DashboardSummary(**asdict(agg), cnpj_status=status, cnpj_score=get_score(status))


@router.get("/overview", response_model=CnpjOverview)
async def overview(
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    """Números do CNPJ para o Início (feature 005): CARs, alertas abertas/superadas, embargos vigentes."""
    return await cnpj_overview(db, client, producer.cnpj)


@router.get("/report", response_model=CnpjReport)
async def report(
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    """Relatório do CNPJ (hoje um exemplo; depois o agente). `nivel` = regras, nunca o texto."""
    return await get_report(db, client, producer.cnpj)
