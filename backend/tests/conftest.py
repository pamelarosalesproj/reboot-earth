import copy
import json
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.db import get_session
from app.main import app
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.rate_limit import public_limiter

FIXTURES = Path(__file__).parent / "fixtures"
REF_CAR = "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"
OTHER_CAR = "PE-2600500-99E6E359827B460BAF346B15E27F602D"
NO_ALERTS_CAR = "PE-2606507-AC1BA1E9D7A24326A1FF97C58D37E146"
VALID_CNPJ = "04.654.691/0001-06"
API_URL = "https://mapbiomas.test/api/v2/graphql"


def load_fixture() -> dict:
    return json.loads((FIXTURES / "pe_2607505_completo.json").read_text(encoding="utf-8"))


class FakeMapBiomas:
    """Simula la API GraphQL de MapBiomas Alerta según el nombre de la operación."""

    def __init__(self):
        ref = load_fixture()
        other = copy.deepcopy(ref)
        other["propertyCode"] = OTHER_CAR
        for a in other["alerts"]:
            a["crossedRuralProperties"] = [{"code": OTHER_CAR, "alertAreaInCar": 1.0}]
        self.properties: dict[str, dict] = {REF_CAR: ref, OTHER_CAR: other}
        self.embargoes: dict[str, list[dict]] = {}
        self.down = False
        self.calls: list[str] = []
        # Feature 003: overrides por alerta (campos crossed*, actionsList) y alertas suspendidas.
        self.alert_extra: dict[int, dict] = {}
        self.judicial: dict[str, list[int]] = {}
        self.judicial_error = False
        # Feature 007: pointInformation responde 500 al pedir embargos (comportamiento real desde 2026-11-08).
        self.point_down = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        q, v = body["query"], body.get("variables") or {}
        op = next((n for n in ("SignIn", "CarExists", "RuralPropertyCar", "CarEmbargoesViaAlerts",
                               "CarEmbargoesViaPoint", "AlertIndicators", "SuspendedJudicialAlerts")
                   if n in q), "?")
        self.calls.append(op)
        if self.down and op != "SignIn":
            return httpx.Response(502, text="Bad Gateway")
        if op == "SignIn":
            return httpx.Response(200, json={"data": {"signIn": {"token": "tok"}}})
        if op == "CarExists":
            prop = self.properties.get(v["code"])
            return httpx.Response(200, json={"data": {"ruralProperty":
                                                      {"propertyCode": v["code"]} if prop else None}})
        if op == "RuralPropertyCar":
            return httpx.Response(200, json={"data": {"ruralProperty": self.properties.get(v["code"])}})
        if op == "CarEmbargoesViaAlerts":
            code = v["code"]
            if code not in self.properties or not self.properties[code].get("alerts"):
                return httpx.Response(200, json={"data": {"alerts": {"collection": []}}})
            rp = {"carCode": code, "embargoedAreas": self.embargoes.get(code, [])}
            return httpx.Response(200, json={"data": {"alerts": {"collection": [{"ruralProperties": [rp]}]}}})
        if op == "AlertIndicators":
            prop = self.properties.get(v["c"][0])
            alerts = [{**a, **self.alert_extra.get(a["alertCode"], {})} for a in (prop or {}).get("alerts", [])]
            return httpx.Response(200, json={"data": {"alerts": {"collection": alerts}}})
        if op == "SuspendedJudicialAlerts":
            if self.judicial_error:
                return httpx.Response(200, json={"errors": [{"message": "boom"}]})
            codes = self.judicial.get(v["c"], [])
            return httpx.Response(200, json={"data": {"findSuspendedJudicialAlert":
                                                      [{"alertCode": c} for c in codes]}})
        if op == "CarEmbargoesViaPoint":
            if self.point_down:
                return httpx.Response(500, text="")
            return httpx.Response(200, json={"data": {"pointInformation": {"ruralProperties": []}}})
        return httpx.Response(400, json={"errors": [{"message": "unknown op"}]})

    def count(self, op: str) -> int:
        return self.calls.count(op)


