"""GET /api/dashboard/report — features 005 (formato) e 008 (IA explica os dados, com regras de reserva)."""

import json

import pytest

from app.config import settings
from tests.conftest import OTHER_CAR, REF_CAR, register

CNPJ = "04654691000106"
CNPJ_FMT = "04.654.691/0001-06"
REPORT = {
    "nivel": "gold",  # o backend deve ignorar e impor o nível calculado
    "titulo": "Desmatamento recente sem autorização registrada",
    "riscos": ["3 alertas de 2026 (74,5 ha) sem autorização registrada"],
    "contexto": ["1 foco de calor em out/2026"],
    "ressalvas": ["O PRODES não registra regeneração"],
    "imoveis": [{"car_code": "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0", "resumo": "3 alertas de 2026"}],
    "data_dos_dados": "2026-11-06",
    "gerado_em": "2026-11-06T15:00:00Z",
}
AI = {
    "titulo": "Imóvel A tem alertas em aberto em reserva legal",
    "riscos": ["Alertas sem autorização registrada no Imóvel A, parte em reserva legal e APP."],
    "contexto": ["Focos de calor e vegetação nativa aparecem só como contexto."],
    "ressalvas": ["O PRODES não registra regeneração."],
    "imoveis": [{"id": "Imóvel A", "resumo": "Alertas em aberto depois de 2020 em reserva legal."}],
}


@pytest.fixture
def reports_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "mock_reports_dir", str(tmp_path))
    return tmp_path


@pytest.fixture
def demo(reports_dir, monkeypatch):
    monkeypatch.setattr(settings, "report_demo_mode", True)
    return reports_dir


def report(client):
    r = client.get("/api/dashboard/report")
    assert r.status_code == 200, r.text
    return r.json()


def level(client):
    return client.get("/api/dashboard").json()["cnpj_status"]["level"]


# ---- Sem IA: texto por regras -------------------------------------------------------------------------
def test_without_llm_key_uses_rules_text(client, reports_dir):
    register(client)
    d = report(client)
    assert d["status"] == "ok" and d["origem"] == "regras"
    assert d["nivel"] == level(client) == "bronze"
    assert d["imoveis"][0]["car_code"] == REF_CAR and d["imoveis"][0]["nivel"] == "bronze" and d["titulo"]
    text = json.dumps(d, ensure_ascii=False)
    assert "Gerado por IA" not in text and "Recomenda-se" not in text and "nota ESG" not in text


def test_no_properties_is_unavailable(client):
    register(client, cars=())
    assert report(client)["status"] == "indisponivel"


def test_requires_session(client):
    client.cookies.clear()
    assert client.get("/api/dashboard/report").status_code == 401


# ---- Exemplo escrito à mão: só em modo demonstração ---------------------------------------------------
def test_example_ignored_without_demo_mode(client, reports_dir):
    (reports_dir / f"{CNPJ}.json").write_text(json.dumps(REPORT), encoding="utf-8")
    register(client)
    assert report(client)["origem"] == "regras"


def test_example_report_with_computed_level(client, demo):
    (demo / f"{CNPJ}.json").write_text(json.dumps(REPORT), encoding="utf-8")
    register(client)
    d = report(client)
    assert d["status"] == "ok" and d["origem"] == "exemplo"
    assert d["nivel"] == level(client) == "bronze"  # regra 006: RL/APP pós-2020
    assert d["titulo"] == REPORT["titulo"] and d["imoveis"][0]["resumo"] == "3 alertas de 2026"
    assert d["imoveis"][0]["nivel"] == "bronze"


@pytest.mark.parametrize("bad", [
    {"riscos": ["Desmatamento ilegal na reserva"]},
    {"titulo": "Possível crime ambiental"},
    {"riscos": ["a", "b", "c", "d"]},
    {"campo_desconhecido": 1},
])
def test_invalid_example_is_rejected(client, demo, bad):
    (demo / f"{CNPJ}.json").write_text(json.dumps({**REPORT, **bad}), encoding="utf-8")
    register(client)
    assert report(client)["status"] == "indisponivel"


