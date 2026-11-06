"""INPE: unión de capas superpuestas, focos en polígono/ventana, clases DETER (sin red)."""

from datetime import date

import httpx
import pytest
import respx
from shapely.geometry import box, mapping

from app.sources import SourceUnavailable, inpe
from app.sources.geo import area_ha

CAR = box(-50.0, -10.0, -49.99, -9.99)  # ~1 km² en lat -10


def feat(geom, **props):
    return {"type": "Feature", "geometry": mapping(geom), "properties": props}


def serve(layers: dict[str, list[dict]]):
    def handler(request: httpx.Request):
        return httpx.Response(200, json={"features": layers.get(request.url.params["typeName"], [])})
    return handler


@pytest.fixture
def wfs():
    with respx.mock(assert_all_called=False) as router:
        yield router


async def test_overlapping_biome_layers_count_once(wfs):
    half = box(-50.0, -10.0, -49.995, -9.99)  # mitad del CAR, en dos capas de biomas distintos
    wfs.get(url__startswith="https://terrabrasilis").mock(side_effect=serve({
        "prodes-cerrado-nb:yearly_deforestation": [feat(half, year=2022)],
        "prodes-amazon-nb:yearly_deforestation_biome": [feat(half, year=2022)],
        "prodes-amazon-nb:accumulated_deforestation_2007_biome": [feat(box(-60, -20, -59, -19))],  # fuera
    }))
    async with httpx.AsyncClient() as http:
        r = await inpe.prodes_loss(http, CAR, {"Cerrado", "Amazônia"})
    assert r["remaining_pct"] == pytest.approx(50.0, abs=0.2)
    assert r["deforested_ha"] == pytest.approx(area_ha(half, -10), rel=0.01)
    assert list(r["by_year"]) == ["2022"]
    assert r["by_year"]["2022"] == pytest.approx(area_ha(half, -10), rel=0.01)


async def test_hotspots_inside_polygon_and_window(wfs):
    inside, outside = box(-49.996, -9.996, -49.9959, -9.9959).centroid, box(-49.9, -9.9, -49.89, -9.89).centroid
    wfs.get(url__startswith="https://terrabrasilis").mock(side_effect=serve({"bdqueimadas2:focos": [
        feat(inside, data_hora_gmt="2026-10-01T15:00:00Z", eh_satelite_referencia=True),
        feat(outside, data_hora_gmt="2026-10-02T15:00:00Z", eh_satelite_referencia=True),
        feat(inside, data_hora_gmt="2025-01-01T15:00:00Z", eh_satelite_referencia=True),  # > 12 meses
        feat(inside, data_hora_gmt="2026-10-03T15:00:00Z", eh_satelite_referencia=False),
    ]}))
    async with httpx.AsyncClient() as http:
        r = await inpe.hotspots_12m(http, CAR, date(2026, 11, 6))
    assert r == {"count": 1, "by_month": {"2026-10": 1}}


async def test_deter_classes_aggregated(wfs):
    a, b = box(-50.0, -10.0, -49.998, -9.998), box(-49.995, -9.995, -49.993, -9.993)
    wfs.get(url__startswith="https://terrabrasilis").mock(side_effect=serve({"deter-amz:deter_amz": [
        feat(a, classname="CS_GEOMETRICO", view_date="2024-05-01"),
        feat(b, classname="CS_GEOMETRICO", view_date="2025-07-01"),
        feat(b, classname="CS_DESORDENADO", view_date="2020-07-01"),  # antes de 2021
    ]}))
    async with httpx.AsyncClient() as http:
        r = await inpe.deter_by_class(http, CAR)
    assert set(r["by_class"]) == {"CS_GEOMETRICO"}
    c = r["by_class"]["CS_GEOMETRICO"]
    assert c["n"] == 2 and c["last"] == "2025-07-01" and c["ha"] > 0


async def test_server_error_is_source_unavailable(wfs):
    wfs.get(url__startswith="https://terrabrasilis").mock(return_value=httpx.Response(500))
    async with httpx.AsyncClient() as http:
        with pytest.raises(SourceUnavailable):
            await inpe.biomes(http, CAR)


def test_filter_uses_srid_prefix_and_lon_lat():
    """Regla verificada contra el servidor real: sin SRID interpreta lat/lon."""
    import urllib.parse

    captured = {}

    def handler(request):
        captured["cql"] = request.url.params["CQL_FILTER"]
        return httpx.Response(200, json={"features": []})

    import asyncio

    async def go():
        with respx.mock() as router:
            router.get(url__startswith="https://terrabrasilis").mock(side_effect=handler)
            async with httpx.AsyncClient() as http:
                await inpe.biomes(http, CAR)

    asyncio.run(go())
    cql = urllib.parse.unquote(captured["cql"])
    assert cql.startswith("INTERSECTS(geom, SRID=4326;POLYGON ((-50")
