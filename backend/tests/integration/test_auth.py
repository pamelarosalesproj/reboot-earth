from tests.conftest import VALID_CNPJ, register


def payload(**kw):
    return {"email": "prod@test.com", "password": "segredo123", "cnpj": VALID_CNPJ, **kw}


def test_register_without_cars_sets_cookie_and_me(client, mapbiomas_mock):
    r = client.post("/api/auth/register", json=payload())
    assert r.status_code == 201, r.text
    assert "session" in r.cookies
    body = r.json()
    assert body["cnpj"] == "04654691000106" and body["cars"] == []
    assert client.get("/api/auth/me").json()["email"] == "prod@test.com"
    assert client.get("/api/cars").json() == []
    assert mapbiomas_mock.calls == []  # el registro no depende de MapBiomas


def test_register_works_with_mapbiomas_down(client, mapbiomas_mock):
    mapbiomas_mock.down = True
    assert client.post("/api/auth/register", json=payload()).status_code == 201


def test_register_never_exposes_secrets(client):
    text = client.post("/api/auth/register", json=payload()).text.lower()
    assert "password" not in text and "hash" not in text


def test_duplicate_email_409(client):
    client.post("/api/auth/register", json=payload())
    client.cookies.clear()
    assert client.post("/api/auth/register", json=payload(email="PROD@test.com")).status_code == 409


def test_invalid_cnpj_422(client):
    r = client.post("/api/auth/register", json=payload(cnpj="04.654.691/0001-07"))
    assert r.status_code == 422 and r.json()["field"] == "cnpj"


def test_invalid_email_and_short_password_422(client):
    assert client.post("/api/auth/register", json=payload(email="no-es-email")).json()["field"] == "email"
    assert client.post("/api/auth/register", json=payload(password="corta")).json()["field"] == "password"


def test_login_logout(client):
    register(client, cars=())
    client.cookies.clear()
    bad = client.post("/api/auth/login", json={"email": "prod@test.com", "password": "errada123"})
    assert bad.status_code == 401
    nouser = client.post("/api/auth/login", json={"email": "x@test.com", "password": "errada123"})
    assert nouser.json()["detail"] == bad.json()["detail"]  # mensaje genérico
    ok = client.post("/api/auth/login", json={"email": "PROD@test.com", "password": "segredo123"})
    assert ok.status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401
