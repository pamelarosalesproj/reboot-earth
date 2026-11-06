"""Rota de auditoria e validação ESG para cruzamento NF x CAR/MapBiomas."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.auth import current_producer
from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.models import Producer
from app.schemas_audit import AIAuditResult, AuditCrossCheckRequest, CarAuditContext, InvoiceAuditInput
from app.services.ai_auditor_service import audit_invoice_with_car
from app.services.car_service import get_detail
from app.validators import normalize_car, normalize_cnpj

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/cross-check", response_model=AIAuditResult)
async def audit_cross_check(
    req: AuditCrossCheckRequest,
    producer: Producer = Depends(current_producer),
):
    """Executa auditoria direta fornecendo a NF e o contexto do CAR explicitamente.

    Acesso restrito ao produtor autenticado.
    """
    return await audit_invoice_with_car(req)


@router.post("/invoice", response_model=AIAuditResult)
async def audit_invoice_and_fetch_car(
    invoice: InvoiceAuditInput,
    producer: Producer = Depends(current_producer),
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    """Audita uma NF de madeira buscando automaticamente os dados do CAR no MapBiomas se informado."""
    try:
        normalize_cnpj(invoice.issuer_cnpj)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"CNPJ do emitente inválido: {e}")

    car_context: CarAuditContext | None = None
    if invoice.car_code and invoice.car_code.strip():
        try:
            norm_code = normalize_car(invoice.car_code)
            # Busca dados do CAR no backend (com cache / MapBiomas)
            try:
                detail = await get_detail(db, client, norm_code)
                summary = detail.summary
                # Estimativa de cota autorizada baseada na área do CAR se não houver cota explícita
                # (exemplo conservador: ~15 m³/ha para áreas sob plano de manejo)
                estimated_max_volume = round(summary.area_ha * 15.0, 2) if summary.area_ha else 50.0

                car_context = CarAuditContext(
                    car_code=summary.car_code,
                    state=summary.state,
                    area_ha=summary.area_ha,
                    alerts_count=summary.alerts_count,
                    embargoes_count=summary.embargoes_count,
                    max_volume_allowed_m3=estimated_max_volume,
                    mapbiomas_status="found",
                )
            except (HTTPException, Exception):  # noqa: BLE001
                car_context = CarAuditContext(
                    car_code=norm_code,
                    mapbiomas_status="unavailable",
                )
        except ValueError:
            # CAR com formato inválido: mantém nulo para penalizar transparência
            car_context = None

    req = AuditCrossCheckRequest(invoice=invoice, car_context=car_context)
    return await audit_invoice_with_car(req)

