"""Modelos de request/response, alineados con contracts/openapi.yaml."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    cnpj: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AddCarRequest(BaseModel):
    car_code: str


class ProducerCarOut(BaseModel):
    car_code: str
    mapbiomas_status: Literal["found", "not_in_mapbiomas"]
    added_at: datetime


class Me(BaseModel):
    email: str
    cnpj: str
    cars: list[ProducerCarOut]


class CarSummary(BaseModel):
    car_code: str
    state: str | None = None
    area_ha: float | None = None
    car_type: str | None = None
    geometry: dict[str, Any] | None = None
    alerts_count: int | None
    embargoes_count: int | None
    embargoes_status: Literal["ok", "not_determinable", "unavailable"]
    fetched_at: datetime
    stale: bool = False


class Alert(BaseModel):
    alert_code: int
    detected_at: date | None
    area_ha: float | None
    area_in_car_ha: float
    embargoes_count: int | None


class Embargo(BaseModel):
    source: str | None
    process_code: str | None
    area_ha: float | None
    registered_at: date | None
    expired_at: date | None
    descriptions: list[str]


class CarDetail(BaseModel):
    summary: CarSummary
    alerts: list[Alert]
    embargoes: list[Embargo]


class DashboardSummary(BaseModel):
    """Totales del inicio. Alertas y embargos son únicos entre todos los CARs del productor."""

    cars_count: int
    alerts_count: int | None  # None: ningún CAR con datos (MapBiomas no responde y sin caché)
    embargoes_count: int | None  # None: ningún CAR con embargos determinables
    cars_with_data: int
    cars_unavailable: int
    cars_embargoes_unknown: int
    stale: bool
    oldest_fetched_at: datetime | None


class ErrorOut(BaseModel):
    detail: str


class ValidationErrorOut(BaseModel):
    detail: str
    field: str | None = None
    invalid_values: list[str] = []
