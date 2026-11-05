#!/usr/bin/env python3
"""
Cliente para la API GraphQL de MapBiomas Alerta (staging).

Endpoint: https://staging.plataforma.alerta.mapbiomas.org/api/v2/graphql

Uso:
    python mapbiomas_api.py docs              # Genera schema.json + SCHEMA.md (documentación legible)
    python mapbiomas_api.py resumen           # Lista queries y mutations en consola
    python mapbiomas_api.py tipo AlertData    # Muestra los campos/valores de un tipo concreto
    python mapbiomas_api.py demo              # Ejecuta consultas de ejemplo
    python mapbiomas_api.py car <CODIGO_CAR>  # Desmatamento (alertas) en un CAR
    python mapbiomas_api.py poligono <CAR>    # Exporta el polígono del CAR a GeoJSON
    python mapbiomas_api.py embargos <CAR>    # Embargos (IBAMA, ICMBio, estatales) del CAR

Autenticación (necesaria para queries como `alerts`, `alert`, `ruralProperty`...):
    export MAPBIOMAS_EMAIL="tu@email.com"
    export MAPBIOMAS_PASSWORD="tu_password"

Solo usa la librería estándar de Python (no requiere instalar nada).
"""

import json
import os
import sys
import urllib.error
import urllib.request


