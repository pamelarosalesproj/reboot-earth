import json, os, sys, time
sys.path.insert(0, "/Users/pamelarosales/Documents/Proyectos/reboot-earth"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import query_builder as qb
import mapbiomas_api as m

OUT = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
c = m.MapBiomasClient(timeout=180)
c.sign_in(os.environ["MAPBIOMAS_EMAIL"], os.environ["MAPBIOMAS_PASSWORD"])
types = m.types_by_name(m.get_schema(c))

def base(t):
    while t["kind"] in ("NON_NULL", "LIST"): t = t["ofType"]
    return t

def sel(tname, depth, car_arg=False):
    out = []
    for f in types[tname].get("fields") or []:
        req = [a for a in f["args"] if a["type"]["kind"] == "NON_NULL"]
        if req: continue
        b = base(f["type"])
        args = "(carCode: $code)" if car_arg and any(a["name"] == "carCode" for a in f["args"]) else ""
        if b["kind"] in ("SCALAR", "ENUM"):
            out.append(f["name"] + args)
        elif b["kind"] == "OBJECT" and depth > 0:
            inner = sel(b["name"], depth - 1, car_arg)
            if inner: out.append(f"{f['name']}{args} {{ {inner} }}")
    return " ".join(out)

q = qb.full_query(c)

if len(sys.argv) > 3:
    cands = sys.argv[3:]
else:
  # Candidatos: alertas recientes, un CAR por estado (diversidad)
  cands, estados, page = [], set(), 1
  while len(cands) < N and page <= 10:
      col = c.execute("""query($p:Int){ alerts(page:$p, limit:100){ collection{ alertCode ruralPropertiesCodes } } }""",
                      {"p": page})["alerts"]["collection"]
      for a in col:
          for code in a.get("ruralPropertiesCodes") or []:
              uf = code[:2]
              if code.count("-") == 2 and uf not in estados and len(cands) < N:
                  estados.add(uf); cands.append(code)
      page += 1

indice = []
for code in cands:
    t = time.time()
    try:
        qq, omitidos = q, []
        while True:
            try:
                prop = c.execute(qq, {"code": code})["ruralProperty"]; break
            except m.GraphQLError as e:
                import re as _re
                bad = sorted(set(_re.findall(r"for \w+\.(\w+)", str(e))) - set(omitidos))
                if not bad: raise
                omitidos += bad
                for b in bad: qq = _re.sub(r"\b%s\b(?!\s*\{)" % b, "", qq)
        if omitidos: prop["_camposOmitidosPorErrorApi"] = omitidos
        try: emb = c.embargos_car(code)
        except Exception as e: emb = {"error": str(e)[:200]}
        prop["_embargos"] = emb
        prop["_descargadoEn"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if prop.get("geomRuralProperty"):
            wkt = prop["geomRuralProperty"].split(";", 1)[-1]
            prop["_geojson"] = m.wkt_to_geojson(wkt)
        with open(os.path.join(OUT, f"{code}_completo.json"), "w", encoding="utf-8") as fh:
            json.dump(prop, fh, indent=2, ensure_ascii=False)
        al = prop.get("alerts") or []
        indice.append({"carCode": code, "estado": prop.get("stateAcronym"), "areaHa": prop.get("areaHa"),
                       "totalAlertas": len(al), "totalEmbargos": (emb or {}).get("totalEmbargos")})
        print(f"OK {code} alertas={len(al)} emb={(emb or {}).get('totalEmbargos')} ({time.time()-t:.1f}s)", flush=True)
    except Exception as e:
        print(f"FALLO {code}: {str(e)[:200]}", flush=True)
ip = os.path.join(OUT, "indice.json")
prev = json.load(open(ip)) if os.path.exists(ip) else []
merged = {r["carCode"]: r for r in prev + indice}
json.dump(sorted(merged.values(), key=lambda r: r["carCode"]), open(ip, "w"), indent=2, ensure_ascii=False)
