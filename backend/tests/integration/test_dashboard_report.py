"""GET /api/dashboard/report — feature 005 (relatório de exemplo, formato para o agente)."""

import json

import pytest

from app.config import settings
from tests.conftest import register

CNPJ = "04654691000106"
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


@pytest.fixture
def reports_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "mock_reports_dir", str(tmp_path))
    return tmp_path


def report(client):
    r = client.get("/api/dashboard/report")
    assert r.status_code == 200, r.text
    return r.json()


def test_missing_report_is_unavailable(client, reports_dir):
    register(client)
    assert report(client)["status"] == "indisponivel"


def test_example_report_with_computed_level(client, reports_dir):
    (reports_dir / f"{CNPJ}.json").write_text(json.dumps(REPORT), encoding="utf-8")
    register(client)
    d = report(client)
    assert d["status"] == "ok" and d["origem"] == "exemplo"
    assert d["nivel"] == client.get("/api/dashboard").json()["cnpj_status"]["level"] == "silver"
    assert d["titulo"] == REPORT["titulo"] and d["imoveis"][0]["resumo"] == "3 alertas de 2026"


@pytest.mark.parametrize("bad", [
    {"riscos": ["Desmatamento ilegal na reserva"]},
    {"titulo": "Possível crime ambiental"},
    {"riscos": ["a", "b", "c", "d"]},
    {"campo_desconhecido": 1},
])
def test_invalid_report_is_rejected(client, reports_dir, bad):
    (reports_dir / f"{CNPJ}.json").write_text(json.dumps({**REPORT, **bad}), encoding="utf-8")
    register(client)
    assert report(client)["status"] == "indisponivel"


def test_requires_session(client):
    client.cookies.clear()
    assert client.get("/api/dashboard/report").status_code == 401
