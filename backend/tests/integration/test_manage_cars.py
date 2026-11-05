from tests.conftest import NO_ALERTS_CAR, OTHER_CAR, REF_CAR, register


def test_first_car_after_register(client):
    register(client, cars=())
    r = client.post("/api/cars", json={"car_code": REF_CAR})
    assert r.status_code == 201 and r.json()["mapbiomas_status"] == "found"
    assert [c["car_code"] for c in client.get("/api/auth/me").json()["cars"]] == [REF_CAR]


def test_add_validations_and_remove(client):
    register(client)
    r = client.post("/api/cars", json={"car_code": OTHER_CAR})
    assert r.status_code == 201 and r.json()["car_code"] == OTHER_CAR
    assert client.post("/api/cars", json={"car_code": OTHER_CAR.lower()}).status_code == 409
    bad = client.post("/api/cars", json={"car_code": "PE-123"})
    assert bad.status_code == 422 and bad.json()["invalid_values"] == ["PE-123"]
    assert client.delete(f"/api/cars/{OTHER_CAR}").status_code == 204
    assert [c["car_code"] for c in client.get("/api/cars").json()] == [REF_CAR]


def test_car_not_in_mapbiomas_is_accepted(client):
    register(client, cars=())
    r = client.post("/api/cars", json={"car_code": NO_ALERTS_CAR})
    assert r.status_code == 201 and r.json()["mapbiomas_status"] == "not_in_mapbiomas"


def test_can_remove_last_car(client):
    register(client)
    assert client.delete(f"/api/cars/{REF_CAR}").status_code == 204
    assert client.get("/api/cars").json() == []


def test_add_mapbiomas_down_503(client, mapbiomas_mock):
    register(client, cars=())
    mapbiomas_mock.down = True
    assert client.post("/api/cars", json={"car_code": OTHER_CAR}).status_code == 503
    assert client.get("/api/cars").json() == []


def test_remove_other_producer_car_404(client):
    register(client, email="a@test.com", cars=(REF_CAR, OTHER_CAR))
    client.cookies.clear()
    register(client, email="b@test.com", cars=(REF_CAR,))
    assert client.delete(f"/api/cars/{OTHER_CAR}").status_code == 404