def _load_dotenv(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Carga variables KEY=VALUE desde .env (sin pisar las ya definidas en el entorno)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

API_URL = os.environ.get(
    "MAPBIOMAS_API_URL",
    "https://staging.plataforma.alerta.mapbiomas.org/api/v2/graphql",
)


# --------------------------------------------------------------------------- #
# Cliente
# --------------------------------------------------------------------------- #
class GraphQLError(Exception):
    pass


class MapBiomasClient:
    def __init__(self, url=API_URL, token=None, timeout=60):
        self.url = url
        self.token = token
        self.timeout = timeout

    def execute(self, query, variables=None):
        """Ejecuta una query/mutation GraphQL y devuelve el bloque `data`."""
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(self.url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise GraphQLError(f"HTTP {e.code}: {e.read().decode()[:500]}") from e

        if body.get("errors"):
            msgs = "; ".join(err.get("message", str(err)) for err in body["errors"])
            raise GraphQLError(msgs)
        return body.get("data")

    # ---- Autenticación ---------------------------------------------------- #
    def sign_in(self, email, password):
        data = self.execute(
            """
            mutation SignIn($email: String!, $password: String!) {
              signIn(email: $email, password: $password) { token }
            }
            """,
            {"email": email, "password": password},
        )
        self.token = data["signIn"]["token"]
        return self.token

    # ---- Queries públicas (no requieren token) ---------------------------- #
    def version(self):
        return self.execute("{ version { version buildDate buildHash } }")["version"]

    def last_alert_publication(self):
        return self.execute(
            "{ lastAlertPublication { publishedAt total publicationRange } }"
        )["lastAlertPublication"]

    def alert_date_range(self):
        return self.execute(
            "{ alertDateRange { minDetectedAt maxDetectedAt minPublishedAt maxPublishedAt } }"
        )["alertDateRange"]

    # ---- Queries que requieren token -------------------------------------- #
    def alerts(self, page=1, limit=10, **filtros):
        """
        Busca alertas. Filtros opcionales (ver `python mapbiomas_api.py tipo Query`):
          startDate, endDate (YYYY-MM-DD), dateType (DetectedAt|PublishedAt),
          sources ([Sad, Glad, DeterbAmazonia...]), territoryIds, startSize, endSize, ...
        """
        query = """
        query Alerts($page: Int, $limit: Int, $startDate: BaseDate, $endDate: BaseDate,
                     $dateType: DateTypes, $sources: [SourceTypes!], $territoryIds: [Int!]) {
          alerts(page: $page, limit: $limit, startDate: $startDate, endDate: $endDate,
                 dateType: $dateType, sources: $sources, territoryIds: $territoryIds) {
            metadata { currentPage limitValue totalCount totalPages }
            collection {
              alertCode
              areaHa
              detectedAt
              publishedAt
              sources
            }
          }
        }
        """
        return self.execute(query, {"page": page, "limit": limit, **filtros})["alerts"]

    def alert(self, alert_code):
        query = """
        query Alert($alertCode: Int!) {
          alert(alertCode: $alertCode) {
            alertCode areaHa detectedAt publishedAt sources crossedBiomes crossedCities
          }
        }
        """
        return self.execute(query, {"alertCode": alert_code})["alert"]

    # ---- Desmatamento por CAR -------------------------------------------- #
    def desmatamento_por_car(self, car_code):
        """
        Devuelve la propiedad rural (CAR/SIGEF/SNCI) y todas las alertas de
        desmatamento que la cruzan, con el área de cada alerta dentro del CAR,
        en Reserva Legal (RL), en APP, y si hay embargo o autorización.
        """
        query = """
        query DesmatamentoCar($code: String!) {
          ruralProperty(propertyCode: $code) {
            propertyCode propertyType carType areaHa state stateAcronym carUpdatedAt
            alerts {
              alertCode detectedAt publishedAt areaHa sources crossedBiomes crossedCities
              crossedRuralProperties(carCode: $code) { code alertAreaInCar }
              crossedLegalReservesList
              crossedPermanentProtectedAreaList
              crossedEmbargoesRuralPropertiesTotal
              crossedDeforestationAuthorizationsArea
            }
          }
        }
        """
        prop = self.execute(query, {"code": car_code})["ruralProperty"]
        if not prop:
            return None

        filas = []
        for a in prop.get("alerts") or []:
            cruces = a.pop("crossedRuralProperties") or []
            a["areaEnCarHa"] = sum(c.get("alertAreaInCar") or 0 for c in cruces)
            # Las listas incluyen RL/APP de TODOS los CARs que cruza la alerta;
            # nos quedamos solo con las del CAR consultado.
            def solo_este_car(lista):
                return sum(x.get("intersection_area") or 0 for x in (lista or [])
                           if x.get("rural_property_code") == car_code)
            a["areaEnReservaLegalDelCarHa"] = solo_este_car(a.pop("crossedLegalReservesList"))
            a["areaEnAppDelCarHa"] = solo_este_car(a.pop("crossedPermanentProtectedAreaList"))
            filas.append(a)
        prop["alerts"] = filas
        prop["resumen"] = {
            "totalAlertas": len(filas),
            "areaAlertasEnCarHa": round(sum(a["areaEnCarHa"] for a in filas), 4),
            "areaEnReservaLegalHa": round(sum(a["areaEnReservaLegalDelCarHa"] for a in filas), 4),
            "areaEnAppHa": round(sum(a["areaEnAppDelCarHa"] for a in filas), 4),
        }
        return prop

    EMBARGO_FIELDS = """carCode embargoedAreasCount embargoedAreas {
        code source processCode areaHa description legislation
        sourceRegisteredAt sourceExpiredAt updatedAt }"""

    def embargos_car(self, car_code):
        """
        Embargos (IBAMA, ICMBio, órganos estatales) registrados en un CAR.
        Vía 1: a través de una alerta que cruce el CAR (fiable).
        Vía 2: si el CAR no tiene alertas, consulta un punto dentro del CAR
               con pointInformation (en producción a veces devuelve HTTP 500).
        Devuelve {"carCode", "via", "embargos": [...]} o lanza GraphQLError.
        """
        q = """query($c: [ID!], $code: String) {
          alerts(propertyCodes: $c, limit: 1) {
            collection { ruralProperties(carCode: $code) { %s } }
          }
        }""" % self.EMBARGO_FIELDS
        col = self.execute(q, {"c": [car_code], "code": car_code})["alerts"]["collection"]
        rps, via = [], None
        if col:
            rps, via = col[0]["ruralProperties"] or [], "alertas"
        else:
            feat = self.poligono_car(car_code)
            if not feat:
                return None
            x, y = _punto_interior(feat["geometry"])
            d = 0.0001
            q2 = """query($b: BoundingBoxInput) {
              pointInformation(boundingBox: $b) { ruralProperties { %s } }
            }""" % self.EMBARGO_FIELDS
            b = {"swLat": y - d, "swLng": x - d, "neLat": y + d, "neLng": x + d}
            via = "pointInformation"
            try:
                rps = self.execute(q2, {"b": b})["pointInformation"]["ruralProperties"]
            except GraphQLError as e:
                return {"carCode": car_code, "via": via, "totalEmbargos": None,
                        "error": "No determinable: el CAR no tiene alertas y la API "
                                 f"falla al consultar embargos por punto ({str(e)[:60]})"}

        # La API repite cada embargo (mismo proceso) con distintos `code`/descripciones;
        # agrupamos por (fuente, nº de proceso) y juntamos las descripciones.
        por_proceso = {}
        for rp in rps:
            if rp.get("carCode") != car_code:
                continue
            for e in rp.get("embargoedAreas") or []:
                key = (e.get("source"), e.get("processCode"))
                if key not in por_proceso:
                    por_proceso[key] = dict(e, descriptions=[])
                    por_proceso[key].pop("description", None)
                desc = (e.get("description") or "").strip()
                if desc and desc not in por_proceso[key]["descriptions"]:
                    por_proceso[key]["descriptions"].append(desc)
        embargos = sorted(por_proceso.values(), key=lambda e: e.get("sourceRegisteredAt") or "")
        return {"carCode": car_code, "via": via, "totalEmbargos": len(embargos),
                "areaEmbargadaHa": round(sum(e.get("areaHa") or 0 for e in embargos), 4),
                "embargos": embargos}

    def poligono_car(self, car_code):
        """
        Devuelve el polígono del CAR como GeoJSON Feature (coordenadas lon/lat,
        SIRGAS 2000 / EPSG:4674). La API lo entrega en EWKT: 'SRID=4674;MULTIPOLYGON(...)'.
        """
        query = """
        query PoligonoCar($code: String!) {
          ruralProperty(propertyCode: $code) {
            propertyCode propertyType areaHa stateAcronym carUpdatedAt geomRuralProperty
          }
        }
        """
        prop = self.execute(query, {"code": car_code})["ruralProperty"]
        if not prop or not prop.get("geomRuralProperty"):
            return None
        wkt = prop.pop("geomRuralProperty")
        srid = None
        if wkt.upper().startswith("SRID="):
            srid, wkt = wkt.split(";", 1)
            srid = srid.split("=")[1]
        prop["srid"] = srid
        return {"type": "Feature", "properties": prop, "geometry": wkt_to_geojson(wkt)}

    def alertas_de_cars(self, car_codes, page=1, limit=50):
        """Alertas que cruzan uno o varios CARs (paginado), vía filtro propertyCodes."""
        query = """
        query AlertasCars($codes: [ID!], $page: Int, $limit: Int) {
          alerts(propertyCodes: $codes, page: $page, limit: $limit) {
            metadata { totalCount totalPages currentPage }
            collection { alertCode detectedAt areaHa sources ruralPropertiesCodes }
          }
        }
        """
        return self.execute(query, {"codes": car_codes, "page": page, "limit": limit})["alerts"]


# --------------------------------------------------------------------------- #
# Introspección: explorar y documentar el esquema
# --------------------------------------------------------------------------- #
TYPE_REF = """
fragment TypeRef on __Type {
  kind name
  ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } }
}
"""

INTROSPECTION_QUERY = TYPE_REF + """
query Introspection {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      kind name description
      fields(includeDeprecated: true) {
        name description isDeprecated deprecationReason
        args { name description defaultValue type { ...TypeRef } }
        type { ...TypeRef }
      }
      inputFields { name description defaultValue type { ...TypeRef } }
      enumValues(includeDeprecated: true) { name description }
    }
  }
}
"""


def type_str(t):
    """Convierte una referencia de tipo a notación GraphQL: [String!]!"""
    if t is None:
        return "?"
    if t["kind"] == "NON_NULL":
        return type_str(t["ofType"]) + "!"
    if t["kind"] == "LIST":
        return "[" + type_str(t["ofType"]) + "]"
    return t["name"]


def get_schema(client):
    return client.execute(INTROSPECTION_QUERY)["__schema"]


def types_by_name(schema):
    return {t["name"]: t for t in schema["types"]}


def print_field(f, indent="  "):
    args = ", ".join(f"{a['name']}: {type_str(a['type'])}" for a in f.get("args") or [])
    sig = f"{f['name']}({args})" if args else f["name"]
    print(f"{indent}{sig} -> {type_str(f['type'])}")
    if f.get("description"):
        print(f"{indent}    # {f['description'].strip()}")


def cmd_resumen(client):
    schema = get_schema(client)
    types = types_by_name(schema)
    for root in ("queryType", "mutationType"):
        if not schema.get(root):
            continue
        name = schema[root]["name"]
        print(f"\n===== {name.upper()} =====")
        for f in types[name]["fields"]:
            print_field(f)
            print()


def cmd_tipo(client, name):
    types = types_by_name(get_schema(client))
    t = types.get(name)
    if not t:
        sugeridos = [n for n in types if name.lower() in n.lower()]
        print(f"Tipo '{name}' no encontrado. ¿Quizá: {', '.join(sugeridos[:15])}?")
        return
    print(f"{t['kind']} {t['name']}")
    if t.get("description"):
        print(f"  {t['description']}")
    for f in t.get("fields") or []:
        print_field(f)
    for f in t.get("inputFields") or []:
        print(f"  {f['name']}: {type_str(f['type'])}")
    for e in t.get("enumValues") or []:
        print(f"  - {e['name']}" + (f"  # {e['description']}" if e.get("description") else ""))


def cmd_docs(client, out_dir="."):
    schema = get_schema(client)
    types = types_by_name(schema)

    with open(os.path.join(out_dir, "schema.json"), "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)

    lines = [f"# Esquema GraphQL – MapBiomas Alerta\n", f"Endpoint: `{client.url}`\n"]

    def fields_md(t):
        out = []
        for f in t.get("fields") or []:
            args = ", ".join(f"{a['name']}: {type_str(a['type'])}" for a in f.get("args") or [])
            sig = f"{f['name']}({args})" if args else f["name"]
            out.append(f"- `{sig}` → `{type_str(f['type'])}`")
            if f.get("description"):
                out.append(f"  - {f['description'].strip()}")
        return out

    for root in ("queryType", "mutationType"):
        if schema.get(root):
            name = schema[root]["name"]
            lines += [f"\n## {name}\n"] + fields_md(types[name])

    lines.append("\n## Tipos\n")
    for t in sorted(schema["types"], key=lambda x: x["name"]):
        if t["name"].startswith("__") or t["name"] in ("Query", "Mutation"):
            continue
        lines.append(f"\n### {t['name']} ({t['kind']})\n")
        if t.get("description"):
            lines.append(t["description"].strip() + "\n")
        lines += fields_md(t)
        for f in t.get("inputFields") or []:
            lines.append(f"- `{f['name']}`: `{type_str(f['type'])}`")
        for e in t.get("enumValues") or []:
            lines.append(f"- `{e['name']}`")

    with open(os.path.join(out_dir, "SCHEMA.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Generados schema.json y SCHEMA.md ({len(schema['types'])} tipos)")


def cmd_demo(client):
    print("Versión API:", client.version())
    print("Última publicación:", client.last_alert_publication())
    print("Rango de fechas:", client.alert_date_range())

    email, password = os.environ.get("MAPBIOMAS_EMAIL"), os.environ.get("MAPBIOMAS_PASSWORD")
    if not (email and password):
        print("\n(Define MAPBIOMAS_EMAIL y MAPBIOMAS_PASSWORD para probar las queries autenticadas.)")
        return

    client.sign_in(email, password)
    print("\nSesión iniciada. Buscando 5 alertas...")
    res = client.alerts(limit=5)
    print("Metadata:", res["metadata"])
    for a in res["collection"]:
        print(" ", a)


def _punto_interior(geom):
    """Un punto (lon, lat) dentro del polígono: prueba el centroide y, si cae fuera,
    busca en una grilla dentro del bbox (ray casting)."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    outer = max(polys, key=lambda p: len(p[0]))

    def dentro(x, y):
        ins = False
        for ring in outer:
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    ins = not ins
        return ins

    ring = outer[0]
    cx, cy = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
    if dentro(cx, cy):
        return cx, cy
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    for i in range(1, 20):
        for j in range(1, 20):
            x = min(xs) + (max(xs) - min(xs)) * i / 20
            y = min(ys) + (max(ys) - min(ys)) * j / 20
            if dentro(x, y):
                return x, y
    return cx, cy


def wkt_to_geojson(wkt):
    """Convierte POLYGON / MULTIPOLYGON WKT a geometría GeoJSON (sin dependencias)."""
    import re

    wkt = wkt.strip()
    gtype = wkt.split("(", 1)[0].strip().upper()
    body = wkt[len(gtype):].strip()

    def ring(txt):
        return [[float(x), float(y)] for x, y in (p.split()[:2] for p in txt.split(","))]

    def polygon(txt):  # txt: "(x y, ...), (x y, ...)"
        return [ring(r) for r in re.findall(r"\(([^()]+)\)", txt)]

    if gtype == "POLYGON":
        return {"type": "Polygon", "coordinates": polygon(body[1:-1])}
    if gtype == "MULTIPOLYGON":
        polys = re.findall(r"\(((?:\([^()]+\)\s*,?\s*)+)\)", body[1:-1])
        return {"type": "MultiPolygon", "coordinates": [polygon(p) for p in polys]}
    raise ValueError(f"Tipo de geometría no soportado: {gtype}")


def main():
    client = MapBiomasClient(token=os.environ.get("MAPBIOMAS_TOKEN"))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "resumen"
    try:
        if cmd == "docs":
            cmd_docs(client)
        elif cmd == "resumen":
            cmd_resumen(client)
        elif cmd == "tipo" and len(sys.argv) > 2:
            cmd_tipo(client, sys.argv[2])
        elif cmd == "demo":
            cmd_demo(client)
        elif cmd == "car" and len(sys.argv) > 2:
            email, pwd = os.environ.get("MAPBIOMAS_EMAIL"), os.environ.get("MAPBIOMAS_PASSWORD")
            if not client.token and email and pwd:
                client.sign_in(email, pwd)
            res = client.desmatamento_por_car(sys.argv[2])
            print(json.dumps(res, indent=2, ensure_ascii=False) if res
                  else "CAR no encontrado o sin alertas cruzadas.")
        elif cmd == "embargos" and len(sys.argv) > 2:
            email, pwd = os.environ.get("MAPBIOMAS_EMAIL"), os.environ.get("MAPBIOMAS_PASSWORD")
            if not client.token and email and pwd:
                client.sign_in(email, pwd)
            res = client.embargos_car(sys.argv[2])
            print(json.dumps(res, indent=2, ensure_ascii=False) if res else "CAR no encontrado.")
        elif cmd == "poligono" and len(sys.argv) > 2:
            feat = client.poligono_car(sys.argv[2])
            if not feat:
                print("CAR no encontrado o sin geometría.")
            else:
                out = sys.argv[3] if len(sys.argv) > 3 else f"{sys.argv[2]}.geojson"
                with open(out, "w", encoding="utf-8") as fh:
                    json.dump({"type": "FeatureCollection", "features": [feat]}, fh)
                g = feat["geometry"]
                n = sum(len(r) for p in g["coordinates"] for r in p) if g["type"] == "MultiPolygon" \
                    else sum(len(r) for r in g["coordinates"])
                print(json.dumps(feat["properties"], indent=2, ensure_ascii=False))
                print(f"{g['type']} con {n} vértices guardado en {out}")
        else:
            print(__doc__)
    except GraphQLError as e:
        print("Error de la API:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
