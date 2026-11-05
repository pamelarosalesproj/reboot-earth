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


# ---- Feature 002, US3: paridad panel ↔ ficha pública (constitución IV, SC-106) ----

def _public(client, cnpj="04654691000106"):
    cookies = dict(client.cookies)
    client.cookies.clear()
    d = client.get(f"/api/public/cnpj/{cnpj}").json()
    client.cookies.update(cookies)
    return d


def test_dashboard_status_matches_public(client):
    register(client)
    d = client.get("/api/dashboard").json()
    p = _public(client)
    assert d["cnpj_status"] == p["status"] and d["cnpj_score"] == p["score"]


def test_parity_after_removing_last_car(client):
    register(client)
    assert client.delete(f"/api/cars/{REF_CAR}").status_code == 204
    d = client.get("/api/dashboard").json()
    assert d["cnpj_status"]["level"] == "sem_dados" and d["cnpj_status"]["reason"] == "no_properties"
    assert d["cnpj_status"] == _public(client)["status"]


def test_status_is_cnpj_level_but_counts_are_account_level(client, mapbiomas_mock):
    emb = {"code": "1", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": ""}
    mapbiomas_mock.embargoes[OTHER_CAR] = [emb]
    register(client, email="b@test.com", cars=(OTHER_CAR,))
    client.cookies.clear()
    register(client, email="a@test.com", cars=(REF_CAR,))
    d = client.get("/api/dashboard").json()
    assert d["cars_count"] == 1 and d["embargoes_count"] == 0  # solo la cuenta
    assert d["cnpj_status"]["level"] == "bronze"  # el CNPJ entero (embargo en OTHER_CAR)
    assert d["cnpj_status"] == _public(client)["status"]
