from datetime import timedelta

from sqlmodel import Session

from app.db import utcnow
from app.models import CarSnapshot
from tests.conftest import NO_ALERTS_CAR, OTHER_CAR, REF_CAR, register

URL = f"/api/cars/{REF_CAR}/summary"


def test_summary_reference_car(client):
    register(client)
    r = client.get(URL)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["alerts_count"] == 3
    assert s["embargoes_count"] == 0 and s["embargoes_status"] == "ok"
    assert s["state"] == "PE" and round(s["area_ha"], 2) == 264.23
    assert s["geometry"]["type"] == "MultiPolygon"
    assert s["stale"] is False


def test_list_cars(client):
    register(client, cars=(REF_CAR, OTHER_CAR))
    assert [c["car_code"] for c in client.get("/api/cars").json()] == [REF_CAR, OTHER_CAR]


def test_cache_and_refresh(client, mapbiomas_mock):
    register(client)
    client.get(URL)
    n = mapbiomas_mock.count("RuralPropertyCar")
    client.get(URL)
    assert mapbiomas_mock.count("RuralPropertyCar") == n  # desde caché
    client.get(URL, params={"refresh": "true"})
    assert mapbiomas_mock.count("RuralPropertyCar") == n + 1


def test_stale_cache_when_mapbiomas_down(client, mapbiomas_mock, engine):
    register(client)
    client.get(URL)
    with Session(engine) as db:
        snap = db.get(CarSnapshot, REF_CAR)
        snap.fetched_at = utcnow() - timedelta(hours=30)
        db.add(snap)
        db.commit()
    mapbiomas_mock.down = True
    r = client.get(URL)
    assert r.status_code == 200 and r.json()["stale"] is True and r.json()["alerts_count"] == 3


def test_503_without_cache(client, mapbiomas_mock):
    register(client)
    mapbiomas_mock.down = True
    assert client.get(URL).status_code == 503


def test_not_in_mapbiomas_summary(client):
    register(client, cars=(NO_ALERTS_CAR,))
    s = client.get(f"/api/cars/{NO_ALERTS_CAR}/summary").json()
    assert s["alerts_count"] == 0 and s["embargoes_count"] is None
    assert s["embargoes_status"] == "not_determinable" and s["geometry"] is None


def test_embargoes_counted_dedup(client, mapbiomas_mock):
    mapbiomas_mock.embargoes[REF_CAR] = [
        {"code": "1", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": "a"},
        {"code": "2", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": "b"},
        {"code": "3", "source": "SEMAS", "processCode": "P2", "areaHa": 1.0, "description": ""},
    ]
    register(client)
    assert client.get(URL).json()["embargoes_count"] == 2


def test_other_producer_car_404_and_no_session_401(client):
    register(client, email="a@test.com", cars=(REF_CAR,))
    client.cookies.clear()
    assert client.get(URL).status_code == 401
    register(client, email="b@test.com", cars=(OTHER_CAR,))
    assert client.get(URL).status_code == 404
