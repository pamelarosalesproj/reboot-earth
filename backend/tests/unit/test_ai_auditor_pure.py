"""Testes puros de validação das regras de negócio do Consultor/Auditor ESG."""

from app.schemas_audit import (
    AuditCrossCheckRequest,
    CarAuditContext,
    InvoiceAuditInput,
)
from app.services.ai_auditor_service import (
    _build_deterministic_evaluation,
)


def test_pure_deterministic_rules_no_car():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-01",
            issuer_cnpj="04654691000106",
            car_code=None,
            volume_extracted_m3=10.0,
        ),
        car_context=None,
    )
    status, score, suggestions = _build_deterministic_evaluation(req)
    assert status == "nao_apto"
    assert score <= 60
    assert 3 <= len(suggestions) <= 5
    assert any("CAR" in s for s in suggestions)


def test_pure_deterministic_rules_volume_exceeded():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-02",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=100.0,
        ),
        car_context=CarAuditContext(
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            max_volume_allowed_m3=40.0,
        ),
    )
    status, score, suggestions = _build_deterministic_evaluation(req)
    assert status == "nao_apto"
    assert score <= 50
    assert 3 <= len(suggestions) <= 5


def test_pure_deterministic_rules_apto():
    req = AuditCrossCheckRequest(
        invoice=InvoiceAuditInput(
            invoice_number="NF-03",
            issuer_cnpj="04654691000106",
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            volume_extracted_m3=30.0,
        ),
        car_context=CarAuditContext(
            car_code="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            max_volume_allowed_m3=50.0,
            alerts_count=0,
            embargoes_count=0,
        ),
    )
    status, score, suggestions = _build_deterministic_evaluation(req)
    assert status == "apto"
    assert score == 100
    assert 3 <= len(suggestions) <= 5


if __name__ == "__main__":
    test_pure_deterministic_rules_no_car()
    test_pure_deterministic_rules_volume_exceeded()
    test_pure_deterministic_rules_apto()
    print("Todos os testes unitários do motor puro passaram com sucesso!")

