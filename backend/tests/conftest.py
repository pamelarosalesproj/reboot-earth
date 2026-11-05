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

FIXTURES = Path(__file__).parent / "fixtures"
REF_CAR = "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"
OTHER_CAR = "PE-2600500-99E6E359827B460BAF346B15E27F602D"
NO_ALERTS_CAR = "PE-2606507-AC1BA1E9D7A24326A1FF97C58D37E146"
VALID_CNPJ = "04.654.691/0001-06"
API_URL = "https://mapbiomas.test/api/v2/graphql"


def load_fixture() -> dict:
    return json.loads((FIXTURES / "pe_2607505_completo.json").read_text())


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

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        q, v = body["query"], body.get("variables") or {}
        op = next((n for n in ("SignIn", "CarExists", "RuralPropertyCar", "CarEmbargoesViaAlerts",
                               "CarEmbargoesViaPoint") if n in q), "?")
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
            if code not in self.properties:
                return httpx.Response(200, json={"data": {"alerts": {"collection": []}}})
            rp = {"carCode": code, "embargoedAreas": self.embargoes.get(code, [])}
            return httpx.Response(200, json={"data": {"alerts": {"collection": [{"ruralProperties": [rp]}]}}})
        if op == "CarEmbargoesViaPoint":
            return httpx.Response(200, json={"data": {"pointInformation": {"ruralProperties": []}}})
        return httpx.Response(400, json={"errors": [{"message": "unknown op"}]})

    def count(self, op: str) -> int:
        return self.calls.count(op)


@pytest.fixture
def mapbiomas_mock():
    fake = FakeMapBiomas()
    with respx.mock(assert_all_called=False) as router:
        router.post(API_URL).mock(side_effect=fake.handler)
        yield fake


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
