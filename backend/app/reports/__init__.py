"""Relatório do CNPJ para o Início (features 005 e 008).

A IA só consolida e explica os dados que o sistema já calculou (feature 008):
- entrada = `build_report_facts` (nível e motivos, indicadores e embargos de cada CAR; totais do CNPJ), com
  pseudônimos ("Imóvel A"...) no lugar dos códigos de CAR e sem o CNPJ;
- a resposta é validada (formato, até 3 riscos/contexto, vocabulário, números presentes nos dados,
  pseudônimos existentes); um retry; se falhar, texto por regras (`origem="regras"`);
- o nível vem sempre das regras (feature 006), nunca do texto;
- cache em memória por conteúdo: a IA só é chamada de novo quando os dados mudam.
O exemplo escrito à mão (`MOCK_REPORTS_DIR/<cnpj>.json`) só é usado com `REPORT_DEMO_MODE=true`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections import OrderedDict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlmodel import Session

from app.config import settings
from app.mapbiomas.client import MapBiomasClient
from app.reports.facts import (
    CarInput,
    allowed_numbers,
    build_report_facts,
    invented_numbers,
    restore_aliases,
    unknown_aliases,
)
from app.reports.prompt import PROMPT_VERSION, SYSTEM_PROMPT
from app.schemas import OPEN_SITUACOES, CarDetail, CarIndicators, CnpjReport, ReportProperty
from app.services.cnpj_report import car_inputs, cnpj_codes
from app.services.level_rules import car_level, cnpj_level

log = logging.getLogger("app.reports")

FORBIDDEN = re.compile(r"\b(ilegal\w*|crime\w*|criminos\w*)", re.IGNORECASE)
UNAVAILABLE = CnpjReport(status="indisponivel")
PLACEHOLDER_KEYS = ("", "mock-key", "sua_chave_api_do_llm_aqui")
RULES_CACHE_S = 15 * 60
CACHE_MAX = 256

# hash dos dados → (relatório, expira_em | None)
_cache: OrderedDict[str, tuple[CnpjReport, float | None]] = OrderedDict()


def clear_report_cache() -> None:
    _cache.clear()


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _texts(r: CnpjReport) -> list[str]:
    return [r.titulo or "", *r.riscos, *r.contexto, *r.ressalvas, *(p.resumo for p in r.imoveis)]


def _validate(raw: dict) -> CnpjReport | None:
    """Validação estrita do exemplo escrito à mão (formato e vocabulário)."""
    try:
        report = CnpjReport.model_validate({**raw, "status": "ok"})
    except Exception as e:  # noqa: BLE001
        log.warning("relatório inválido estruturalmente: %s", str(e)[:200])
        return None
    if any(FORBIDDEN.search(t) for t in _texts(report)):
        log.warning("relatório rejeitado pelo filtro de vocabulário da constituição")
        return None
    return report


# --------------------------------------------------------------------------- #
# Texto por regras (sem IA)
# --------------------------------------------------------------------------- #
def _car_sentence(ind: CarIndicators | None, detail: CarDetail | None) -> tuple[str, dict[str, Any]]:
    """Frase de um imóvel e seus números (usados também nos totais)."""
    n = {"emb": 0, "open": 0, "open_ha": 0.0, "post": 0, "post_ha": 0.0, "rl_ha": 0.0, "app": 0,
         "auth": 0, "auth_ha": 0.0, "focos": 0, "emb_known": False}
    if detail and detail.summary.embargoes_status == "ok":
        n["emb_known"] = True
        n["emb"] = sum(1 for e in detail.embargoes if not e.expired_at)
    if ind and ind.sources.get("mapbiomas") and ind.sources["mapbiomas"].status == "ok":
        for a in ind.alerts:
            if a.status in OPEN_SITUACOES:
                n["open"] += 1
                n["open_ha"] += a.area_in_car_ha
                if a.post_2020:
                    n["post"] += 1
                    n["post_ha"] += a.area_in_car_ha
                n["rl_ha"] += a.legal_reserve_ha
                n["app"] += 1 if a.touches_app else 0
            elif a.status == "autorizada":
                n["auth"] += 1
                n["auth_ha"] += a.area_in_car_ha
        if ind.context and ind.context.hotspots_12m:
            n["focos"] = ind.context.hotspots_12m.count
    parts = []
    if n["emb"]:
        parts.append(f"{n['emb']} embargo(s) vigente(s)")
    if n["open"]:
        sub = f"{n['open']} alertas em aberto ({n['open_ha']:.1f} ha)"
        if n["rl_ha"] > 0:
            sub += f", {n['rl_ha']:.1f} ha em reserva legal"
        if n["app"]:
            sub += f" e {n['app']} tocando APP"
        parts.append(sub)
    if not detail:
        parts.append("Dados do MapBiomas indisponíveis no momento")
    elif not n["emb_known"]:
        parts.append("embargos não puderam ser verificados")
    if not parts:
        parts.append("Sem alertas em aberto nem embargos vigentes")
    return "; ".join(parts), n


def _build_deterministic_report(nivel: str, cars_data: list[tuple[str, CarIndicators | None, CarDetail | None]],
                                today_str: str) -> CnpjReport:
    """Relatório montado por regras quando a IA não está disponível ou não passou nos controles."""
    total = len(cars_data)
    imoveis: list[ReportProperty] = []
    tot = {"emb": 0, "open": 0, "open_ha": 0.0, "post": 0, "post_ha": 0.0, "rl_ha": 0.0, "auth": 0,
           "auth_ha": 0.0, "focos": 0}
    with_emb: list[str] = []
    with_open: list[str] = []
    for code, ind, detail in cars_data:
        sentence, n = _car_sentence(ind, detail)
        imoveis.append(ReportProperty(car_code=code, resumo=sentence))
        for k in tot:
            tot[k] += n[k]
        short = "-".join(code.split("-")[:2])
        if n["emb"]:
            with_emb.append(short)
        if n["open"]:
            with_open.append(short)

    riscos: list[str] = []
    if tot["emb"]:
        riscos.append(f"{tot['emb']} embargos vigentes em {len(with_emb)} imóveis ({', '.join(with_emb[:3])}).")
    if tot["open"]:
        post = (f"; {tot['post']} ({tot['post_ha']:.1f} ha) detectadas depois de 31/12/2020, a data de corte da EUDR"
                if tot["post"] else "")
        riscos.append(f"{tot['open']} alertas em aberto somam {tot['open_ha']:.1f} ha{post}.")
    if tot["rl_ha"] > 0:
        riscos.append(f"{tot['rl_ha']:.1f} ha de alertas em aberto em reserva legal.")
    if not riscos:
        riscos.append("Nenhum embargo vigente nem alerta em aberto nos imóveis cadastrados.")

    contexto: list[str] = []
    if tot["auth"]:
        contexto.append(f"{tot['auth']} alertas ({tot['auth_ha']:.1f} ha) têm autorização registrada e não contam "
                        "como risco aberto.")
    if tot["focos"]:
        contexto.append(f"{tot['focos']} focos de calor nos últimos 12 meses (INPE).")

    affected = len(set(with_emb + with_open))
    if tot["emb"] and tot["open"]:
        titulo = f"Embargos vigentes e alertas sem autorização registrada em {affected} dos {total} imóveis"
    elif tot["emb"]:
        titulo = f"Embargos vigentes em {len(with_emb)} dos {total} imóveis"
    elif tot["open"]:
        titulo = f"Alertas sem autorização registrada em {len(with_open)} dos {total} imóveis"
    else:
        titulo = f"Nenhum risco em aberto nos {total} imóveis"

    ressalvas = [
        "A vegetação nativa do PRODES (INPE) considera o histórico de desmatamento e não registra regeneração.",
        "Reserva legal e APP são calculadas pelo MapBiomas sobre a área da alerta, limitadas à área do imóvel.",
        ("\"Sem autorização registrada\" indica ausência de registro nas bases consultadas; não é uma conclusão "
         "jurídica."),
    ]
    return CnpjReport(
        status="ok", origem="regras", nivel=nivel,  # type: ignore[arg-type]
        titulo=titulo, riscos=riscos[:3], contexto=contexto[:3], ressalvas=ressalvas, imoveis=imoveis,
        data_dos_dados=date.fromisoformat(today_str), gerado_em=_now_utc(),
    )


# --------------------------------------------------------------------------- #
# IA
# --------------------------------------------------------------------------- #
def _llm_key() -> str | None:
    key = settings.llm_api_key
    return None if key in PLACEHOLDER_KEYS else key


async def call_llm(facts: dict[str, Any]) -> dict[str, Any] | None:
    """Uma chamada à API compatível com a da OpenAI. None se não há chave, se falha ou se não é JSON."""
    key = _llm_key()
    if not key:
        return None
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as http:
            resp = await http.post(settings.llm_api_url, json=payload,
                                   headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        if resp.status_code != 200:
            log.warning("LLM respondeu HTTP %s", resp.status_code)
            return None
        body = resp.json()
        if body.get("choices"):
            content = body["choices"][0]["message"]["content"]
        else:
            content = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(content.strip())
        return data if isinstance(data, dict) else None
    except Exception as e:  # noqa: BLE001 — qualquer falha cai no texto por regras
        log.warning("falha na chamada ao LLM: %s", type(e).__name__)
        return None


def _validate_llm(raw: dict[str, Any], facts: dict[str, Any], aliases: dict[str, str],
                  sentences: dict[str, str]) -> CnpjReport | None:
    """Controles da resposta da IA (FR-805). Devolve o relatório com os códigos reais, ou None."""
    try:
        props = [{"id": str(p["id"]), "resumo": str(p["resumo"])} for p in raw.get("imoveis") or []]
        titulo = str(raw.get("titulo") or "").strip()
        riscos = [str(x) for x in raw.get("riscos") or []][:3]
        contexto = [str(x) for x in raw.get("contexto") or []][:3]
        ressalvas = [str(x) for x in raw.get("ressalvas") or []]
    except (TypeError, KeyError, AttributeError) as e:
        log.warning("resposta da IA fora do formato: %s", type(e).__name__)
        return None
    if not titulo:
        log.warning("resposta da IA sem título")
        return None
    texts = [titulo, *riscos, *contexto, *ressalvas, *(p["resumo"] for p in props)]
    if any(FORBIDDEN.search(t) for t in texts):
        log.warning("resposta da IA com vocabulário proibido")
        return None
    unknown = unknown_aliases(texts + [p["id"] for p in props], aliases)
    if unknown:
        log.warning("resposta da IA cita imóveis inexistentes: %s", sorted(unknown))
        return None
    bad = invented_numbers(texts, allowed_numbers(facts))
    if bad:
        log.warning("resposta da IA com números ausentes dos dados: %s", bad[:5])
        return None
    by_alias = {p["id"]: p["resumo"] for p in props}
    imoveis = [ReportProperty(car_code=code,
                              resumo=restore_aliases(by_alias[a], aliases) if a in by_alias else sentences[code])
               for a, code in aliases.items()]
    # Imóveis além do limite enviado à IA recebem a frase por regras.
    imoveis += [ReportProperty(car_code=c, resumo=s) for c, s in sentences.items() if c not in aliases.values()]
    return CnpjReport(
        status="ok", origem="agente",
        titulo=restore_aliases(titulo, aliases),
        riscos=[restore_aliases(t, aliases) for t in riscos],
        contexto=[restore_aliases(t, aliases) for t in contexto],
        ressalvas=[restore_aliases(t, aliases) for t in ressalvas],
        imoveis=imoveis,
    )


# --------------------------------------------------------------------------- #
# Orquestração
# --------------------------------------------------------------------------- #
def _example_report(cnpj: str) -> dict | None:
    if not settings.mock_reports_dir:
        return None
    path = Path(settings.mock_reports_dir) / f"{cnpj}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _cache_key(facts: dict[str, Any]) -> str:
    raw = json.dumps(facts, sort_keys=True, ensure_ascii=False) + PROMPT_VERSION + settings.llm_model
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> CnpjReport | None:
    hit = _cache.get(key)
    if not hit:
        return None
    report, expires = hit
    if expires is not None and time.monotonic() > expires:
        del _cache[key]
        return None
    _cache.move_to_end(key)
    return report


def _cache_put(key: str, report: CnpjReport) -> None:
    _cache[key] = (report, None if report.origem == "agente" else time.monotonic() + RULES_CACHE_S)
    _cache.move_to_end(key)
    while len(_cache) > CACHE_MAX:
        _cache.popitem(last=False)


def _set_property_levels(report: CnpjReport, levels: dict[str, str]) -> None:
    """Nível de cada imóvel pelas regras (coluna "Nível" do relatório); nunca do texto."""
    for p in report.imoveis:
        p.nivel = levels.get(p.car_code)  # type: ignore[assignment]


async def get_report(db: Session, client: MapBiomasClient, cnpj: str) -> CnpjReport:
    today = date.today()
    registered, codes = cnpj_codes(db, cnpj)

    if settings.report_demo_mode and (raw := _example_report(cnpj)):
        validated = _validate(raw)
        if not validated:
            return UNAVAILABLE
        inputs = await car_inputs(db, client, codes)
        statuses = [car_level(d, i, today) for d, i in inputs]
        validated.nivel = cnpj_level(statuses, registered).level
        validated.origem = "exemplo"
        _set_property_levels(validated, {c: st.level for c, st in zip(codes, statuses, strict=True)})
        return validated

    if not registered or not codes:
        return UNAVAILABLE

    inputs = await car_inputs(db, client, codes)
    statuses = [car_level(d, i, today) for d, i in inputs]
    cnpj_st = cnpj_level(statuses, registered)
    cars: list[CarInput] = [(code, d, i, s) for code, (d, i), s in zip(codes, inputs, statuses, strict=True)]
    facts, aliases = build_report_facts(cars, cnpj_st, today)

    key = _cache_key(facts)
    if cached := _cache_get(key):
        return cached

    sentences = {code: _car_sentence(i, d)[0] for code, (d, i) in zip(codes, inputs, strict=True)}
    report: CnpjReport | None = None
    if _llm_key():
        for _ in range(2):  # uma tentativa + um retry
            raw = await call_llm(facts)
            if raw is None:
                break  # sem resposta (erro/timeout): não insiste
            report = _validate_llm(raw, facts, aliases, sentences)
            if report:
                break
    if report is None:
        report = _build_deterministic_report(cnpj_st.level, [(c, i, d) for c, (d, i) in zip(codes, inputs, strict=True)],
                                             today.isoformat())
    report.nivel = cnpj_st.level  # type: ignore[assignment]
    _set_property_levels(report, {c: st.level for c, st in zip(codes, statuses, strict=True)})
    report.data_dos_dados = today
    report.gerado_em = report.gerado_em or _now_utc()
    _cache_put(key, report)
    return report
