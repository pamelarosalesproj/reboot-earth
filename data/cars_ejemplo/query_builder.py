import json, sys
sys.path.insert(0, "/Users/pamelarosales/Documents/Proyectos/reboot-earth")
import mapbiomas_api as m
REF = "/Users/pamelarosales/Documents/Proyectos/reboot-earth/PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0_completo.json"

def base(t):
    while t["kind"] in ("NON_NULL", "LIST"): t = t["ofType"]
    return t

def keys_of(v):
    if isinstance(v, dict): return v
    if isinstance(v, list):
        r = {}
        for x in v:
            if isinstance(x, dict):
                for k, y in x.items(): r.setdefault(k, y)
        return r
    return {}

def build(types, tname, sample):
    """Selección limitada a los campos que aparecen en el ejemplo `sample`."""
    out = []
    fields = {f["name"]: f for f in types[tname].get("fields") or []}
    for k, v in sample.items():
        f = fields.get(k)
        if not f: continue
        b = base(f["type"])
        args = "(carCode: $code)" if any(a["name"] == "carCode" for a in f["args"]) else ""
        if b["kind"] == "OBJECT":
            inner = build(types, b["name"], keys_of(v))
            if inner: out.append(f"{k}{args} {{ {inner} }}")
        else:
            out.append(k + args)
    return " ".join(out)

def full_query(client):
    types = m.types_by_name(m.get_schema(client))
    rp = base([f for f in types["Query"]["fields"] if f["name"] == "ruralProperty"][0]["type"])["name"]
    ref = json.load(open(REF))
    return "query($code: String!) { ruralProperty(propertyCode: $code) { %s } }" % build(types, rp, ref)
