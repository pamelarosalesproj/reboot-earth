"""Schemas para auditoria fiscal e cadastral mensal do produtor (NF x CARs do CNPJ)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceWoodItem(BaseModel):
    """Item ou produto de madeira listado na Nota Fiscal."""

    model_config = ConfigDict(extra="ignore")

    species: str | None = Field(default=None, description="Nome da espécie de madeira (ex: Ipê, Jatobá, Eucalipto)")
    volume_m3: float = Field(..., gt=0, description="Volume em metros cúbicos (m³)")


class MonthlyInvoiceInput(BaseModel):
    """Nota Fiscal emitida no período analisado."""

    model_config = ConfigDict(extra="ignore")

    invoice_number: str = Field(..., description="Número da Nota Fiscal")
    issue_date: date | None = Field(default=None, description="Data de emissão da NF")
    car_code: str | None = Field(
        default=None,
        description="Código do CAR declarado na NF. Se ausente, rastreabilidade é comprometida.",
    )
    volume_extracted_m3: float = Field(
        ...,
        gt=0,
        description="Volume total de madeira faturado na NF em m³",
    )
    items: list[InvoiceWoodItem] = Field(default_factory=list, description="Lista de itens de madeira na NF")


class CarVolumeBalance(BaseModel):
    """Balanço de massa acumulado por CAR."""

    model_config = ConfigDict(extra="forbid")

    car_code: str
    invoices_count: int = Field(..., description="Quantidade de NFs que utilizaram este CAR")
    total_volume_invoices_m3: float = Field(..., description="Soma do volume faturado em todas as NFs do mês para este CAR")
    max_volume_allowed_m3: float = Field(..., description="Volume máximo suportado/autorizado para o imóvel")
    balance_m3: float = Field(..., description="Saldo restante (positivo) ou estouro de cota (negativo)")
    is_exceeded: bool = Field(..., description="True se a soma das NFs ultrapassou a capacidade suportada")
    has_embargoes: bool = Field(default=False, description="True se o CAR possui embargos ativos no MapBiomas")
    embargoes_count: int = 0
    alerts_count: int = 0
    concentration_percentage: float = Field(
        ...,
        description="Percentual do volume total do produtor concentrado neste único CAR",
    )


class MonthlyAuditReportRequest(BaseModel):
    """Requisição para gerar relatório de auditoria do mês anterior."""

    model_config = ConfigDict(extra="ignore")

    reference_month: str | None = Field(
        default=None,
        description="Mês de referência no formato 'AAAA-MM' (ex: '2026-10'). Se omitido, usa o mês anterior.",
    )
    # Lista opcional de NFs. Se omitido, o backend puxa o histórico cadastrado para o CNPJ.
    invoices: list[MonthlyInvoiceInput] | None = None


class MonthlyAuditReportResponse(BaseModel):
    """Relatório final emitido pelo Agente Consultor ESG."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["legal", "ilegal", "indisponivel"] = Field(
        ...,
        description="Classificação final: 'legal' (regular/apto) ou 'ilegal' (irregular/não apto).",
    )
    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Score de Transparência e Conformidade ESG (0 a 100).",
    )
    cnpj: str = Field(..., description="CNPJ do produtor auditado")
    reference_period: str = Field(..., description="Período auditado (ex: '2026-10')")

    # Métricas dos CARs do CNPJ
    total_cars_registered: int = Field(..., description="Total de CARs vinculados ao CNPJ no sistema")
    cars_evidenced_count: int = Field(..., description="Total de CARs que tiveram ao menos 1 NF no mês")
    cars_omitted_count: int = Field(..., description="Total de CARs do CNPJ que NÃO tiveram nenhuma NF associada")
    omitted_car_codes: list[str] = Field(default_factory=list, description="Códigos dos CARs sem evidência no mês")
    coverage_rate_percentage: float = Field(
        ...,
        description="Taxa de Cobertura Documental dos CARs (CARs evidenciados / CARs totais)",
    )

    # Métricas de Volume das NFs
    total_invoices_count: int = Field(..., description="Total de NFs analisadas no mês")
    invoices_missing_car_count: int = Field(..., description="Total de NFs emitidas sem indicar o CAR")
    total_volume_extracted_m3: float = Field(..., description="Volume total extraído somando todas as NFs do mês")

    # Balanço detalhado por CAR e anomalias
    car_balances: list[CarVolumeBalance] = Field(
        default_factory=list,
        description="Balanço consolidado por CAR evidenciado",
    )
    has_volume_exceeded: bool = Field(..., description="True se algum CAR teve sua cota mensal estourada")
    has_embargo_violation: bool = Field(..., description="True se houve faturamento em CAR embargado")
    has_concentration_anomaly: bool = Field(
        ...,
        description="True se mais de 80% do volume faturado se concentrou em um único CAR ('CAR coringa')",
    )

    # Análise da IA
    justification: str = Field(
        ...,
        description="Parecer técnico do Consultor ESG em português do Brasil (pt-BR).",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="De 3 a 5 sugestões práticas de melhoria de governança, processo e transparência.",
    )
    generated_at: datetime = Field(..., description="Data/hora de geração do relatório")
