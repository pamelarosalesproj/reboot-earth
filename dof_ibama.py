#!/usr/bin/env python3
"""
DOF (IBAMA) – Transportes de produtos florestais por CPF/CNPJ, y cruce con polígonos CAR.

Los datos abiertos del IBAMA vienen en un ZIP de ~4.6 GB con un CSV por año y UF.
Este script lee el índice del ZIP remoto con HTTP Range y descarga SOLO los CSV
de las UF/años pedidos (no baja el archivo completo).

Uso:
    python dof_ibama.py listar                                   # años/UF disponibles y tamaños
    python dof_ibama.py cnpj 04.654.691/0001-06 --uf AC --anos 2007-2008
    python dof_ibama.py cnpj <CNPJ> --uf PE --car PE-2607505-F2671DDF...  # + cruce con el CAR
    python dof_ibama.py cnpj <CNPJ> --uf PE --geojson mis_cars.geojson    # + cruce con varios polígonos

Salida: CSV con los transportes encontrados (dof_<cnpj>.csv) y, si se indica CAR/GeoJSON,
una columna POLIGONO_ORIGEN con el CAR/feature donde cae el punto de origen.

Limitaciones:
  * Pará y Mato Grosso usan Sisflora: no están en el DOF.
  * El CPF de personas físicas viene enmascarado (079.***.***-**); por CNPJ funciona.
  * La coordenada de origen es un punto (pátio/origem declarada), no un polígono.
  * Sin dependencias externas (solo librería estándar).
"""

import argparse
import csv
import io
import json
import os
import re
import struct
import sys
import urllib.request
import zlib

URL_TRANSPORTES = ("https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/"
                   "dados/DOF/DOFTransportes/DOFTransportes_csv.zip")
URL_AUTEX = ("https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/"
             "dados/DOF/DOFAutorizacoes/DOFAutorizacoes_csv.zip")


