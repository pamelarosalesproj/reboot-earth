"""Testes unitários do motor de auditoria mensal consolidada."""

from datetime import date

from app.schemas_audit import MonthlyInvoiceInput
from app.services.ai_auditor_service import (
    _build_deterministic_monthly_evaluation,
    calculate_monthly_balances,
)

SAMPLE_REGISTERED_CARS = [
    {"car_code": "CAR-01", "area_ha": 100.0, "max_volume_allowed_m3": 50.0, "embargoes_count": 0},
    {"car_code": "CAR-02", "area_ha": 50.0, "max_volume_allowed_m3": 30.0, "embargoes_count": 0},
    {"car_code": "CAR-03", "area_ha": 40.0, "max_volume_allowed_m3": 25.0, "embargoes_count": 0},
    {"car_code": "CAR-04", "area_ha": 60.0, "max_volume_allowed_m3": 40.0, "embargoes_count": 0},
    {"car_code": "CAR-05", "area_ha": 80.0, "max_volume_allowed_m3": 50.0, "embargoes_count": 0},
    {"car_code": "CAR-06", "area_ha": 70.0, "max_volume_allowed_m3": 40.0, "embargoes_count": 0},
    {"car_code": "CAR-07", "area_ha": 90.0, "max_volume_allowed_m3": 55.0, "embargoes_count": 0},
    {"car_code": "CAR-08", "area_ha": 50.0, "max_volume_allowed_m3": 30.0, "embargoes_count": 0},
]


def test_omitted_cars_detection_and_volume_exceeded():
    # 8 CARs cadastrados, mas NFs só usam 2 CARs (6 omitidos) e CAR-01 estoura a cota (60 m³ > 50 m³)
    invoices = [
        MonthlyInvoiceInput(invoice_number="NF-1", issue_date=date(2026, 10, 1), car_code="CAR-01", volume_extracted_m3=30.0),
        MonthlyInvoiceInput(invoice_number="NF-2", issue_date=date(2026, 10, 5), car_code="CAR-01", volume_extracted_m3=30.0),
        MonthlyInvoiceInput(invoice_number="NF-3", issue_date=date(2026, 10, 10), car_code="CAR-02", volume_extracted_m3=10.0),
    ]

    balances, omitted_codes, total_vol, missing_car_nfs, evidenced_count = calculate_monthly_balances(
        SAMPLE_REGISTERED_CARS, invoices
    )

    assert total_vol == 70.0
    assert evidenced_count == 2
    assert len(omitted_codes) == 6
    assert missing_car_nfs == 0

    car_01_balance = next(b for b in balances if b.car_code == "CAR-01")
    assert car_01_balance.total_volume_invoices_m3 == 60.0
    assert car_01_balance.is_exceeded is True
    assert car_01_balance.balance_m3 == -10.0
    assert car_01_balance.concentration_percentage > 80.0  # ~85.7%

    status, score, suggestions = _build_deterministic_monthly_evaluation(
        total_cars=8,
        evidenced_cars=evidenced_count,
        omitted_cars=omitted_codes,
        balances=balances,
        missing_car_nfs=missing_car_nfs,
        has_concentration_anomaly=True,
    )

    assert status == "ilegal"
    assert score <= 50
    assert 3 <= len(suggestions) <= 5
    assert any("omitidos" in s.lower() or "cadastrados no cnpj" in s.lower() for s in suggestions)
    assert any("extrapolou" in s.lower() for s in suggestions)


def test_monthly_audit_legal_scenario():
    # NFs bem distribuídas sem estouro
    invoices = [
        MonthlyInvoiceInput(invoice_number="NF-A", issue_date=date(2026, 10, 1), car_code="CAR-01", volume_extracted_m3=20.0),
        MonthlyInvoiceInput(invoice_number="NF-B", issue_date=date(2026, 10, 2), car_code="CAR-02", volume_extracted_m3=15.0),
    ]

    balances, omitted_codes, _total_vol, _missing_car_nfs, _evidenced_count = calculate_monthly_balances(
        SAMPLE_REGISTERED_CARS[:2], invoices  # considerando apenas 2 CARs no CNPJ
    )

    assert len(omitted_codes) == 0
    assert not any(b.is_exceeded for b in balances)

    status, score, suggestions = _build_deterministic_monthly_evaluation(
        total_cars=2,
        evidenced_cars=2,
        omitted_cars=[],
        balances=balances,
        missing_car_nfs=0,
        has_concentration_anomaly=False,
    )

    assert status == "legal"
    assert score >= 90
    assert 3 <= len(suggestions) <= 5


if __name__ == "__main__":
    test_omitted_cars_detection_and_volume_exceeded()
    test_monthly_audit_legal_scenario()
    print("Testes de auditoria mensal passaram com sucesso!")
