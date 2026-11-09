"""Embargos do IBAMA como respaldo quando o MapBiomas não os determina (feature 007)."""

from shapely.geometry import box, mapping

from app.sources.geo import car_polygon
from tests.conftest import REF_CAR, load_fixture, register
from tests.integration.test_public_status_levels import EMBARGO

CNPJ = "04654691000106"
PERSONAL = {"cpf_cnpj_embargado": "28251210968", "nome_embargado": "FULANO DE TAL"}


def no_alerts_car_with_broken_point(mapbiomas_mock, ibama, up=True):
    """CAR sem alertas (embargos só via pointInformation) e pointInformation com o 500 real."""
    mapbiomas_mock.properties[REF_CAR]["alerts"] = []
    mapbiomas_mock.point_down = True
    ibama.down = not up


def square_inside(side_deg: float) -> dict:
    """Quadrado de lado `side_deg` a partir de um ponto interior do CAR do fixture."""
    p = car_polygon(load_fixture()["geomRuralProperty"]).representative_point()
    return mapping(box(p.x, p.y, p.x + side_deg, p.y + side_deg))


def ibama_feature(side_deg=0.001, **props) -> dict:  # 0,001° ≈ 1,2 ha nesta latitude
    base = {"num_tad": "625137", "serie_tad": "C", "num_processo": "02048000439201263",
            "dat_embargo": 1341964800000, "qtd_area_embargada": 240.17, "des_tad": "Fica embargada a área."}
    return {"type": "Feature", "geometry": square_inside(side_deg), "properties": {**base, **props}}


def detail(client) -> dict:
    return client.get(f"/api/cars/{REF_CAR}/detail").json()


def test_no_ibama_embargo_makes_car_gold(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    register(client)
    s = detail(client)["summary"]
    assert (s["embargoes_status"], s["embargoes_source"], s["embargoes_count"]) == ("ok", "ibama", 0)
    assert s["embargoes_checked_at"] and s["embargoes_stale"] is False
    assert s["status"]["level"] == "gold" and s["status"]["reasons"] == []
    assert mapbiomas_mock.count("CarEmbargoesViaPoint") >= 1


def test_ibama_embargo_over_threshold_is_bronze(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    ibama.features = [ibama_feature(), ibama_feature(0.0002, num_processo="OUTRO")]  # o 2º < 0,1 ha
    register(client)
    d = detail(client)
    assert d["summary"]["embargoes_count"] == 1
    [e] = d["embargoes"]
    assert e["source"] == "IBAMA" and e["term"] == "625137/C" and e["expired_at"] is None
    assert e["overlap_ha"] >= 0.1
    st = d["summary"]["status"]
    assert st["level"] == "bronze" and st["reasons"][0]["code"] == "EMBARGO_VIGENTE" and st["reasons"][0]["n"] == 1


def test_ibama_down_keeps_partial_data(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama, up=False)
    register(client)
    s = detail(client)["summary"]
    assert s["embargoes_status"] == "unavailable" and s["embargoes_count"] is None
    assert s["embargoes_source"] is None and s["embargoes_checked_at"] is None
    assert s["status"]["level"] == "silver"
    assert [r["code"] for r in s["status"]["reasons"]] == ["DADOS_PARCIAIS"]


def test_mapbiomas_embargoes_skip_ibama(client, mapbiomas_mock, ibama):
    ibama.down = False
    mapbiomas_mock.embargoes[REF_CAR] = [EMBARGO]
    register(client)
    s = detail(client)["summary"]
    assert (s["embargoes_status"], s["embargoes_source"], s["embargoes_count"]) == ("ok", "mapbiomas", 1)
    assert ibama.calls == []


def test_refresh_with_both_sources_down_keeps_previous_as_stale(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    ibama.features = [ibama_feature()]
    register(client)
    first = detail(client)["summary"]
    assert first["embargoes_count"] == 1 and first["embargoes_stale"] is False
    ibama.down = True
    d = client.get(f"/api/cars/{REF_CAR}/detail?refresh=true").json()
    s = d["summary"]
    assert (s["embargoes_status"], s["embargoes_count"], s["embargoes_source"]) == ("ok", 1, "ibama")
    assert s["embargoes_stale"] is True and s["embargoes_checked_at"] == first["embargoes_checked_at"]
    assert len(d["embargoes"]) == 1 and s["status"]["level"] == "bronze"


def test_car_without_polygon_does_not_call_ibama(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    mapbiomas_mock.properties[REF_CAR]["geomRuralProperty"] = None
    register(client)
    s = detail(client)["summary"]
    assert s["embargoes_status"] == "not_determinable" and ibama.calls == []


def test_personal_data_never_leaves_the_backend(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    ibama.features = [ibama_feature(**PERSONAL)]
    register(client)
    private = client.get(f"/api/cars/{REF_CAR}/detail").text
    client.cookies.clear()
    public = client.get(f"/api/public/cnpj/{CNPJ}").text
    for text in (private, public):
        for key, value in PERSONAL.items():
            assert key not in text and value not in text
    for call in ibama.calls:
        assert "cpf" not in call["outFields"] and "nome" not in call["outFields"]


def test_public_level_matches_panel_with_ibama(client, mapbiomas_mock, ibama):
    no_alerts_car_with_broken_point(mapbiomas_mock, ibama)
    register(client)
    panel = client.get("/api/dashboard").json()["cnpj_status"]
    client.cookies.clear()
    public = client.get(f"/api/public/cnpj/{CNPJ}").json()
    assert public["status"]["level"] == panel["level"] == "gold"
    text = str(public)
    for field in ("embargoes'", "term", "overlap_ha", "process_code"):
        assert field not in text
