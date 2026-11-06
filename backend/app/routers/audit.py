"""Rotas de auditoria e validação ESG para análise de Notas Fiscais x CARs."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import current_producer
from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.models import Producer, ProducerCar, SinaflorCar
from app.schemas_audit import (
    InvoiceWoodItem,
    MonthlyAuditReportRequest,
    MonthlyAuditReportResponse,
    MonthlyInvoiceInput,
)
from app.services.ai_auditor_service import audit_monthly_report
from app.services.car_service import get_summary

router = APIRouter(prefix="/audit", tags=["audit"])


def _generate_mock_monthly_invoices(cnpj: str, car_codes: list[str]) -> list[MonthlyInvoiceInput]:
    """Gera dados realistas de NFs ajustados aos 3 casos de uso específicos:

    1. 04654691000106 (Excelente): NFs bem distribuídas, volumes baixos, 100% de cobertura.
    2. 11222333000181 (Atenção / Bom mas pode melhorar): Volume ok, mas omite 2 dos 4 CARs.
    3. 33592510000154 (Crítico / Ruim): Estouro volumétrico violento e concentração massiva em 1 CAR ('CAR coringa').
    """
    if not car_codes:
        return []

    clean_cnpj = "".join(filter(str.isdigit, cnpj))

    # CASO 1: Produtor Excelente / OK
    if clean_cnpj == "04654691000106":
        return [
            MonthlyInvoiceInput(
                invoice_number="NF-OK-01",
                issue_date=date(2026, 10, 5),
                car_code=car_codes[0],
                volume_extracted_m3=12.0,
                items=[InvoiceWoodItem(species="Manejo Sustentável", volume_m3=12.0)],
            ),
            MonthlyInvoiceInput(
                invoice_number="NF-OK-02",
                issue_date=date(2026, 10, 20),
                car_code=car_codes[1] if len(car_codes) > 1 else car_codes[0],
                volume_extracted_m3=10.5,
                items=[InvoiceWoodItem(species="Manejo Sustentável", volume_m3=10.5)],
            ),
        ]

    # CASO 2: Produtor Atenção (Bom, mas pode melhorar - 2 CARs omitidos)
    if clean_cnpj == "11222333000181":
        return [
            MonthlyInvoiceInput(
                invoice_number="NF-ATENCAO-01",
                issue_date=date(2026, 10, 8),
                car_code=car_codes[0],
                volume_extracted_m3=20.0,
                items=[InvoiceWoodItem(species="Eucalipto", volume_m3=20.0)],
            ),
            MonthlyInvoiceInput(
                invoice_number="NF-ATENCAO-02",
                issue_date=date(2026, 10, 15),
                car_code=car_codes[1] if len(car_codes) > 1 else car_codes[0],
                volume_extracted_m3=18.0,
                items=[InvoiceWoodItem(species="Pinus", volume_m3=18.0)],
            ),
        ]

    # CASO 3: Produtor Crítico / Ruim (Estouro de cota de 180 m³ + concentração em 1 CAR)
    primary_car = car_codes[0]
    return [
        MonthlyInvoiceInput(
            invoice_number="NF-CRITICA-01",
            issue_date=date(2026, 10, 3),
            car_code=primary_car,
            volume_extracted_m3=60.0,
            items=[InvoiceWoodItem(species="Ipê-Roxo", volume_m3=60.0)],
        ),
        MonthlyInvoiceInput(
            invoice_number="NF-CRITICA-02",
            issue_date=date(2026, 10, 12),
            car_code=primary_car,
            volume_extracted_m3=75.0,
            items=[InvoiceWoodItem(species="Jatobá", volume_m3=75.0)],
        ),
        MonthlyInvoiceInput(
            invoice_number="NF-CRITICA-03",
            issue_date=date(2026, 10, 22),
            car_code=primary_car,
            volume_extracted_m3=85.0,
            items=[InvoiceWoodItem(species="Cedro Rosa", volume_m3=85.0)],
        ),
    ]


@router.post("/generate-report", response_model=MonthlyAuditReportResponse)
async def generate_monthly_audit_report(
    req: MonthlyAuditReportRequest | None = None,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    """Gera o relatório mensal de auditoria ESG do produtor logado."""
    req = req or MonthlyAuditReportRequest()
    ref_period = req.reference_month or "2026-10"

    producer_cars = db.exec(
        select(ProducerCar).where(ProducerCar.producer_id == producer.id)
    ).all()
    car_codes = [c.car_code for c in producer_cars]

    registered_cars_info = []
    for code in car_codes:
        try:
            summary = await get_summary(db, client, code)
            area = summary.area_ha or 30.0
            max_vol = round(area * 1.5, 2)
            embargoes_count = summary.embargoes_count or 0
            alerts_count = summary.alerts_count or 0

            # Consulta dados oficiais do SINAFLOR e Indicadores Socioambientais se disponíveis
            sinaflor_db = db.get(SinaflorCar, code)
            if sinaflor_db and sinaflor_db.vigentes > 0 and sinaflor_db.volume_m3 > 0:
                max_vol = round(sinaflor_db.volume_m3, 2)

            registered_cars_info.append(
                {
                    "car_code": code,
                    "area_ha": area,
                    "max_volume_allowed_m3": max_vol,
                    "embargoes_count": embargoes_count,
                    "alerts_count": alerts_count,
                }
            )
        except Exception:  # noqa: BLE001
            # Fallback seguro para contingência
            sinaflor_db = db.get(SinaflorCar, code)
            max_vol = round(sinaflor_db.volume_m3, 2) if (sinaflor_db and sinaflor_db.vigentes > 0 and sinaflor_db.volume_m3 > 0) else 45.0
            registered_cars_info.append(
                {
                    "car_code": code,
                    "area_ha": 30.0,
                    "max_volume_allowed_m3": max_vol,
                    "embargoes_count": 0,
                    "alerts_count": 0,
                }
            )

    invoices = (
        req.invoices
        if req.invoices is not None
        else _generate_mock_monthly_invoices(producer.cnpj, car_codes)
    )

    return await audit_monthly_report(
        cnpj=producer.cnpj,
        reference_period=ref_period,
        registered_cars=registered_cars_info,
        invoices=invoices,
    )
