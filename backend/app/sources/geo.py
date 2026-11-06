"""Geometría del CAR con shapely (research R3)."""

import math

from shapely import wkt
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

M2_PER_HA = 10_000
M_PER_DEG = 111_320


def car_polygon(geometry: dict | str) -> BaseGeometry:
    """Polígono del CAR a partir de GeoJSON (dict) o EWKT ("SRID=4674;MULTIPOLYGON(...)")."""
    if isinstance(geometry, dict):
        return shape(geometry).buffer(0)
    return wkt.loads(geometry.split(";", 1)[-1]).buffer(0)


def area_ha(geom: BaseGeometry, lat: float | None = None) -> float:
    """Área aproximada en ha (equirectangular en la latitud dada o del centroide; error < 1 %
    en CARs de hasta decenas de miles de ha)."""
    if geom.is_empty:
        return 0.0
    lat = geom.centroid.y if lat is None else lat
    return geom.area * (M_PER_DEG**2) * math.cos(math.radians(lat)) / M2_PER_HA
