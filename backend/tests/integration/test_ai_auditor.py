"""Testes de unidade e integração do serviço de Auditoria e Consultoria ESG com IA."""

import json

import httpx
import pytest
import respx

from app.schemas_audit import (
    AIAuditResult,
    AuditCrossCheckRequest,
    CarAuditContext,
    InvoiceAuditInput,
    InvoiceWoodItem,
)
from app.services.ai_auditor_service import (
    audit_invoice_with_car,
)

LLM_TEST_URL = "https://mock-llm.rebootearth.local/v1/chat/completions"


@pytest.mark.asyncio
async def test_audit_apto_with_llm_mock():
    """Cenário Apto: NF possui CAR válido, volume dentro do limite e LLM responde com sucesso."""
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

    llm_mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "status": "apto",
                            "score": 95,
                            "justification": "Operação em perfeita conformidade. CAR regular sem alertas e volume compatível com o plano de manejo.",
                            "suggestions": [
                                "Manter o registro contínuo das coordenadas de extração para auditorias futuras.",
                                "Integrar o sistema emissor de NF diretamente com o sistema DOF/Sinaflor.",
                                "Realizar inventário florestal contínuo para renovação das cotas anuais.",
                            ],
                        }
                    )
                }
            }
        ]
    }

    with respx.mock(assert_all_called=False) as mock:
        mock.post(LLM_TEST_URL).mock(
            return_value=httpx.Response(200, json=llm_mock_response)
        )

        result: AIAuditResult = await audit_invoice_with_car(
            req, llm_api_url=LLM_TEST_URL
        )

        assert result.status == "apto"
        assert result.score == 95
        assert "conformidade" in result.justification
        assert len(result.suggestions) >= 3


@pytest.mark.asyncio
async def test_audit_nao_apto_omissao_car():
    """Cenário Não Apto 1: Omissão de CAR compromete rastreabilidade e reduz Score."""
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-999001",
            issuer_cnpj="04654691000106",
            car_code=None,  # CAR omitido!
            volume_extracted_m3=25.0,
        ),
        car_context=None,
    )

    llm_mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "status": "apto",  # LLM tentou marcar como apto erroneamente
                            "score": 90,
                            "justification": "Tentativa de aprovação.",
                            "suggestions": [
                                "Informar o CAR de origem.",
                                "Aprimorar rastreabilidade documental.",
                                "Capacitar a equipe em governança florestal.",
                            ],
                        }
                    )
                }
            }
        ]
    }

    with respx.mock(assert_all_called=False) as mock:
        mock.post(LLM_TEST_URL).mock(
            return_value=httpx.Response(200, json=llm_mock_response)
        )

        # Regra de negócio mandatória do sistema deve sobrepor a do LLM: status 'nao_apto' e score penalizado
        result: AIAuditResult = await audit_invoice_with_car(
            req, llm_api_url=LLM_TEST_URL
        )

        assert result.status == "nao_apto"
        assert result.score <= 50  # penalizado
        assert len(result.suggestions) >= 3


@pytest.mark.asyncio
async def test_audit_nao_apto_volume_excedente():
    """Cenário Não Apto 2: Volume na NF é superior ao limite permitido no CAR."""
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-888222",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=120.0,  # 120 m³ > 50 m³
        ),
        car_context=CarAuditContext(
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            state="PE",
            max_volume_allowed_m3=50.0,
        ),
    )

    with respx.mock(assert_all_called=False) as mock:
        # Simula erro de API (500) para verificar tolerância a falhas e motor determinístico
        mock.post(LLM_TEST_URL).mock(return_value=httpx.Response(500))

        result: AIAuditResult = await audit_invoice_with_car(
            req, llm_api_url=LLM_TEST_URL, allow_fallback=True
        )

        assert result.status == "nao_apto"
        assert result.score <= 50
        assert "ultrapassa" in result.justification or "excede" in result.justification
        assert 3 <= len(result.suggestions) <= 5


@pytest.mark.asyncio
async def test_audit_llm_failure_indisponivel_sem_fallback():
    """Tolerância a falhas: Se o LLM cair e fallback estiver desativado, retorna status 'indisponivel' sem quebrar."""
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-777333",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=10.0,
        ),
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.post(LLM_TEST_URL).mock(side_effect=httpx.ConnectTimeout("Timeout ao conectar ao LLM"))

        result: AIAuditResult = await audit_invoice_with_car(
            req, llm_api_url=LLM_TEST_URL, allow_fallback=False
        )

        assert result.status == "indisponivel"
        assert result.score is None
        assert "indisponível" in result.justification

