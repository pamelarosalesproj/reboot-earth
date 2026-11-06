"""Testes de integração para os endpoints e motor de auditoria mensal ESG."""

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas_audit import InvoiceWoodItem, MonthlyInvoiceInput


@pytest.mark.asyncio
async def test_generate_report_requires_auth():
    """Endpoint de auditoria mensal exige autenticação de produtor."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/audit/generate-report", json={})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_audit_monthly_report_unit_mock():
    """Valida o serviço audit_monthly_report com dados controlados."""
    from app.services.ai_auditor_service import audit_monthly_report

    registered_cars = [
        {"car_code": "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0", "area_ha": 100.0, "max_volume_allowed_m3": 80.0, "embargoes_count": 0, "alerts_count": 0},
        {"car_code": "MT-5102504-D274A7C9CD6C4B4C8FE5B14B88BA1BCE", "area_ha": 50.0, "max_volume_allowed_m3": 40.0, "embargoes_count": 0, "alerts_count": 0},
    ]

    invoices = [
        MonthlyInvoiceInput(
            invoice_number="NF-TEST-01",
            issue_date=date(2026, 10, 10),
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=20.0,
            items=[InvoiceWoodItem(species="Manejo Sustentável", volume_m3=20.0)],
        )
    ]

    report = await audit_monthly_report(
        cnpj="04654691000106",
        reference_period="2026-10",
        registered_cars=registered_cars,
        invoices=invoices,
        allow_fallback=True,
    )

    assert report.cnpj == "04654691000106"
    assert report.total_cars_registered == 2
    assert report.cars_evidenced_count == 1
    assert report.cars_omitted_count == 1
    assert "MT-5102504-D274A7C9CD6C4B4C8FE5B14B88BA1BCE" in report.omitted_car_codes
    assert report.total_volume_extracted_m3 == 20.0
    assert report.has_volume_exceeded is False
    assert len(report.suggestions) >= 3
