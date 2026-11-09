"""Áreas embargadas do IBAMA (feature 007): mapeamento, limiar de 0,1 ha, deduplicação e falhas."""

import asyncio

import httpx
import pytest
import respx
from shapely.geometry import box, mapping

from app.config import settings
from app.sources import SourceUnavailable
from app.sources.ibama import IBAMA_MIN_OVERLAP_HA, embargoes_from_features, fetch_embargoes

# CAR de ~1 km × 1 km perto do equador (≈ 123 ha); 0,001° ≈ 111 m.
CAR = box(-60.0, -5.0, -59.99, -4.99)
CAR_GEOJSON = mapping(CAR)
DAY_MS = 1341964800000  # 2012-07-11


def feature(geom, **props) -> dict:
    base = {"num_tad": "625137", "serie_tad": "C", "num_processo": "02048000439201263",
            "dat_embargo": DAY_MS, "qtd_area_embargada": 240.17, "des_tad": "Fica embargada a área."}
    return {"type": "Feature", "geometry": mapping(geom), "properties": {**base, **props}}


def inside(side_deg: float):
    """Quadrado de lado `side_deg` dentro do CAR."""
    return box(-59.995, -4.995, -59.995 + side_deg, -4.995 + side_deg)


def test_maps_feature_to_embargo():
    [e] = embargoes_from_features([feature(inside(0.001))], CAR)  # ~1,2 ha
    assert e.source == "IBAMA" and e.process_code == "02048000439201263"
    assert e.term == "625137/C" and e.area_ha == 240.17
    assert e.registered_at.isoformat() == "2012-07-11" and e.expired_at is None
    assert e.descriptions == ["Fica embargada a área."]
    assert 1.1 < e.overlap_ha < 1.3


def test_overlap_threshold():
    tiny = inside(0.0002)  # ~0,05 ha
    assert embargoes_from_features([feature(tiny)], CAR) == []
    assert IBAMA_MIN_OVERLAP_HA == 0.1
    # Polígono que só toca a borda: sobreposição 0.
    neighbour = box(-59.99, -5.0, -59.98, -4.99)
    assert embargoes_from_features([feature(neighbour)], CAR) == []


def test_partial_overlap_counts_only_area_inside():
    half_out = box(-60.001, -4.995, -59.999, -4.994)  # metade fora do CAR
    [e] = embargoes_from_features([feature(half_out)], CAR)
    assert 1.1 < e.overlap_ha < 1.3


def test_same_process_counts_once_and_sums_overlap():
    a = feature(box(-59.995, -4.995, -59.994, -4.994), num_tad="1")
    b = feature(box(-59.993, -4.993, -59.992, -4.992), num_tad="2")
    [e] = embargoes_from_features([a, b], CAR)
    assert 2.3 < e.overlap_ha < 2.6


def test_without_process_groups_by_term():
    a = feature(inside(0.001), num_processo=None)
    b = feature(inside(0.001), num_processo="", num_tad="999")
    es = embargoes_from_features([a, b], CAR)
    assert sorted(e.term for e in es) == ["625137/C", "999/C"]


def test_invalid_geometry_counts_conservatively():
    f = feature(inside(0.001))
    f["geometry"] = {"type": "Polygon", "coordinates": [[[0, 0]]]}
    [e] = embargoes_from_features([f], CAR)
    assert e.overlap_ha is None


def run(features=None, status=200, body=None):
    with respx.mock() as router:
        route = router.post(settings.ibama_embargoes_url).mock(return_value=httpx.Response(
            status, json=body if body is not None else {"type": "FeatureCollection", "features": features or []}))
        try:
            return asyncio.run(fetch_embargoes(CAR_GEOJSON)), route
        finally:
            run.last_form = dict(httpx.QueryParams(route.calls.last.request.content.decode())) if route.calls else None


def test_fetch_never_asks_personal_fields():
    result, _ = run([feature(inside(0.001))])
    assert len(result) == 1
    fields = run.last_form["outFields"]
    assert "cpf" not in fields and "nome" not in fields
    assert run.last_form["spatialRel"] == "esriSpatialRelIntersects" and run.last_form["inSR"] == "4326"


@pytest.mark.parametrize("status,body", [
    (500, {"x": 1}),
    (200, {"error": {"code": 400, "message": "Invalid query"}}),
    (200, {"type": "FeatureCollection", "features": [], "properties": {"exceededTransferLimit": True}}),
    (200, {"features": [], "exceededTransferLimit": True}),
])
def test_fetch_failures_are_unavailable(status, body):
    with pytest.raises(SourceUnavailable):
        run(status=status, body=body)


def test_fetch_invalid_json_is_unavailable():
    with respx.mock() as router:
        router.post(settings.ibama_embargoes_url).mock(return_value=httpx.Response(200, text="<html>"))
        with pytest.raises(SourceUnavailable):
            asyncio.run(fetch_embargoes(CAR_GEOJSON))


def test_fetch_timeout_is_unavailable():
    with respx.mock() as router:
        router.post(settings.ibama_embargoes_url).mock(side_effect=httpx.ReadTimeout("slow"))
        with pytest.raises(SourceUnavailable):
            asyncio.run(fetch_embargoes(CAR_GEOJSON))
