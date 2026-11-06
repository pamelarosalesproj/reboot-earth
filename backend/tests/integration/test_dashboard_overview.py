"""GET /api/dashboard/overview — feature 005 (números do CNPJ)."""

from sqlmodel import Session

from app.models import CarIndicatorsSnapshot, CarSnapshot
from tests.conftest import OTHER_CAR, REF_CAR, register

EMB = {"code": "1", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": ""}


def overview(client):
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 200, r.text
    return r.json()


def test_reference_car_open_alerts(client):
    register(client)
    d = overview(client)
    assert d["cars_count"] == 1 and d["alerts_total"] == 3
    assert d["open_alerts"]["n"] == 3
    assert round(d["open_alerts"]["ha"], 2) == round(31.14631 + 15.96029 + 27.3525, 2)
    assert d["superseded_alerts"] == {"n": 0, "ha": 0.0}
    assert d["embargoes_active"] == 0 and d["cars_without_alert_data"] == 0


def test_authorized_alert_is_superseded(client, mapbiomas_mock):
    mapbiomas_mock.alert_extra[1571779] = {"crossedDeforestationAuthorizationsArea": 31.0}
    register(client)
    d = overview(client)
    assert d["open_alerts"]["n"] == 2 and d["superseded_alerts"]["n"] == 1
    assert round(d["superseded_alerts"]["ha"], 2) == 31.15


def test_alert_shared_by_two_cars_counts_once_and_embargoes_dedupe(client, mapbiomas_mock):
    # OTHER_CAR comparte las 3 alertas (mismos códigos) con REF_CAR.
    lifted = {**EMB, "code": "9", "processCode": "P9", "sourceExpiredAt": "2024-01-01"}
    mapbiomas_mock.embargoes[REF_CAR] = [EMB]
    mapbiomas_mock.embargoes[OTHER_CAR] = [dict(EMB), lifted]
    register(client, cars=(REF_CAR, OTHER_CAR))
    d = overview(client)
    assert d["cars_count"] == 2 and d["alerts_total"] == 3
    assert d["embargoes_active"] == 1  # P1 único entre los dos CARs; P9 levantado no cuenta


def test_counts_whole_cnpj_across_accounts(client):
    register(client, email="a@test.com", cars=(REF_CAR,))
    client.cookies.clear()
    register(client, email="b@test.com", cars=(OTHER_CAR,))
    assert overview(client)["cars_count"] == 2


def test_mapbiomas_down_without_cache_is_null_not_zero(client, engine, mapbiomas_mock):
    register(client)
    with Session(engine) as db:
        for model in (CarSnapshot, CarIndicatorsSnapshot):
            if row := db.get(model, REF_CAR):
                db.delete(row)
        db.commit()
    mapbiomas_mock.down = True
    d = overview(client)
    assert d["alerts_total"] is None and d["open_alerts"] is None and d["superseded_alerts"] is None
    assert d["embargoes_active"] is None
    assert d["cars_without_alert_data"] == 1


def test_requires_session(client):
    client.cookies.clear()
    assert client.get("/api/dashboard/overview").status_code == 401
