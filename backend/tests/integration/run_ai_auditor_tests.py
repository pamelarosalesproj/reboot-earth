"""Executor de testes assíncronos de integração usando httpx."""

import asyncio
import json

import httpx

from app.schemas_audit import (
    AuditCrossCheckRequest,
    CarAuditContext,
    InvoiceAuditInput,
    InvoiceWoodItem,
)
from app.services.ai_auditor_service import audit_invoice_with_car

LLM_TEST_URL = "https://mock-llm.rebootearth.local/v1/chat/completions"


async def test_integration_apto():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-001234",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=30.0,
            items=[
                InvoiceWoodItem(species="Ipê", volume_m3=20.0),
                InvoiceWoodItem(species="Jatobá", volume_m3=10.0),
            ],
        ),
        car_context=CarAuditContext(
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            state="PE",
            area_ha=100.0,
            alerts_count=0,
            embargoes_count=0,
            max_volume_allowed_m3=80.0,
        ),
    )

    # Simula resposta do LLM com mock transport
    def mock_handler(request: httpx.Request) -> httpx.Response:
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "apto",
                                "score": 95,
                                "justification": "Operação em conformidade técnica e ambiental comprovada.",
                                "suggestions": [
                                    "Manter registros das guias florestais.",
                                    "Adotar rastreamento por QR code.",
                                    "Realizar inventário periódico.",
                                ],
                            }
                        )
                    }
                }
            ]
        }
        return httpx.Response(200, json=body)

    # Injeta mock transport temporário substituindo o AsyncClient em ai_auditor_service
    import app.services.ai_auditor_service as svc
    original_call = svc.call_llm_api

    async def mocked_call(*args, **kwargs):
        return {
            "status": "apto",
            "score": 95,
            "justification": "Operação em conformidade técnica e ambiental comprovada.",
            "suggestions": [
                "Manter registros das guias florestais.",
                "Adotar rastreamento por QR code.",
                "Realizar inventário periódico.",
            ],
        }

    svc.call_llm_api = mocked_call
    try:
        res = await audit_invoice_with_car(req)
        assert res.status == "apto"
        assert res.score == 95
        assert len(res.suggestions) >= 3
        print("  [OK] test_integration_apto")
    finally:
        svc.call_llm_api = original_call


async def test_integration_omissao_car():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-999001",
            issuer_cnpj="04654691000106",
            car_code=None,  # Sem CAR
            volume_extracted_m3=25.0,
        ),
        car_context=None,
    )

    import app.services.ai_auditor_service as svc
    original_call = svc.call_llm_api

    async def mocked_call(*args, **kwargs):
        # LLM tenta dar 90 e apto, mas as regras estritas da plataforma corrigem
        return {
            "status": "apto",
            "score": 90,
            "justification": "Tentativa de aprovação.",
            "suggestions": [
                "Cadastrar o CAR na NF.",
                "Realizar auditoria de custódia.",
                "Treinar operadores em conformidade.",
            ],
        }

    svc.call_llm_api = mocked_call
    try:
        res = await audit_invoice_with_car(req)
        assert res.status == "nao_apto"
        assert res.score <= 50
        assert len(res.suggestions) >= 3
        print("  [OK] test_integration_omissao_car")
    finally:
        svc.call_llm_api = original_call


async def test_integration_timeout_failure():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-TIMEOUT",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=10.0,
        ),
    )

    import app.services.ai_auditor_service as svc
    original_call = svc.call_llm_api

    async def mocked_call(*args, **kwargs):
        return None  # Simula timeout / indisponibilidade

    svc.call_llm_api = mocked_call
    try:
        res = await audit_invoice_with_car(req, allow_fallback=False)
        assert res.status == "indisponivel"
        assert res.score is None
        assert "indisponível" in res.justification
        print("  [OK] test_integration_timeout_failure")
    finally:
        svc.call_llm_api = original_call


async def run_all():
    print("Iniciando testes integrados assíncronos...")
    await test_integration_apto()
    await test_integration_omissao_car()
    await test_integration_timeout_failure()
    print("Todos os testes integrados assíncronos passaram com 100% de sucesso!")


if __name__ == "__main__":
    asyncio.run(run_all())

