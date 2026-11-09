from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.auth import current_producer
from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.models import Producer, ProducerCar
from app.schemas import (
    AddCarRequest,
    CarDetail,
    CarIndicators,
    CarSummary,
    ProducerCarOut,
    ValidationErrorOut,
)
from app.services.car_indicators import get_indicators
from app.services.car_service import get_detail, verify_car_exists
from app.services.cnpj_report import car_status
from app.validators import normalize_car

router = APIRouter(prefix="/cars", tags=["cars"])


def own_car(db: Session, producer: Producer, car_code: str) -> ProducerCar:
    """FR-006: solo CARs del productor autenticado; si no, 404."""
    code = car_code.strip().upper()
    car = db.exec(select(ProducerCar).where(ProducerCar.producer_id == producer.id,
                                            ProducerCar.car_code == code)).first()
    if not car:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CAR não encontrado na sua conta")
    return car


@router.get("", response_model=list[ProducerCarOut])
def list_cars(producer: Producer = Depends(current_producer), db: Session = Depends(get_session)):
    cars = db.exec(select(ProducerCar).where(ProducerCar.producer_id == producer.id)
                   .order_by(ProducerCar.added_at)).all()
    return [ProducerCarOut.model_validate(c, from_attributes=True) for c in cars]


@router.post("", status_code=201, response_model=ProducerCarOut)
async def add_car(
    req: AddCarRequest,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    try:
        code = normalize_car(req.car_code)
    except ValueError as e:
        body = ValidationErrorOut(detail=str(e), field="car_code", invalid_values=[req.car_code])
        return JSONResponse(body.model_dump(), status_code=422)
    exists = db.exec(select(ProducerCar).where(ProducerCar.producer_id == producer.id,
                                               ProducerCar.car_code == code)).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este CAR já está na sua conta")
    mb_status = await verify_car_exists(client, code)
    car = ProducerCar(producer_id=producer.id, car_code=code, mapbiomas_status=mb_status)
    db.add(car)
    db.commit()
    db.refresh(car)
    return ProducerCarOut.model_validate(car, from_attributes=True)


@router.delete("/{car_code}", status_code=204)
def remove_car(car_code: str, producer: Producer = Depends(current_producer),
               db: Session = Depends(get_session)):
    car = own_car(db, producer, car_code)
    db.delete(car)
    db.commit()
    return Response(status_code=204)


@router.get("/{car_code}/summary", response_model=CarSummary)
async def car_summary(
    car_code: str,
    refresh: bool = False,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    car = own_car(db, producer, car_code)
    detail = await get_detail(db, client, car.car_code, refresh)
    return detail.summary.model_copy(update={"status": await car_status(db, client, detail)})


@router.get("/{car_code}/detail", response_model=CarDetail)
async def car_detail(
    car_code: str,
    refresh: bool = False,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    car = own_car(db, producer, car_code)
    detail = await get_detail(db, client, car.car_code, refresh)
    status = await car_status(db, client, detail)
    return detail.model_copy(update={"summary": detail.summary.model_copy(update={"status": status})})


@router.get("/{car_code}/indicators", response_model=CarIndicators)
async def car_indicators(
    car_code: str,
    refresh: bool = False,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    """Indicadores socioambientales (feature 003). Siempre 200 para un CAR propio."""
    car = own_car(db, producer, car_code)
    return await get_indicators(db, client, car.car_code, refresh)
