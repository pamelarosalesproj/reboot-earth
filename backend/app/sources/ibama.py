"""Áreas embargadas do IBAMA (Pamgia, ArcGIS FeatureServer público): respaldo dos embargos (feature 007).

Uso: só quando o MapBiomas não determina os embargos de um CAR (hoje `pointInformation` responde 500 ao
pedir campos de embargo; specs/007-embargos-ibama/research.md R1). Regras verificadas em 2026-11-08 (R3–R5):
- Consulta espacial `esriSpatialRelIntersects` com a envoltória convexa simplificada do CAR (superconjunto);
  a sobreposição exata é calculada aqui com shapely.
- Um embargo conta como do CAR se a sobreposição for ≥ IBAMA_MIN_OVERLAP_HA (descarta roces de borda).
- A camada não indica embargos levantados: todo embargo que conta é vigente (`expired_at=None`).
- `outFields` explícito: nunca se pede nome nem CPF/CNPJ do embargado (princípio III).
- Resposta truncada (`exceededTransferLimit`) = fonte indisponível: nunca uma lista parcial como completa.
"""

import json
import logging
from datetime import UTC, date, datetime

import httpx
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from app.config import settings
from app.schemas import Embargo
from app.sources import SourceUnavailable
from app.sources.geo import area_ha, car_polygon

log = logging.getLogger("app.ibama")

IBAMA_MIN_OVERLAP_HA = 0.1
OUT_FIELDS = "num_tad,serie_tad,num_processo,dat_embargo,qtd_area_embargada,des_tad"
MAX_RECORDS = 2000


def _esri_rings(geom: BaseGeometry) -> dict:
    """Envoltória convexa simplificada (como `inpe._filter_geom`) em anéis ESRI, lon/lat EPSG:4326."""
    hull = geom.buffer(0.001).convex_hull.simplify(0.0005)
    return {"rings": [[list(p) for p in hull.exterior.coords]], "spatialReference": {"wkid": 4326}}


def _epoch_date(v) -> date | None:
    if v is None or v == "":
        return None
    try:
        return datetime.fromtimestamp(float(v) / 1000, tz=UTC).date()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _str(v) -> str | None:
    v = str(v).strip() if v is not None else ""
    return v or None


def embargoes_from_features(features: list[dict], car_geom: BaseGeometry) -> list[Embargo]:
    """Embargos do CAR a partir das features GeoJSON do IBAMA (função pura)."""
    from app.services.car_service import merge_embargo_items  # evita import circular

    items: list[dict] = []
    for f in features:
        p = f.get("properties") or {}
        try:
            overlap = round(area_ha(car_geom.intersection(shape(f["geometry"]).buffer(0)), lat=car_geom.centroid.y), 2)
        except Exception:  # noqa: BLE001 — geometria não interpretável: conta (critério conservador)
            log.warning("geometria IBAMA não interpretável (termo %s)", p.get("num_tad"))
            overlap = None
        if overlap is not None and overlap < IBAMA_MIN_OVERLAP_HA:
            continue
        num, serie = _str(p.get("num_tad")), _str(p.get("serie_tad"))
        term = f"{num}/{serie}" if num and serie else num
        items.append({
            "source": "IBAMA",
            "processCode": _str(p.get("num_processo")),
            "code": term,
            "areaHa": p.get("qtd_area_embargada"),
            "sourceRegisteredAt": _epoch_date(p.get("dat_embargo")),
            "sourceExpiredAt": None,
            "description": p.get("des_tad"),
            "term": term,
            "overlap_ha": overlap,
        })
    return merge_embargo_items(items)


async def fetch_embargoes(geometry: dict) -> list[Embargo]:
    """Embargos do IBAMA que se sobrepõem ≥ 0,1 ha ao polígono do CAR. Lança SourceUnavailable."""
    car_geom = car_polygon(geometry)
    if car_geom.is_empty:
        raise SourceUnavailable("ibama: polígono do CAR vazio")
    form = {
        "f": "geojson",
        "geometry": json.dumps(_esri_rings(car_geom)),
        "geometryType": "esriGeometryPolygon",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "true",
        "outFields": OUT_FIELDS,
        "resultRecordCount": str(MAX_RECORDS),
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ibama_timeout_s) as http:
            r = await http.post(settings.ibama_embargoes_url, data=form)
        r.raise_for_status()
        body = r.json()
    except (httpx.HTTPError, ValueError) as e:
        raise SourceUnavailable(f"ibama: {type(e).__name__}") from e
    if not isinstance(body, dict) or "error" in body:
        raise SourceUnavailable(f"ibama: {str(body.get('error') if isinstance(body, dict) else body)[:120]}")
    if body.get("exceededTransferLimit") or (body.get("properties") or {}).get("exceededTransferLimit"):
        raise SourceUnavailable("ibama: resposta truncada")
    return embargoes_from_features(body.get("features") or [], car_geom)
