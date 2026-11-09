"""Dados do relatório do CNPJ para a IA (feature 008). Funções puras.

A IA recebe só o que o sistema já calculou (detalhe, indicadores, nível e motivos de cada CAR e o nível do
CNPJ), com pseudônimos ("Imóvel A"...) no lugar dos códigos de CAR e sem o CNPJ (princípio III). Os totais
do CNPJ já vão somados: a IA não calcula. Valores desconhecidos vão como texto ("indisponivel"...), nunca 0.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from app.schemas import OPEN_SITUACOES, CarDetail, CarIndicators, Status

MAX_PROPERTIES = 40
LEVEL_ORDER = {"bronze": 0, "silver": 1, "gold": 2, "sem_dados": 3}
SUPERSEDED = ("autorizada", "embargo_levantado", "suspensa_judicial")
# Números das próprias regras que o texto pode citar sem estarem nos dados.
RULE_NUMBERS = {2020.0, 31.0, 12.0, 24.0, 1.0, 0.1}
DETER_WINDOW_DAYS = 730

CarInput = tuple[str, CarDetail | None, CarIndicators | None, Status]

ALIAS_RE = re.compile(r"\bImóvel ([A-Z]{1,2})\b")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _r1(x: float | None) -> float | None:
    return None if x is None else round(float(x), 1)


def alias_for(i: int) -> str:
    letters = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        letters = chr(65 + rem) + letters
    return f"Imóvel {letters}"


def _source_state(ind: CarIndicators | None, name: str) -> str | None:
    """None se a fonte está ok; senão o estado ("indisponivel", "nao_se_aplica")."""
    if ind is None or name not in ind.sources:
        return "indisponivel"
    st = ind.sources[name].status  # type: ignore[index]
    return None if st == "ok" else st


def _alerts(ind: CarIndicators | None) -> dict[str, Any] | str:
    if _source_state(ind, "mapbiomas"):
        return "indisponivel"
    assert ind is not None
    by = ind.alerts_by_status
    opened = [by[k] for k in OPEN_SITUACOES if k in by]
    superseded = [by[k] for k in SUPERSEDED if k in by]
    years = sorted(a.detected_at.year for a in ind.alerts if a.detected_at)
    post = ind.open.post_2020
    return {
        "abertas": {"n": sum(c.n for c in opened), "ha": _r1(sum(c.ha for c in opened))},
        "superadas": {"n": sum(c.n for c in superseded), "ha": _r1(sum(c.ha for c in superseded))},
        "pos_2020": {"n": post.n, "ha": _r1(post.ha)} if post else None,
        "por_situacao": {k: {"n": c.n, "ha": _r1(c.ha)} for k, c in by.items() if c.n},
        "reserva_legal_ha": _r1(ind.open.legal_reserve_ha),
        "alertas_app": ind.open.app_alerts,
        "terra_indigena_ha": _r1(ind.open.indigenous_land_ha),
        "uc_integral_ha": _r1(ind.open.integral_protection_ha),
        "primeiro_ano": years[0] if years else None,
        "ultimo_ano": years[-1] if years else None,
    }


def _embargoes(detail: CarDetail | None) -> dict[str, Any]:
    if detail is None:
        return {"estado": "indisponivel"}
    s = detail.summary
    if s.embargoes_status != "ok":
        return {"estado": "indisponivel" if s.embargoes_status == "unavailable" else "nao_determinavel"}
    return {
        "estado": "verificado",
        "fonte": "IBAMA (cruzamento geográfico)" if s.embargoes_source == "ibama" else "MapBiomas",
        "vigentes": sum(1 for e in detail.embargoes if not e.expired_at),
        "levantados": sum(1 for e in detail.embargoes if e.expired_at),
        "copia_anterior": s.embargoes_stale or None,
    }


def _context(ind: CarIndicators | None, today: date) -> dict[str, Any]:
    if ind is None:
        return {"estado": "indisponivel"}
    c = ind.context
    out: dict[str, Any] = {}
    prodes = _source_state(ind, "prodes")
    out["vegetacao_nativa_pct"] = prodes or (_r1(c.native_vegetation.remaining_pct) if c.native_vegetation else None)
    out["desmatado_prodes_ha"] = None if prodes or not c.native_vegetation else _r1(c.native_vegetation.deforested_ha)
    deter = _source_state(ind, "deter")
    if deter:
        out["deter_24m"] = deter
    else:
        since = (today - timedelta(days=DETER_WINDOW_DAYS)).isoformat()
        out["deter_24m"] = {k: {"n": v.n, "ha": _r1(v.ha)} for k, v in (c.deter.by_class.items() if c.deter else [])
                            if v.last and v.last >= since}
    focos = _source_state(ind, "focos")
    out["focos_12m"] = focos or (c.hotspots_12m.count if c.hotspots_12m else None)
    sinaflor = _source_state(ind, "sinaflor")
    fm = c.forest_management
    out["manejo_sinaflor"] = sinaflor or ({"autorizacoes": fm.authorizations, "vigentes": fm.active,
                                           "volume_m3": _r1(fm.volume_m3)} if fm else None)
    out["uc_uso_sustentavel"] = c.sustainable_use_names
    return out


def _property(alias: str, code: str, detail: CarDetail | None, ind: CarIndicators | None, st: Status,
              today: date) -> dict[str, Any]:
    s = detail.summary if detail else None
    return {
        "id": alias,
        "uf": (s.state if s and s.state else code[:2]),
        "area_ha": _r1(s.area_ha) if s else None,
        "nivel": st.level,
        "motivos": [{"codigo": r.code, "n": r.n, "ha": _r1(r.ha), "pct": _r1(r.pct)} for r in st.reasons],
        "alertas": _alerts(ind) if detail else "indisponivel",
        "embargos": _embargoes(detail),
        "contexto": _context(ind, today) if detail else {"estado": "indisponivel"},
        "fontes_indisponiveis": sorted(k for k, v in (ind.sources.items() if ind else []) if v.status == "indisponivel"),
        "sinal_eudr": st.eudr_attention,
    }


def _totals(props: list[dict[str, Any]]) -> dict[str, Any]:
    def alert_sum(key: str) -> dict[str, Any]:
        items = [p["alertas"][key] for p in props if isinstance(p["alertas"], dict) and p["alertas"].get(key)]
        return {"n": sum(i["n"] for i in items), "ha": _r1(sum(i["ha"] or 0 for i in items))}

    emb = [p["embargos"] for p in props]
    focos = [p["contexto"].get("focos_12m") for p in props]
    return {
        "alertas_abertas": alert_sum("abertas"),
        "alertas_pos_2020": alert_sum("pos_2020"),
        "alertas_superadas": alert_sum("superadas"),
        "imoveis_com_alertas_abertas": sum(1 for p in props if isinstance(p["alertas"], dict)
                                           and p["alertas"]["abertas"]["n"]),
        "embargos_vigentes": sum(e.get("vigentes", 0) for e in emb if e["estado"] == "verificado"),
        "imoveis_com_embargo": sum(1 for e in emb if e.get("vigentes")),
        "imoveis_com_embargos_nao_verificados": sum(1 for e in emb if e["estado"] != "verificado"),
        "focos_12m": sum(f for f in focos if isinstance(f, int)),
    }


def build_report_facts(cars: list[CarInput], cnpj: Status, today: date) -> tuple[dict[str, Any], dict[str, str]]:
    """(dados para a IA, pseudônimo → código do CAR). Imóveis do mais grave ao menos grave, no máximo 40."""
    ordered = sorted(cars, key=lambda c: (LEVEL_ORDER[c[3].level], c[0]))[:MAX_PROPERTIES]
    aliases: dict[str, str] = {}
    props = []
    for i, (code, detail, ind, st) in enumerate(ordered):
        alias = alias_for(i)
        aliases[alias] = code
        props.append(_property(alias, code, detail, ind, st, today))
    facts = {
        "cnpj": {
            "nivel": cnpj.level,
            "motivos": [{"codigo": r.code, "imoveis": r.cars} for r in cnpj.reasons],
            "imoveis_por_nivel": cnpj.cars_by_level.model_dump() if cnpj.cars_by_level else None,
            "total_imoveis": len(cars),
            "imoveis_no_relatorio": len(ordered),
            "sinal_eudr": cnpj.eudr_attention,
            **_totals(props),
            "data_dos_dados": today.isoformat(),
        },
        "imoveis": props,
    }
    return facts, aliases


# --------------------------------------------------------------------------- #
# Controles do texto
# --------------------------------------------------------------------------- #
def allowed_numbers(facts: Any) -> set[float]:
    """Todos os números dos dados (com 1 decimal e inteiro arredondado) + os números das regras."""
    out = set(RULE_NUMBERS)

    def walk(v: Any) -> None:
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            out.add(round(float(v), 1))
            out.add(float(round(v)))
        elif isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            out.update(float(p) for p in v.split("-"))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(facts)
    return out


def _candidates(token: str) -> set[float]:
    """Leituras possíveis de um número escrito em pt-BR ("2.968,4", "376,1") ou com ponto decimal."""
    if "," in token:
        return {float(token.replace(".", "").replace(",", "."))}
    if "." in token:
        parts = token.split(".")
        reads = {float(token)} if len(parts) == 2 else set()
        if all(len(p) == 3 for p in parts[1:]):
            reads.add(float(token.replace(".", "")))
        return reads or {float(token.replace(".", ""))}
    return {float(token)}


def numbers_in_text(text: str) -> list[set[float]]:
    return [_candidates(t) for t in NUMBER_RE.findall(text)]


def invented_numbers(texts: list[str], allowed: set[float]) -> list[str]:
    """Números do texto que não estão nos dados (nenhuma leitura possível bate)."""
    bad = []
    for text in texts:
        for token in NUMBER_RE.findall(text):
            if not any(round(c, 1) in allowed for c in _candidates(token)):
                bad.append(token)
    return bad


# "imóveis A, B e D": pseudônimos abreviados que não dá para trocar pelos códigos reais.
ABBREVIATED_RE = re.compile(r"\bim[óo]veis\s+[A-Z]{1,2}(?:\s*,\s*[A-Z]{1,2})*\s+e\s+[A-Z]{1,2}\b", re.IGNORECASE)


def unknown_aliases(texts: list[str], aliases: dict[str, str]) -> set[str]:
    """Pseudônimos inexistentes, ou abreviados ("imóveis A, B e D"), que não podem ser trocados."""
    found = {f"Imóvel {m}" for t in texts for m in ALIAS_RE.findall(t)} - set(aliases)
    found |= {m.group(0) for t in texts for m in ABBREVIATED_RE.finditer(t)}
    return found


def _display_codes(aliases: dict[str, str]) -> dict[str, str]:
    """Pseudônimo → como aparece no texto: prefixo UF-município, ou o código completo se o prefixo se repete."""
    prefix = {a: "-".join(c.split("-")[:2]) for a, c in aliases.items()}
    counts: dict[str, int] = {}
    for p in prefix.values():
        counts[p] = counts.get(p, 0) + 1
    return {a: (p if counts[p] == 1 else aliases[a]) for a, p in prefix.items()}


def restore_aliases(text: str, aliases: dict[str, str]) -> str:
    shown = _display_codes(aliases)
    return ALIAS_RE.sub(lambda m: shown.get(m.group(0), m.group(0)), text)
