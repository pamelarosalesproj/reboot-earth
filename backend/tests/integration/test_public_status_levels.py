"""Nivel de punta a punta con MapBiomas simulado (feature 002, US2, FR-111a)."""

from sqlmodel import Session

from app.models import CarSnapshot
from tests.conftest import NO_ALERTS_CAR, OTHER_CAR, REF_CAR, register

CNPJ = "04654691000106"
EMBARGO = {"code": "1", "source": "IBAMA", "processCode": "P1", "areaHa": 5.0, "description": ""}


def status(client):
    client.cookies.clear()
    d = client.get(f"/api/public/cnpj/{CNPJ}").json()
    assert d["status"]["basis"] == "provisional"
    assert not (d["status"]["level"] == "gold" and d["status"]["partial"])
    return d["status"]


def test_gold_without_alerts_or_embargoes(client, mapbiomas_mock):
    mapbiomas_mock.properties[REF_CAR]["alerts"] = []
    register(client)
    assert status(client) == {"level": "gold", "reason": None, "partial": False, "basis": "provisional",
                              "alerts_count": 0, "embargoes_count": 0}


def test_silver_with_alerts(client):
    register(client)  # el fixture de referencia tiene 3 alertas y 0 embargos
    assert status(client)["level"] == "silver"


def test_bronze_with_embargo(client, mapbiomas_mock):
    mapbiomas_mock.embargoes[REF_CAR] = [EMBARGO]
    register(client)
    s = status(client)
    assert s["level"] == "bronze" and s["embargoes_count"] == 1  # el conteo explica el nivel


def test_sem_dados_when_mapbiomas_down_without_cache(client, engine, mapbiomas_mock):
    register(client)
    with Session(engine) as db:
        if snap := db.get(CarSnapshot, REF_CAR):
            db.delete(snap)
            db.commit()
    mapbiomas_mock.down = True
    assert status(client)["reason"] == "data_unavailable"


def test_partial_unavailable_car_blocks_gold(client, engine, mapbiomas_mock):
    for code in (REF_CAR, OTHER_CAR):
        mapbiomas_mock.properties[code]["alerts"] = []
    register(client, cars=(REF_CAR, OTHER_CAR))
    assert status(client)["level"] == "gold"  # ambos limpios y con datos
    with Session(engine) as db:  # OTHER_CAR pierde su caché y MapBiomas cae
        db.delete(db.get(CarSnapshot, OTHER_CAR))
        db.commit()
    mapbiomas_mock.down = True
    s = status(client)
    assert (s["level"], s["partial"]) == ("silver", True)


def test_not_in_mapbiomas_car_blocks_gold(client, mapbiomas_mock):
    """Confirmado por el usuario el 2026-11-05 (research R5)."""
    mapbiomas_mock.properties[REF_CAR]["alerts"] = []
    register(client, cars=(REF_CAR, NO_ALERTS_CAR))
    s = status(client)
    assert (s["level"], s["partial"]) == ("silver", True)