# ---- IA (feature 008) ---------------------------------------------------------------------------------
def test_ai_report_with_real_codes_and_rules_level(client, llm):
    llm.response = AI
    register(client)
    d = report(client)
    assert d["origem"] == "agente" and d["nivel"] == level(client) == "bronze"
    assert d["imoveis"] == [{"car_code": REF_CAR, "resumo": "Alertas em aberto depois de 2020 em reserva legal.",
                             "nivel": "bronze"}]  # nível do imóvel pelas regras, não pela IA
    assert d["titulo"].startswith("PE-2607505 tem alertas")  # pseudônimo trocado pelo prefixo do CAR
    assert "Imóvel A" not in json.dumps(d, ensure_ascii=False)


def test_ai_receives_facts_without_car_codes_or_cnpj(client, llm):
    llm.response = AI
    register(client)
    report(client)
    sent = json.dumps(llm.bodies[0], ensure_ascii=False)
    for secret in (REF_CAR, REF_CAR.split("-")[2], CNPJ, CNPJ_FMT, "prod@test.com"):
        assert secret not in sent
    facts = json.loads(llm.bodies[0]["messages"][1]["content"])
    car = facts["imoveis"][0]
    assert car["id"] == "Imóvel A" and car["nivel"] == "bronze"
    assert car["motivos"][0]["codigo"] == "RL_APP_POS2020"
    assert facts["cnpj"]["nivel"] == "bronze" and facts["cnpj"]["total_imoveis"] == 1
    assert "geometry" not in sent and "alert_code" not in sent


@pytest.mark.parametrize("case", ["status", "timeout"])
def test_ai_failure_falls_back_to_rules(client, llm, case):
    if case == "status":
        llm.status = 500
    else:
        llm.timeout = True
    register(client)
    d = report(client)
    assert d["origem"] == "regras" and llm.calls == 1  # erro de rede/servidor: sem retry


@pytest.mark.parametrize("bad", [
    {"riscos": ["999,9 ha em reserva legal no Imóvel A."]},  # número inventado
    {"titulo": "Imóvel Z tem embargos"},  # imóvel inexistente
    {"titulo": "Desmatamento ilegal no Imóvel A"},  # vocabulário proibido
    {"titulo": ""},  # sem título
])
def test_invalid_ai_text_retries_once_then_rules(client, llm, bad):
    llm.response = {**AI, **bad}
    register(client)
    d = report(client)
    assert d["origem"] == "regras" and llm.calls == 2


def test_retry_can_recover(client, llm):
    llm.response = [{**AI, "titulo": "Imóvel Z"}, AI]
    register(client)
    assert report(client)["origem"] == "agente" and llm.calls == 2


def test_extra_risks_are_trimmed(client, llm):
    llm.response = {**AI, "riscos": ["a", "b", "c", "d"], "contexto": ["e", "f", "g", "h"]}
    register(client)
    d = report(client)
    assert d["origem"] == "agente" and d["riscos"] == ["a", "b", "c"] and len(d["contexto"]) == 3


def test_missing_property_gets_rules_sentence(client, llm):
    llm.response = AI  # só fala do Imóvel A
    register(client, cars=(REF_CAR, OTHER_CAR))
    d = report(client)
    assert d["origem"] == "agente"
    assert {p["car_code"] for p in d["imoveis"]} == {REF_CAR, OTHER_CAR}
    other = next(p for p in d["imoveis"] if p["resumo"] != AI["imoveis"][0]["resumo"])
    assert "alertas em aberto" in other["resumo"]


# ---- Cache ----------------------------------------------------------------------------------------------
def test_same_data_calls_ai_once(client, llm):
    llm.response = AI
    register(client)
    first, second = report(client), report(client)
    assert llm.calls == 1 and first == second


def test_changed_data_regenerates(client, llm, mapbiomas_mock):
    llm.response = AI
    register(client)
    report(client)
    mapbiomas_mock.properties[REF_CAR]["alerts"] = mapbiomas_mock.properties[REF_CAR]["alerts"][:1]
    client.get(f"/api/cars/{REF_CAR}/detail?refresh=true")
    client.get(f"/api/cars/{REF_CAR}/indicators?refresh=true")
    report(client)
    assert llm.calls == 2


def test_rules_text_is_cached_too(client):
    register(client)
    first, second = report(client), report(client)
    assert first["origem"] == "regras" and first["gerado_em"] == second["gerado_em"]
