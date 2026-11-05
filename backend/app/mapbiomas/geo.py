"""Geometría sin dependencias (portado de mapbiomas_api.py)."""

import re
from itertools import pairwise


def wkt_to_geojson(wkt: str) -> dict:
    """Convierte POLYGON / MULTIPOLYGON WKT a geometría GeoJSON."""
    wkt = wkt.strip()
    gtype = wkt.split("(", 1)[0].strip().upper()
    body = wkt[len(gtype):].strip()

    def ring(txt: str) -> list[list[float]]:
        return [[float(x), float(y)] for x, y in (p.split()[:2] for p in txt.split(","))]

    def polygon(txt: str) -> list[list[list[float]]]:
        return [ring(r) for r in re.findall(r"\(([^()]+)\)", txt)]

    if gtype == "POLYGON":
        return {"type": "Polygon", "coordinates": polygon(body[1:-1])}
    if gtype == "MULTIPOLYGON":
        polys = re.findall(r"\(((?:\([^()]+\)\s*,?\s*)+)\)", body[1:-1])
        return {"type": "MultiPolygon", "coordinates": [polygon(p) for p in polys]}
    raise ValueError(f"Tipo de geometría no soportado: {gtype}")


def parse_ewkt(ewkt: str) -> tuple[str | None, dict]:
    """'SRID=4674;MULTIPOLYGON(...)' → ('4674', geometría GeoJSON lon/lat)."""
    srid = None
    if ewkt.upper().startswith("SRID="):
        prefix, ewkt = ewkt.split(";", 1)
        srid = prefix.split("=", 1)[1]
    return srid, wkt_to_geojson(ewkt)


def interior_point(geom: dict) -> tuple[float, float]:
    """Un punto (lon, lat) dentro del polígono más grande: centroide o búsqueda en grilla."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    outer = max(polys, key=lambda p: len(p[0]))

    def inside(x: float, y: float) -> bool:
        ins = False
        for r in outer:
            for (x1, y1), (x2, y2) in pairwise(r):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    ins = not ins
        return ins

    ring = outer[0]
    cx, cy = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
    if inside(cx, cy):
        return cx, cy
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    for i in range(1, 20):
        for j in range(1, 20):
            x = min(xs) + (max(xs) - min(xs)) * i / 20
            y = min(ys) + (max(ys) - min(ys)) * j / 20
            if inside(x, y):
                return x, y
    return cx, cy
