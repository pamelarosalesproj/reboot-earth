"""Schemas para auditoria de NF e cruzamento com CAR via IA."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceWoodItem(BaseModel):
    """Item ou produto de madeira listado na Nota Fiscal."""

    model_config = ConfigDict(extra="ignore")

    species: str | None = Field(default=None, description="Nome popular ou científico da espécie")
    volume_m3: float = Field(..., gt=0, description="Volume extraído ou transportado em metros cúbicos (m³)")


class InvoiceAuditInput(BaseModel):
    """Dados extraídos de uma Nota Fiscal (NF) de madeira para auditoria."""

    model_config = ConfigDict(extra="ignore")

    invoice_number: str = Field(..., description="Número da Nota Fiscal")
    issuer_cnpj: str = Field(..., description="CNPJ do emitente da NF")
    issue_date: date | None = Field(default=None, description="Data de emissão da NF")
    car_code: str | None = Field(
        default=None,
        description="Código do CAR declarado na NF. Se ausente, rastreabilidade é comprometida.",
    )
    volume_extracted_m3: float = Field(
        ...,
        gt=0,
        description="Volume total de madeira extraído/transportado na NF em m³",
    )
    items: list[InvoiceWoodItem] = Field(default_factory=list, description="Lista de itens de madeira na NF")


class CarAuditContext(BaseModel):
    """Dados do CAR/MapBiomas relevantes para o cruzamento com a NF."""

    model_config = ConfigDict(extra="ignore")

    car_code: str
    state: str | None = None
    area_ha: float | None = None
    alerts_count: int | None = None
    embargoes_count: int | None = None
    max_volume_allowed_m3: float | None = Field(
        default=None,
        description="Volume máximo de madeira permitido para manejo/supressão autorizada no imóvel",
    )
    is_active: bool = True
    mapbiomas_status: Literal["found", "not_in_mapbiomas", "unavailable"] = "found"


class AuditCrossCheckRequest(BaseModel):
    """Payload de entrada completo para auditoria cruzada."""

    model_config = ConfigDict(extra="ignore")

    invoice: InvoiceAuditInput
    car_context: CarAuditContext | None = None


class AIAuditResult(BaseModel):
    """Resultado da auditoria ESG e análise do Consultor de IA."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["apto", "nao_apto", "indisponivel"] = Field(
        ...,
        description="Status de conformidade da auditoria: apto, nao_apto ou indisponivel.",
    )
    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Score ESG calculado (0 a 100). Penalizado caso faltem dados essenciais.",
    )
    justification: str = Field(
        ...,
        description="Justificativa técnica em português (pt-BR) detalhando os achados.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="De 3 a 5 sugestões práticas de melhoria de transparência e processos para o produtor.",
    )
    audited_at: datetime = Field(..., description="Timestamp da auditoria")

