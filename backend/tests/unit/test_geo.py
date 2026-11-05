import pytest

from app.mapbiomas.geo import interior_point, parse_ewkt, wkt_to_geojson
from tests.conftest import load_fixture


def test_parse_ewkt_fixture_multipolygon():
    srid, geom = parse_ewkt(load_fixture()["geomRuralProperty"])
    assert srid == "4674"
    assert geom["type"] == "MultiPolygon"
    ring = geom["coordinates"][0][0]
    lon, lat = ring[0]
    assert -38 < lon < -37 and -10 < lat < -9  # lon/lat en Pernambuco
    assert ring[0] == ring[-1]


def test_polygon_with_hole():
    g = wkt_to_geojson("POLYGON((0 0, 4 0, 4 4, 0 4, 0 0), (1 1, 2 1, 2 2, 1 1))")
    assert g["type"] == "Polygon" and len(g["coordinates"]) == 2


def test_unsupported_type():
    with pytest.raises(ValueError):
        wkt_to_geojson("POINT(1 2)")


def test_interior_point_inside_bbox():
    _, geom = parse_ewkt(load_fixture()["geomRuralProperty"])
    x, y = interior_point(geom)
    xs = [p[0] for p in geom["coordinates"][0][0]]
    ys = [p[1] for p in geom["coordinates"][0][0]]
    assert min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys)
