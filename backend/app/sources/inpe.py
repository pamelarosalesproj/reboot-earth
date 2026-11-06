"""INPE TerraBrasilis (WFS público, sin credenciales): biomas, PRODES, DETER y focos de calor.

Reglas verificadas el 2026-11-06 (specs/003-car-indicators/research.md R2):
- WFS 1.1.0. El filtro espacial va en CQL como INTERSECTS(geom, SRID=4326;<WKT lon lat>):
  sin el prefijo SRID el servidor interpreta lat/lon; y el parámetro `bbox` compara cajas
  (el bioma Amazonía "cruzaría" un CAR del Cerrado).
- Se envía la envolvente convexa simplificada del CAR (superconjunto) y la intersección exacta
  se hace en local con shapely.
"""

from collections import defaultdict
from datetime import date, timedelta

import httpx
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.config import settings
from app.sources import SourceUnavailable
from app.sources.geo import area_ha

BIOME_LAYER = "prodes-brasil-nb:biomas_brasil"
PRODES_LAYERS = {  # bioma (nombre en la capa de biomas) → capas anual y acumulada
    "Amazônia": ("prodes-amazon-nb:yearly_deforestation_biome", "prodes-amazon-nb:accumulated_deforestation_2007_biome"),
    "Cerrado": ("prodes-cerrado-nb:yearly_deforestation", "prodes-cerrado-nb:accumulated_deforestation_2000"),
    "Caatinga": ("prodes-caatinga-nb:yearly_deforestation", "prodes-caatinga-nb:accumulated_deforestation_2000"),
    "Mata Atlântica": ("prodes-mata-atlantica-nb:yearly_deforestation",
                       "prodes-mata-atlantica-nb:accumulated_deforestation_2000"),
    "Pampa": ("prodes-pampa-nb:yearly_deforestation", "prodes-pampa-nb:accumulated_deforestation_2000"),
    "Pantanal": ("prodes-pantanal-nb:yearly_deforestation", "prodes-pantanal-nb:accumulated_deforestation_2000"),
}
DETER_LAYER = "deter-amz:deter_amz"
FIRE_LAYER = "bdqueimadas2:focos"
DETER_SINCE = "2021-01-01"


def _filter_geom(geom: BaseGeometry) -> str:
    return geom.buffer(0.001).convex_hull.simplify(0.0005).wkt


async def wfs(http: httpx.AsyncClient, url: str, layer: str, geom: BaseGeometry, extra_cql: str | None = None,
              geom_name: str = "geom", properties: str | None = None) -> list[dict]:
    cql = f"INTERSECTS({geom_name}, SRID=4326;{_filter_geom(geom)})"
    if extra_cql:
        cql += f" AND {extra_cql}"
    params = {"service": "WFS", "version": "1.1.0", "request": "GetFeature", "typeName": layer,
              "outputFormat": "application/json", "maxFeatures": "20000", "CQL_FILTER": cql}
    if properties:
        params["propertyName"] = properties
    try:
        r = await http.get(url, params=params, timeout=settings.inpe_timeout_s)
        r.raise_for_status()
        return r.json().get("features") or []
    except (httpx.HTTPError, ValueError) as e:
        raise SourceUnavailable(f"{layer}: {type(e).__name__}") from e


def _clip(feature: dict, geom: BaseGeometry) -> BaseGeometry | None:
    if not feature.get("geometry"):
        return None
    inter = shape(feature["geometry"]).buffer(0).intersection(geom)
    return None if inter.is_empty else inter


async def biomes(http: httpx.AsyncClient, geom: BaseGeometry) -> set[str]:
    feats = await wfs(http, settings.inpe_wfs_url, BIOME_LAYER, geom, properties="bioma")
    return {f["properties"]["bioma"] for f in feats if f.get("properties", {}).get("bioma")}


async def prodes_loss(http: httpx.AsyncClient, geom: BaseGeometry, car_biomes: set[str]) -> dict:
    """% de vegetación nativa remanescente = 1 − área desmatada (unión de todas las capas) / área del CAR."""
    lat = geom.centroid.y
    clipped, by_year = [], defaultdict(list)
    for biome in sorted(car_biomes & PRODES_LAYERS.keys()):
        yearly, accumulated = PRODES_LAYERS[biome]
        for layer in (yearly, accumulated):
            for f in await wfs(http, settings.inpe_wfs_url, layer, geom):
                if (g := _clip(f, geom)) is None:
                    continue
                clipped.append(g)
                year = (f.get("properties") or {}).get("year")
                if layer == yearly and year:
                    by_year[str(int(year))].append(g)
    car_ha = area_ha(geom, lat)
    lost = area_ha(unary_union(clipped), lat) if clipped else 0.0
    return {
        "remaining_pct": round(100 * max(0.0, 1 - lost / car_ha), 1) if car_ha else 0.0,
        "deforested_ha": round(lost, 1),
        "by_year": {y: round(area_ha(unary_union(gs), lat), 2) for y, gs in sorted(by_year.items())},
    }


async def deter_by_class(http: httpx.AsyncClient, geom: BaseGeometry) -> dict:
    lat = geom.centroid.y
    out: dict[str, dict] = {}
    for f in await wfs(http, settings.inpe_wfs_url, DETER_LAYER, geom, f"view_date >= '{DETER_SINCE}'"):
        p = f.get("properties") or {}
        if str(p.get("view_date", "")) < DETER_SINCE or (g := _clip(f, geom)) is None:
            continue
        c = out.setdefault(p.get("classname") or "?", {"n": 0, "ha": 0.0, "last": None})
        c["n"] += 1
        c["ha"] = round(c["ha"] + area_ha(g, lat), 2)
        c["last"] = max(c["last"] or "", str(p.get("view_date"))[:10])
    return {"by_class": out}


async def hotspots_12m(http: httpx.AsyncClient, geom: BaseGeometry, today: date) -> dict:
    since = (today - timedelta(days=365)).isoformat()
    feats = await wfs(http, settings.inpe_fire_wfs_url, FIRE_LAYER, geom,
                      f"data_hora_gmt >= '{since}T00:00:00Z' AND eh_satelite_referencia = true",
                      geom_name="geometria")
    by_month: dict[str, int] = defaultdict(int)
    for f in feats:
        p = f.get("properties") or {}
        when = str(p.get("data_hora_gmt") or "")[:10]
        if not when or when < since or p.get("eh_satelite_referencia") is False:
            continue
        if f.get("geometry") and geom.covers(shape(f["geometry"])):
            by_month[when[:7]] += 1
    return {"count": sum(by_month.values()), "by_month": dict(sorted(by_month.items()))}
