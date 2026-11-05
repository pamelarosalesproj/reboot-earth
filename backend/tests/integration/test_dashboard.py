import copy

from tests.conftest import NO_ALERTS_CAR, OTHER_CAR, REF_CAR, register


def test_dashboard_empty(client):
    register(client, cars=())
    d = client.get("/api/dashboard").json()
    assert d["cars_count"] == 0 and d["alerts_count"] == 0 and d["embargoes_count"] == 0


def test_dashboard_reference_car(client):
    register(client)
    d = client.get("/api/dashboard").json()
    assert (d["cars_count"], d["alerts_count"], d["embargoes_count"]) == (1, 3, 0)
    assert d["cars_unavailable"] == 0 and d["stale"] is False


def test_alerts_and_embargoes_unique_across_cars(client, mapbiomas_mock):
    # OTHER_CAR comparte las mismas 3 alertas (mismos códigos) → siguen siendo 3.
    emb = {"code": "1", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": ""}
    mapbiomas_mock.embargoes[REF_CAR] = [emb]
    mapbiomas_mock.embargoes[OTHER_CAR] = [copy.deepcopy(emb), {**emb, "code": "2", "processCode": "P2"}]
    register(client, cars=(REF_CAR, OTHER_CAR))
    d = client.get("/api/dashboard").json()
    assert (d["cars_count"], d["alerts_count"], d["embargoes_count"]) == (2, 3, 2)


def test_not_in_mapbiomas_car_counts_but_embargoes_unknown(client):
    register(client, cars=(REF_CAR, NO_ALERTS_CAR))
    d = client.get("/api/dashboard").json()
    assert d["cars_count"] == 2 and d["alerts_count"] == 3 and d["embargoes_count"] == 0
    assert d["cars_embargoes_unknown"] == 1


def test_mapbiomas_down_without_cache(client, mapbiomas_mock):
    register(client, cars=())
    client.post("/api/cars", json={"car_code": REF_CAR})
    mapbiomas_mock.down = True
    d = client.get("/api/dashboard").json()
    assert d["cars_count"] == 1 and d["alerts_count"] is None and d["cars_unavailable"] == 1


def test_dashboard_requires_session(client):
    assert client.get("/api/dashboard").status_code == 401
