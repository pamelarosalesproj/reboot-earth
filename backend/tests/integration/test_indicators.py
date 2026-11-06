"""GET /api/cars/{code}/indicators — feature 003."""

from datetime import timedelta

from sqlmodel import Session

from app.config import settings
from app.db import utcnow
from app.models import CarIndicatorsSnapshot
from tests.conftest import NO_ALERTS_CAR, REF_CAR, register

SITUACOES = {"suspensa_judicial", "embargo_vigente", "autorizada", "embargo_levantado", "com_fiscalizacao",
             "pendente"}


def ind(client, code=REF_CAR, refresh=False):
    r = client.get(f"/api/cars/{code}/indicators" + ("?refresh=true" if refresh else ""))
    assert r.status_code == 200, r.text
    return r.json()


# ---- US1: riscos abertos (T009) ----

def test_reference_car_all_pending(client):
    register(client)
    d = ind(client)
    assert set(d["alerts_by_status"]) == SITUACOES
    assert d["alerts_by_status"]["pendente"]["n"] == 3
    assert round(d["alerts_by_status"]["pendente"]["ha"], 2) == round(31.14631 + 15.96029 + 27.3525, 2)
    assert sum(c["n"] for c in d["alerts_by_status"].values()) == len(d["alerts"]) == 3
    assert d["sources"]["mapbiomas"]["status"] == "ok"
    assert {a["status"] for a in d["alerts"]} == {"pendente"}


def test_post_2020_only_counts_later_alerts(client, mapbiomas_mock):
    old = mapbiomas_mock.properties[REF_CAR]["alerts"][0]
    old["detectedAt"] = "2020-12-31"
    register(client)
    d = ind(client)
    assert d["open"]["post_2020"]["n"] == 2
    assert round(d["open"]["post_2020"]["ha"], 2) == round(15.96029 + 27.3525, 2)


def test_legal_reserve_and_app_count_only_open_alerts(client, mapbiomas_mock):
    # 1571779 (19.68 ha RL) pasa a autorizada → no cuenta; 1580505 (7.39 RL, APP) y 1581449 (APP) abiertas.
    mapbiomas_mock.alert_extra[1571779] = {"crossedDeforestationAuthorizationsArea": 31.0}
    register(client)
    d = ind(client)
    assert d["alerts_by_status"]["autorizada"]["n"] == 1
    assert round(d["open"]["legal_reserve_ha"], 2) == 7.39
    assert d["open"]["app_alerts"] == 2


def test_judicial_and_actions(client, mapbiomas_mock):
    mapbiomas_mock.judicial[REF_CAR] = [1581449]
    mapbiomas_mock.alert_extra[1580505] = {"actionsList": [{"type": "AUTO_DE_INFRACAO"}]}
    register(client)
    d = ind(client)
    by = {a["alert_code"]: a["status"] for a in d["alerts"]}
    assert by == {1581449: "suspensa_judicial", 1580505: "com_fiscalizacao", 1571779: "pendente"}


def test_judicial_query_failure_is_not_fatal(client, mapbiomas_mock):
    mapbiomas_mock.judicial_error = True
    register(client)
    assert ind(client)["alerts_by_status"]["pendente"]["n"] == 3


def test_car_without_alerts_is_zero_not_unavailable(client):
    register(client, cars=(NO_ALERTS_CAR,))
    d = ind(client, NO_ALERTS_CAR)
    assert d["sources"]["mapbiomas"]["status"] == "ok"
    assert d["open"]["post_2020"] == {"n": 0, "ha": 0.0} and d["open"]["app_alerts"] == 0


def test_other_producers_car_is_404(client):
    register(client, email="a@test.com", cars=(REF_CAR,))
    client.cookies.clear()
    register(client, email="b@test.com", cars=())
    assert client.get(f"/api/cars/{REF_CAR}/indicators").status_code == 404


def test_requires_session(client):
    client.cookies.clear()
    assert client.get(f"/api/cars/{REF_CAR}/indicators").status_code == 401


def test_mapbiomas_down_without_cache(client, mapbiomas_mock):
    register(client)
    mapbiomas_mock.down = True
    d = ind(client)
    assert d["sources"]["mapbiomas"]["status"] == "indisponivel"
    assert d["open"]["post_2020"] is None and d["open"]["legal_reserve_ha"] is None


def test_mapbiomas_down_with_expired_cache_is_stale(client, engine, mapbiomas_mock):
    register(client)
    first = ind(client)
    with Session(engine) as db:
        snap = db.get(CarIndicatorsSnapshot, REF_CAR)
        snap.fetched_at = utcnow() - timedelta(hours=settings.cache_ttl_hours + 1)
        db.add(snap)
        db.commit()
    mapbiomas_mock.down = True
    d = ind(client)
    assert d["sources"]["mapbiomas"]["stale"] is True and d["stale"] is True
    assert d["alerts_by_status"] == first["alerts_by_status"]


def test_cache_avoids_refetch(client, mapbiomas_mock):
    register(client)
    ind(client)
    n = mapbiomas_mock.count("AlertIndicators")
    ind(client)
    assert mapbiomas_mock.count("AlertIndicators") == n
    ind(client, refresh=True)
    assert mapbiomas_mock.count("AlertIndicators") == n + 1


# ---- US2: contexto (T020) ----

def test_outside_amazon_deter_and_sinaflor_not_applicable(client, inpe):
    inpe.layers["prodes-brasil-nb:biomas_brasil"] = [{"type": "Feature", "geometry": None,
                                                     "properties": {"bioma": "Caatinga"}}]
    register(client)  # REF_CAR es PE
    d = ind(client)
    assert d["sources"]["deter"]["status"] == "nao_se_aplica" and d["context"]["deter"] is None
    assert d["sources"]["sinaflor"]["status"] == "nao_se_aplica"
    assert d["sources"]["prodes"]["status"] == "ok"
    assert d["context"]["native_vegetation"]["remaining_pct"] == 100.0  # sin desmatamento en las capas
    assert d["sources"]["focos"]["status"] == "ok" and d["context"]["hotspots_12m"]["count"] == 0


def test_inpe_down_keeps_mapbiomas(client, inpe):
    inpe.down = True
    register(client)
    d = ind(client)
    for s in ("prodes", "deter", "focos"):
        assert d["sources"][s]["status"] == "indisponivel"
    assert d["sources"]["mapbiomas"]["status"] == "ok"
    assert d["alerts_by_status"]["pendente"]["n"] == 3


def test_sinaflor_unsynced_then_synced(client, engine, mapbiomas_mock, inpe):
    from pathlib import Path

    from app.sources.sinaflor import aggregate_csv, save

    code = "MT-5102504-FB5206A8AF224FDC8B7E1D19FCF26A8E"
    mapbiomas_mock.properties[code] = {**mapbiomas_mock.properties[REF_CAR], "propertyCode": code, "alerts": []}
    register(client, cars=(code,))
    assert ind(client, code)["sources"]["sinaflor"]["status"] == "indisponivel"
    sample = Path(__file__).parents[1] / "fixtures" / "sinaflor_poa_sample.csv"
    with Session(engine) as db, sample.open(encoding="utf-8-sig") as f:
        save(db, aggregate_csv(f))
    d = ind(client, code)  # sin refresh: la caché no debe ocultar la sincronización nueva
    assert d["sources"]["sinaflor"]["status"] == "ok"
    assert d["context"]["forest_management"] == {"authorizations": 2, "active": 1, "volume_m3": 1355.0,
                                                 "last_issued": "2024-04-05"}
