"""GET /api/public/cnpj/{cnpj} — feature 002, US1 (FR-101…107)."""

from datetime import timedelta

from sqlmodel import Session

from app.config import settings
from app.db import utcnow
from app.models import CarSnapshot
from tests.conftest import OTHER_CAR, REF_CAR, VALID_CNPJ, register

CNPJ = "04654691000106"
NOT_REGISTERED = "11222333000181"
FORBIDDEN_KEYS = {"car_code", "geometry", "email", "id", "alerts", "embargoes"}


def public(client, cnpj=CNPJ):
    client.cookies.clear()  # siempre sin sesión
    return client.get(f"/api/public/cnpj/{cnpj}")


def all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from all_keys(v)


# ---- (T016) ficha, validación y agregación ----

def test_registered_cnpj_without_session(client):
    register(client)
    r = public(client)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["cnpj"] == CNPJ and d["cnpj_formatted"] == VALID_CNPJ
    assert d["registered"] is True and d["cars_count"] == 1 and d["cars_with_data"] == 1
    assert d["score"] == {"state": "em_calculo", "value": None, "computed_at": None, "method_version": None}
    assert d["status"]["basis"] == "regras" and d["data_as_of"] is not None


def test_not_registered_cnpj(client):
    d = public(client, NOT_REGISTERED).json()
    assert d["registered"] is False
    assert d["status"] == {"level": "sem_dados", "reason": "not_registered", "partial": False,
                           "basis": "regras", "reasons": [], "cars_by_level": None,
                           "eudr_attention": None, "alerts_count": None, "embargoes_count": None}
    assert d["score"]["state"] == "nao_calculavel"
    assert (d["cars_count"], d["data_as_of"]) == (0, None)


def test_invalid_cnpj_is_422(client):
    r = public(client, "11222333000100")
    assert r.status_code == 422
    assert r.json() == {"detail": "CNPJ inválido", "field": "cnpj", "invalid_values": []}


def test_masked_and_unmasked_are_identical(client):
    register(client)
    assert public(client, "04.654.691%2F0001-06").json() == public(client, CNPJ).json()


def test_registered_without_cars(client):
    register(client, cars=())
    d = public(client).json()
    assert (d["status"]["level"], d["status"]["reason"]) == ("sem_dados", "no_properties")
    assert d["score"]["state"] == "nao_calculavel"


def test_two_accounts_same_cnpj_dedupe_cars(client):
    register(client, email="a@test.com", cars=(REF_CAR,))
    client.cookies.clear()
    register(client, email="b@test.com", cars=(REF_CAR, OTHER_CAR))
    assert public(client).json()["cars_count"] == 2


# ---- (T017) privacidad: constitución III, SC-104 ----

def test_public_report_exposes_no_private_data(client):
    register(client, email="secreto@test.com", cars=(REF_CAR, OTHER_CAR))
    r = public(client)
    assert not FORBIDDEN_KEYS & set(all_keys(r.json()))
    assert REF_CAR not in r.text and OTHER_CAR not in r.text
    assert "secreto@test.com" not in r.text


# ---- (T018) fallos de MapBiomas: constitución II, SC-105 ----

def test_mapbiomas_down_with_expired_cache_serves_stale(client, engine, mapbiomas_mock):
    register(client)
    level = public(client).json()["status"]["level"]
    with Session(engine) as db:
        snap = db.get(CarSnapshot, REF_CAR)
        snap.fetched_at = utcnow() - timedelta(hours=settings.cache_ttl_hours + 1)
        db.add(snap)
        db.commit()
    mapbiomas_mock.down = True
    r = public(client)
    assert r.status_code == 200
    assert r.json()["stale"] is True and r.json()["status"]["level"] == level


def test_mapbiomas_down_without_cache_is_sem_dados(client, engine, mapbiomas_mock):
    register(client)
    with Session(engine) as db:  # garantizar que no hay caché previa
        if snap := db.get(CarSnapshot, REF_CAR):
            db.delete(snap)
            db.commit()
    mapbiomas_mock.down = True
    r = public(client)
    assert r.status_code == 200
    d = r.json()
    assert (d["status"]["level"], d["status"]["reason"]) == ("sem_dados", "data_unavailable")
    assert d["score"]["state"] == "nao_calculavel"


# ---- (T019) límite de búsquedas: FR-106 ----

def test_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setattr(settings, "public_search_limit_per_hour", 2)
    assert public(client, NOT_REGISTERED).status_code == 200
    assert public(client, NOT_REGISTERED).status_code == 200
    r = public(client, NOT_REGISTERED)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    body = r.json()
    assert body["retry_after_s"] == int(r.headers["Retry-After"]) and "Limite" in body["detail"]