class FakeInpe:
    """WFS del INPE simulado: features por capa (GeoJSON), filtrados solo por nombre de capa."""

    def __init__(self):
        self.layers: dict[str, list[dict]] = {}
        self.down = False
        self.calls: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        layer = request.url.params.get("typeName", "")
        self.calls.append(layer)
        if self.down:
            return httpx.Response(500, text="Internal error")
        return httpx.Response(200, json={"type": "FeatureCollection", "features": self.layers.get(layer, [])})


class FakeIbama:
    """Áreas embargadas do IBAMA simuladas (feature 007). Caído por defecto: los tests existentes
    conservan su comportamiento; los de la 007 lo encienden con `down = False`."""

    def __init__(self):
        self.features: list[dict] = []
        self.down = True
        self.truncated = False
        self.calls: list[dict] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        form = dict(httpx.QueryParams(request.content.decode()))
        self.calls.append(form)
        if self.down:
            return httpx.Response(500, text="Internal error")
        body: dict = {"type": "FeatureCollection", "features": self.features}
        if self.truncated:
            body["properties"] = {"exceededTransferLimit": True}
        return httpx.Response(200, json=body)


@pytest.fixture
def mapbiomas_mock():
    fake = FakeMapBiomas()
    fake.inpe = FakeInpe()
    fake.ibama = FakeIbama()
    with respx.mock(assert_all_called=False) as router:
        fake.router = router
        router.post(API_URL).mock(side_effect=fake.handler)
        router.get(url__startswith="https://terrabrasilis.dpi.inpe.br/").mock(side_effect=fake.inpe.handler)
        router.post(url__startswith="https://pamgia.ibama.gov.br/").mock(side_effect=fake.ibama.handler)
        yield fake


@pytest.fixture
def inpe(mapbiomas_mock):
    return mapbiomas_mock.inpe


@pytest.fixture
def ibama(mapbiomas_mock):
    return mapbiomas_mock.ibama


class FakeLlm:
    """LLM compatível com a API da OpenAI, simulado (feature 008). `response` é o JSON que o modelo "escreve";
    pode ser uma lista para respostas diferentes em chamadas seguidas."""

    def __init__(self):
        self.response: dict | list | str = {}
        self.status = 200
        self.timeout = False
        self.bodies: list[dict] = []

    @property
    def calls(self) -> int:
        return len(self.bodies)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(json.loads(request.content))
        if self.timeout:
            raise httpx.ReadTimeout("slow", request=request)
        if self.status != 200:
            return httpx.Response(self.status, text="error")
        resp = self.response
        if isinstance(resp, list):
            resp = resp[min(len(self.bodies), len(resp)) - 1]
        content = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    """Nenhum teste usa a chave real do .env: sem fixture `llm`, o relatório usa o texto por regras."""
    from app.config import settings

    monkeypatch.setattr(settings, "llm_api_key", "")
    monkeypatch.delenv("LLM_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _clear_report_cache():
    from app.reports import clear_report_cache

    clear_report_cache()
    yield
    clear_report_cache()


@pytest.fixture
def llm(mapbiomas_mock, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    fake = FakeLlm()
    mapbiomas_mock.router.post(settings.llm_api_url).mock(side_effect=fake.handler)
    return fake


@pytest.fixture(autouse=True)
def _reset_public_limiter():
    public_limiter.reset()
    yield
    public_limiter.reset()


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def client(engine, mapbiomas_mock):
    def _session():
        with Session(engine) as s:
            yield s

    mb = MapBiomasClient(url=API_URL, email="svc@test", password="x", timeout=5)
    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_mapbiomas_client] = lambda: mb
    yield TestClient(app)
    app.dependency_overrides.clear()


def register(client: TestClient, email="prod@test.com", cars=(REF_CAR,), cnpj=VALID_CNPJ,
             password="segredo123"):
    """Crea la cuenta y, si va bien, añade los CARs desde el panel (POST /api/cars)."""
    r = client.post("/api/auth/register", json={"email": email, "password": password, "cnpj": cnpj})
    if r.status_code == 201:
        for code in cars:
            added = client.post("/api/cars", json={"car_code": code})
            assert added.status_code == 201, added.text
    return r
