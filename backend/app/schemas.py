"""Modelos de request/response, alineados con contracts/openapi.yaml."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class Status(BaseModel):
    """Nivel de un CNPJ (specs/002 data-model.md §Status)."""

    model_config = ConfigDict(extra="forbid")

    level: Literal["gold", "silver", "bronze", "sem_dados"]
    reason: Literal["not_registered", "no_properties", "data_unavailable"] | None  # solo con sem_dados
    partial: bool
    basis: Literal["provisional", "score"]


class Score(BaseModel):
    """Score de un CNPJ. Mientras no exista el método: em_calculo / nao_calculavel (FR-108)."""

    model_config = ConfigDict(extra="forbid")

    state: Literal["em_calculo", "nao_calculavel", "disponivel"]
    value: float | None
    computed_at: datetime | None
    method_version: str | None


class PublicCnpjReport(BaseModel):
    """Ficha pública de un CNPJ. Modelo propio: no reutiliza CarSummary ni Me (FR-105, R8)."""

    model_config = ConfigDict(extra="forbid")

    cnpj: str
    cnpj_formatted: str
    registered: bool
    status: Status
    score: Score
    cars_count: int
    cars_with_data: int
    stale: bool
    data_as_of: datetime | None


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
    # Feature 002: nivel y score a nivel CNPJ, idénticos a la ficha pública (FR-114, SC-106).
    cnpj_status: Status
    cnpj_score: Score


class ErrorOut(BaseModel):
    detail: str


class ValidationErrorOut(BaseModel):
    detail: str
    field: str | None = None
    invalid_values: list[str] = []
