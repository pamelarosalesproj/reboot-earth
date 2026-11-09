"""Dados do relatório para a IA e controles do texto (feature 008): funções puras."""

import json
from datetime import date

from app.reports.facts import (
    alias_for,
    allowed_numbers,
    build_report_facts,
    invented_numbers,
    restore_aliases,
    unknown_aliases,
)
from app.schemas import CarsByLevel, Reason, Status

TODAY = date(2026, 11, 8)
GOLD = Status(level="gold", reason=None, partial=False, basis="regras")
BRONZE = Status(level="bronze", reason=None, partial=False, basis="regras",
                reasons=[Reason(code="EMBARGO_VIGENTE", severity="bronze", n=2)])
NO_DATA = Status(level="sem_dados", reason="data_unavailable", partial=True, basis="regras")
CNPJ = Status(level="bronze", reason=None, partial=True, basis="regras",
              reasons=[Reason(code="EMBARGO_VIGENTE", severity="bronze", cars=1)],
              cars_by_level=CarsByLevel(gold=1, bronze=1, sem_dados=1))
CARS = [
    ("PE-2600500-AAA", None, None, GOLD),
    ("MT-5102504-BBB", None, None, BRONZE),
    ("AM-1303304-CCC", None, None, NO_DATA),
]


def test_aliases_follow_severity_and_hide_codes_and_cnpj():
    facts, aliases = build_report_facts(CARS, CNPJ, TODAY)
    assert aliases == {"Imóvel A": "MT-5102504-BBB", "Imóvel B": "PE-2600500-AAA", "Imóvel C": "AM-1303304-CCC"}
    sent = json.dumps(facts, ensure_ascii=False)
    for code, *_ in CARS:
        assert code not in sent and code.split("-")[1] not in sent
    assert [p["nivel"] for p in facts["imoveis"]] == ["bronze", "gold", "sem_dados"]
    assert facts["imoveis"][0]["motivos"] == [{"codigo": "EMBARGO_VIGENTE", "n": 2, "ha": None, "pct": None}]
    assert facts["cnpj"]["imoveis_por_nivel"] == {"gold": 1, "silver": 0, "bronze": 1, "sem_dados": 1}


def test_unknown_data_is_text_never_zero():
    facts, _ = build_report_facts(CARS, CNPJ, TODAY)
    car = facts["imoveis"][2]
    assert car["alertas"] == "indisponivel" and car["embargos"] == {"estado": "indisponivel"}
    assert facts["cnpj"]["imoveis_com_embargos_nao_verificados"] == 3


def test_alias_letters():
    assert [alias_for(i) for i in (0, 25, 26, 27)] == ["Imóvel A", "Imóvel Z", "Imóvel AA", "Imóvel AB"]


def test_allowed_numbers_include_data_rules_and_date():
    allowed = allowed_numbers({"a": {"ha": 376.1, "n": 36}, "d": "2026-11-08", "flag": True})
    assert {376.1, 376.0, 36.0, 2026.0, 11.0, 8.0, 2020.0, 31.0, 12.0, 24.0, 1.0, 0.1} <= allowed
    assert 1.0 in allowed  # regra de 1 %, não o True


def test_invented_numbers_reads_pt_br_formats():
    allowed = allowed_numbers({"area": 2968.4, "ha": 376.1, "n": 5})
    ok = ["2.968,4 ha", "376,1 ha", "376.1 ha", "5 alertas", "depois de 31/12/2020", "376 ha"]
    assert invented_numbers(ok, allowed) == []
    assert invented_numbers(["999,9 ha", "6 embargos"], allowed) == ["999,9", "6"]


def test_unknown_aliases():
    aliases = {"Imóvel A": "X", "Imóvel B": "Y"}
    assert unknown_aliases(["Imóvel A e Imóvel B", "o imóvel a seguir"], aliases) == set()
    assert unknown_aliases(["Imóvel Z tem embargos"], aliases) == {"Imóvel Z"}
    assert unknown_aliases(["Manejo nos imóveis A, B e D."], aliases) == {"imóveis A, B e D"}
    assert unknown_aliases(["imóveis A e B"], aliases) == {"imóveis A e B"}
    assert unknown_aliases(["Os imóveis e as alertas"], aliases) == set()


def test_restore_aliases_uses_prefix_or_full_code_when_prefix_repeats():
    aliases = {"Imóvel A": "MT-5102504-BBB", "Imóvel B": "PE-2600500-AAA", "Imóvel C": "PE-2600500-DDD"}
    text = restore_aliases("Imóvel A, Imóvel B e Imóvel C.", aliases)
    assert text == "MT-5102504, PE-2600500-AAA e PE-2600500-DDD."
