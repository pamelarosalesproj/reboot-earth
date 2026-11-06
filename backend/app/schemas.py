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
    # Nível do CAR: a mesma regra do CNPJ aplicada só a este imóvel (o painel o preenche; nunca é público).
    status: "Status | None" = None


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
    # Conteos que usó la regla (agregados, públicos): permiten explicar el nivel con números.
    alerts_count: int | None = None
    embargoes_count: int | None = None


CarSummary.model_rebuild()  # resolve a referência a Status (definido depois)


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


# ---------------------------------------------------------------------------
# Feature 003: indicadores del CAR (specs/003-car-indicators/contracts/openapi.yaml)
# ---------------------------------------------------------------------------
Situacao = Literal["suspensa_judicial", "embargo_vigente", "autorizada", "embargo_levantado",
                   "com_fiscalizacao", "pendente"]
SITUACOES: tuple[str, ...] = ("suspensa_judicial", "embargo_vigente", "autorizada", "embargo_levantado",
                              "com_fiscalizacao", "pendente")
OPEN_SITUACOES = ("embargo_vigente", "com_fiscalizacao", "pendente")
SourceName = Literal["mapbiomas", "prodes", "deter", "focos", "sinaflor"]


class SourceStatus(BaseModel):
    status: Literal["ok", "indisponivel", "nao_se_aplica"]
    fetched_at: datetime | None = None
    stale: bool = False


class Count(BaseModel):
    n: int = 0
    ha: float = 0.0


class AlertIndicator(BaseModel):
    alert_code: int
    detected_at: date | None
    area_in_car_ha: float
    status: Situacao
    post_2020: bool
    authorized_ha: float
    legal_reserve_ha: float
    touches_app: bool
    indigenous_land_ha: float
    integral_protection_ha: float
    sustainable_use_ha: float
    conservation_units: list[str] = []


class OpenRisks(BaseModel):
    post_2020: Count | None = None
    legal_reserve_ha: float | None = None
    app_alerts: int | None = None
    embargoes_active: int | None = None
    indigenous_land_ha: float | None = None
    integral_protection_ha: float | None = None


class NativeVegetation(BaseModel):
    remaining_pct: float
    deforested_ha: float
    by_year: dict[str, float] = {}


class DeterClass(BaseModel):
    n: int
    ha: float
    last: str | None = None


class Deter(BaseModel):
    by_class: dict[str, DeterClass] = {}


class Hotspots(BaseModel):
    count: int
    by_month: dict[str, int] = {}


class ForestManagement(BaseModel):
    authorizations: int
    active: int
    volume_m3: float
    last_issued: date | None = None


class Context(BaseModel):
    embargoes_lifted: int | None = None
    sustainable_use_ha: float | None = None
    sustainable_use_names: list[str] = []
    native_vegetation: NativeVegetation | None = None
    deter: Deter | None = None
    hotspots_12m: Hotspots | None = None
    forest_management: ForestManagement | None = None


class CarIndicators(BaseModel):
    car_code: str
    fetched_at: datetime
    stale: bool = False
    sources: dict[SourceName, SourceStatus]
    alerts_by_status: dict[Situacao, Count]
    open: OpenRisks
    context: Context
    alerts: list[AlertIndicator] = []


# ---------------------------------------------------------------------------
# Feature 005: Início como resumo do CNPJ (specs/005-dashboard-init/contracts/openapi.yaml)
# ---------------------------------------------------------------------------
class CnpjOverview(BaseModel):
    cars_count: int
    alerts_total: int | None
    open_alerts: Count | None
    superseded_alerts: Count | None
    embargoes_active: int | None
    cars_without_alert_data: int
    cars_embargoes_unknown: int
    data_as_of: datetime | None


class ReportProperty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    car_code: str
    resumo: str


class CnpjReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "indisponivel"]
    origem: Literal["exemplo", "agente"] | None = None
    nivel: Literal["gold", "silver", "bronze", "sem_dados"] | None = None
    titulo: str | None = None
    riscos: list[str] = Field(default_factory=list, max_length=3)
    contexto: list[str] = Field(default_factory=list, max_length=3)
    ressalvas: list[str] = []
    imoveis: list[ReportProperty] = []
    data_dos_dados: date | None = None
    gerado_em: datetime | None = None
