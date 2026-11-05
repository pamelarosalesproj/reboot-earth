from tests.conftest import OTHER_CAR, REF_CAR, register

URL = f"/api/cars/{REF_CAR}/detail"


def test_detail_reference_car(client):
    register(client)
    r = client.get(URL)
    assert r.status_code == 200, r.text
    d = r.json()
    codes = {a["alert_code"] for a in d["alerts"]}
    assert codes == {1571779, 1581449, 1580505}
    dates = [a["detected_at"] for a in d["alerts"]]
    assert dates == sorted(dates, reverse=True)
    assert all(a["embargoes_count"] == 0 for a in d["alerts"])
    assert d["embargoes"] == []
    first = next(a for a in d["alerts"] if a["alert_code"] == 1571779)
    assert round(first["area_in_car_ha"], 3) == 31.146
    assert d["summary"]["alerts_count"] == 3


def test_alert_embargo_ids_dedup(client, mapbiomas_mock):
    mapbiomas_mock.properties[REF_CAR]["alerts"][0]["crossedEmbargoesIds"] = [10, 10, 11]
    register(client)
    alerts = client.get(URL).json()["alerts"]
    assert sorted(a["embargoes_count"] for a in alerts) == [0, 0, 2]


def test_detail_other_producer_404(client):
    register(client, email="a@test.com", cars=(REF_CAR,))
    client.cookies.clear()
    register(client, email="b@test.com", cars=(OTHER_CAR,))
    assert client.get(URL).status_code == 404