# --------------------------------------------------------------------------- #
# ZIP remoto vía HTTP Range (soporta ZIP64)
# --------------------------------------------------------------------------- #
def _get_range(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def _size(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def listar_zip(url):
    """Devuelve [{name, offset, csize, usize, method}] leyendo solo el directorio central."""
    size = _size(url)
    tail = _get_range(url, max(0, size - 70000), size - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("No se encontró el fin del directorio central")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    n_entries = struct.unpack("<H", tail[i + 10:i + 12])[0]
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF or n_entries == 0xFFFF:  # ZIP64
        j = tail.rfind(b"PK\x06\x07")
        z64_off = struct.unpack("<Q", tail[j + 8:j + 16])[0]
        z64 = _get_range(url, z64_off, z64_off + 56)
        n_entries, cd_size, cd_off = struct.unpack("<QQQ", z64[32:56])
    cd = _get_range(url, cd_off, cd_off + cd_size - 1)

    entries, p = [], 0
    while p < len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, xlen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        off = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
        # campos ZIP64 en el extra (id 0x0001), en orden: usize, csize, offset
        q = 0
        while q + 4 <= len(extra):
            hid, hlen = struct.unpack("<HH", extra[q:q + 4])
            if hid == 0x0001:
                vals, k = extra[q + 4:q + 4 + hlen], 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if off == 0xFFFFFFFF:
                    off = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
            q += 4 + hlen
        entries.append({"name": name, "offset": off, "csize": csize,
                        "usize": usize, "method": method})
        p += 46 + nlen + xlen + clen
    return entries


def leer_entrada(url, e, chunk=8 * 1024 * 1024):
    """Genera las líneas de texto de un CSV dentro del ZIP remoto (streaming)."""
    head = _get_range(url, e["offset"], e["offset"] + 29)
    nlen, xlen = struct.unpack("<HH", head[26:30])
    start = e["offset"] + 30 + nlen + xlen
    end = start + e["csize"] - 1
    d = zlib.decompressobj(-15) if e["method"] == 8 else None
    buf = b""
    pos = start
    while pos <= end:
        raw = _get_range(url, pos, min(pos + chunk - 1, end))
        pos += len(raw)
        buf += d.decompress(raw) if d else raw
        *lines, buf = buf.split(b"\n")
        for ln in lines:
            yield ln.decode("utf-8-sig", "replace").rstrip("\r")
    if d:
        buf += d.flush()
    if buf:
        yield buf.decode("utf-8-sig", "replace").rstrip("\r")


def _filtrar_entradas(entries, ufs=None, anos=None):
    out = []
    for e in entries:
        m = re.search(r"ano_(\d{4})_uf_([A-Z]{2})", e["name"])
        if not m:
            continue
        ano, uf = int(m.group(1)), m.group(2)
        if ufs and uf not in ufs:
            continue
        if anos and ano not in anos:
            continue
        out.append(dict(e, ano=ano, uf=uf))
    return out


# --------------------------------------------------------------------------- #
# Búsqueda por CPF/CNPJ
# --------------------------------------------------------------------------- #
def solo_digitos(s):
    return re.sub(r"\D", "", s or "")


def transportes_por_cnpj(cnpj, ufs=None, anos=None, rol="ambos", url=URL_TRANSPORTES, log=print):
    """
    Devuelve (columnas, filas) de transportes donde el CNPJ es remetente y/o destinatario.
    rol: "remetente" | "destinatario" | "ambos"
    Ojo: un transporte puede tener varias filas (una por produto/especie).
    """
    objetivo = solo_digitos(cnpj)
    entries = _filtrar_entradas(listar_zip(url), ufs, anos)
    if not entries:
        raise SystemExit("No hay archivos para esas UF/años.")
    total_mb = sum(e["csize"] for e in entries) / 1e6
    log(f"Leyendo {len(entries)} archivos ({total_mb:,.0f} MB comprimidos)...")

    columnas, filas = None, []
    for e in sorted(entries, key=lambda x: (x["uf"], x["ano"])):
        lines = leer_entrada(url, e)
        header = next(lines).split(";")
        columnas = columnas or header
        i_rem, i_dst = header.index("CPF_CNPJ_REMETENTE"), header.index("CPF_CNPJ_DESTINATARIO")
        n = 0
        for row in csv.reader(lines, delimiter=";"):
            if len(row) < len(header):
                continue
            es_rem = solo_digitos(row[i_rem]) == objetivo
            es_dst = solo_digitos(row[i_dst]) == objetivo
            if (rol in ("remetente", "ambos") and es_rem) or (rol in ("destinatario", "ambos") and es_dst):
                filas.append(dict(zip(header, row), ROL="remetente" if es_rem else "destinatario"))
                n += 1
        log(f"  {e['uf']} {e['ano']}: {n} filas")
    return (columnas or []) + ["ROL"], filas


# --------------------------------------------------------------------------- #
# Punto en polígono
# --------------------------------------------------------------------------- #
def _en_anillo(x, y, ring):
    ins = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def punto_en_geom(x, y, geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if _en_anillo(x, y, poly[0]) and not any(_en_anillo(x, y, h) for h in poly[1:]):
            return True
    return False


def distancia_km(x1, y1, x2, y2):
    import math
    r = 6371.0
    p1, p2 = math.radians(y1), math.radians(y2)
    dphi, dl = p2 - p1, math.radians(x2 - x1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _num(s):
    try:
        return float((s or "").replace(",", "."))
    except ValueError:
        return None


def cruzar_con_poligonos(filas, features, campo_lat="LATITUDE_ORIGEM", campo_lon="LONGITUDE_ORIGEM"):
    """Agrega POLIGONO_ORIGEN (nombre del feature que contiene el punto) y DIST_KM al más cercano."""
    centros = []
    for f in features:
        g = f["geometry"]
        ring = (g["coordinates"][0][0] if g["type"] == "MultiPolygon" else g["coordinates"][0])
        centros.append((sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)))
    for fila in filas:
        lat, lon = _num(fila.get(campo_lat)), _num(fila.get(campo_lon))
        fila["POLIGONO_ORIGEN"], fila["DIST_KM_POLIGONO_MAS_CERCANO"] = "", ""
        if lat is None or lon is None:
            fila["POLIGONO_ORIGEN"] = "(sin coordenadas)"
            continue
        dentro = [f["properties"].get("propertyCode") or f["properties"].get("name") or str(i)
                  for i, f in enumerate(features) if punto_en_geom(lon, lat, f["geometry"])]
        fila["POLIGONO_ORIGEN"] = "|".join(dentro) or "(fuera)"
        if not dentro and centros:
            fila["DIST_KM_POLIGONO_MAS_CERCANO"] = round(
                min(distancia_km(lon, lat, cx, cy) for cx, cy in centros), 2)
    return filas


def _rango_anos(s):
    if not s:
        return None
    out = set()
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    c = sub.add_parser("cnpj")
    c.add_argument("cnpj")
    c.add_argument("--uf", help="UF(s) separadas por coma, ej. PE,AL (muy recomendado)")
    c.add_argument("--anos", help="ej. 2020-2024 o 2019,2023")
    c.add_argument("--rol", default="ambos", choices=["ambos", "remetente", "destinatario"])
    c.add_argument("--car", action="append", help="Código CAR para cruzar (repetible); usa MapBiomas")
    c.add_argument("--geojson", help="GeoJSON con polígonos para cruzar")
    c.add_argument("--out", help="CSV de salida")
    a = ap.parse_args()

    if a.cmd == "listar":
        ents = _filtrar_entradas(listar_zip(URL_TRANSPORTES))
        resumen = {}
        for e in ents:
            resumen.setdefault(e["uf"], []).append((e["ano"], e["csize"]))
        for uf in sorted(resumen):
            anos = sorted(resumen[uf])
            mb = sum(s for _, s in anos) / 1e6
            print(f"{uf}: {anos[0][0]}–{anos[-1][0]} ({len(anos)} archivos, {mb:,.0f} MB)")
        return

    ufs = set(a.uf.upper().split(",")) if a.uf else None
    cols, filas = transportes_por_cnpj(a.cnpj, ufs, _rango_anos(a.anos), a.rol)

    features = []
    if a.geojson:
        features += json.load(open(a.geojson, encoding="utf-8"))["features"]
    if a.car:
        from mapbiomas_api import MapBiomasClient
        cli = MapBiomasClient()
        for code in a.car:
            f = cli.poligono_car(code)
            if f:
                features.append(f)
            else:
                print(f"CAR {code} sin polígono en MapBiomas", file=sys.stderr)
    if features and filas:
        cruzar_con_poligonos(filas, features)
        cols += ["POLIGONO_ORIGEN", "DIST_KM_POLIGONO_MAS_CERCANO"]

    out = a.out or f"dof_{solo_digitos(a.cnpj)}.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    dofs = {f.get("NUM_SERIE_DOF") for f in filas}
    vol = {}
    for f in filas:
        k = (f.get("ROL"), f.get("UNIDADE"))
        vol[k] = vol.get(k, 0) + (_num(f.get("VOLUME")) or 0)
    print(f"\n{len(filas)} filas, {len(dofs)} DOFs distintos → {out}")
    for (rol, un), v in sorted(vol.items()):
        print(f"  {rol}: {v:,.3f} {un}")
    if features and filas:
        from collections import Counter
        print("Origen por polígono:", dict(Counter(f["POLIGONO_ORIGEN"] for f in filas)))


if __name__ == "__main__":
    main()
