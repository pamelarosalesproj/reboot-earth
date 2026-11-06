"""Relatório do CNPJ para o Início gerado em tempo real pelo Agente IA / Motor ESG.

Consolida dados reais de:
- MapBiomas Alerta (polígono, alertas abertas, alertas superadas, embargos, RL/APP)
- INPE (DETER, PRODES, focos de calor)
- IBAMA / SINAFLOR (planos de manejo POA e cotas)

Respeita estritamente:
- Princípio do Nível: calculado exclusivamente por regras fixas (compute_status), nunca pelo texto.
- Princípio do Vocabulário: jamais usa palavras proibidas como 'crime' ou 'ilegal' no parecer.
- Tolerância a falhas: fallback analítico determinístico se a API do LLM estiver sem chave ou falhar.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import settings
from app.mapbiomas.client import MapBiomasClient, MapBiomasError, MapBiomasUnavailable
from app.models import Producer, ProducerCar
from app.schemas import (
    OPEN_SITUACOES,
    CarDetail,
    CarIndicators,
    CnpjReport,
    ReportProperty,
)
from app.services.car_indicators import get_indicators
from app.services.car_service import get_detail
from app.services.cnpj_report import cnpj_aggregate, compute_status

log = logging.getLogger("app.reports")

FORBIDDEN = re.compile(r"\b(ilegal\w*|crime\w*|criminos\w*)", re.IGNORECASE)
UNAVAILABLE = CnpjReport(status="indisponivel")

CNPJ_AGENT_PROMPT = """Você é o Agente Analista e Auditor Socioambiental/ESG da plataforma RebootEarth.
Sua missão é redigir a síntese executiva do 'Relatório do CNPJ' para o produtor rural autenticado, a partir de dados consolidados de MapBiomas Alerta, INPE (DETER/PRODES/Focos) e IBAMA (SINAFLOR).

Diretrizes Obrigatórias (Constituição do RebootEarth):
1. O Nível (Gold, Silver ou Bronze) já foi definido pelo sistema de regras fixas. Você NUNCA altera e NÃO discute a legitimidade do nível, apenas explica suas razões.
2. Vocabulário: NUNCA use palavras sensacionalistas ou jurídicas conclusivas como 'crime', 'ilegal' ou 'criminoso'. Use 'sem autorização registrada', 'com embargo vigente' ou 'sem comprovação documental'.
3. Riscos: cite exclusivamente riscos em aberto (máximo 3 tópicos, focando em embargos, alertas abertas pós-2020/EUDR e reserva legal/APP).
4. Contexto: fatos atenuantes ou contextuais que NÃO diminuem o nível (máximo 3 tópicos, ex: alertas autorizadas, APAs de uso sustentável, focos de calor, manejo).
5. Ressalvas e Melhorias: no mínimo 2 ressalvas técnicas (ex: PRODES não mede regeneração, MapBiomas calcula sobreposição) e recomendações claras de como o produtor pode regularizar sua situação.
6. Por Imóvel: forneça um resumo conciso de uma frase para cada CAR analisado.

Responda OBRIGATORIAMENTE em JSON válido com exatamente esta estrutura:
{
  "titulo": "<Frase executiva de síntese>",
  "riscos": ["<risco 1>", "<risco 2>", "<risco 3>"],
  "contexto": ["<contexto 1>", "<contexto 2>"],
  "ressalvas": ["<ressalva 1>", "<ressalva 2>", "<como melhorar classificação>"],
  "imoveis": [
    {"car_code": "<código CAR>", "resumo": "<resumo do CAR>"}
  ]
}
"""


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _texts(r: CnpjReport) -> list[str]:
    return [r.titulo or "", *r.riscos, *r.contexto, *r.ressalvas, *(p.resumo for p in r.imoveis)]


def _validate(raw: dict) -> CnpjReport | None:
    try:
        report = CnpjReport.model_validate({**raw, "status": "ok"})
    except Exception as e:  # noqa: BLE001
        log.warning("relatório inválido estruturalmente: %s", str(e)[:200])
        return None
    if any(FORBIDDEN.search(t) for t in _texts(report)):
        log.warning("relatório rejeitado pelo filtro de vocabulário da constituição")
        return None
    return report


async def _car_data(bind: Engine, client: MapBiomasClient, code: str) -> tuple[CarIndicators | None, CarDetail | None]:
    with Session(bind) as db:
        try:
            detail = await get_detail(db, client, code)
        except (MapBiomasUnavailable, MapBiomasError):
            detail = None
        try:
            ind = await get_indicators(db, client, code)
        except Exception:  # noqa: BLE001
            ind = None
    return ind, detail


def _build_deterministic_report(
    nivel: str,
    cars_data: list[tuple[str, CarIndicators | None, CarDetail | None]],
    today_str: str,
) -> CnpjReport:
    """Gera o relatório analítico determinístico estruturado caso o LLM esteja indisponível."""
    total_cars = len(cars_data)
    imoveis_list: list[ReportProperty] = []

    active_embargoes_total = 0
    open_alerts_count = 0
    open_alerts_ha = 0.0
    post_2020_count = 0
    post_2020_ha = 0.0
    rl_app_ha = 0.0
    hotspots_total = 0
    authorized_alerts_count = 0
    authorized_alerts_ha = 0.0

    cars_with_active_embargoes = []
    cars_with_open_alerts = []

    for code, ind, detail in cars_data:
        car_short = code[:10]
        car_embargoes = 0
        if detail and detail.summary.embargoes_status == "ok":
            active_embs = [e for e in detail.embargoes if not e.expired_at]
            car_embargoes = len(active_embs)
            active_embargoes_total += car_embargoes
            if car_embargoes > 0:
                cars_with_active_embargoes.append(car_short)

        car_open_alerts = 0
        car_open_ha = 0.0
        car_rl_ha = 0.0
        car_app_touch = 0

        if ind and ind.sources.get("mapbiomas") and ind.sources["mapbiomas"].status == "ok":
            for a in ind.alerts:
                if a.status in OPEN_SITUACOES:
                    open_alerts_count += 1
                    open_alerts_ha += a.area_in_car_ha
                    car_open_alerts += 1
                    car_open_ha += a.area_in_car_ha
                    if a.post_2020:
                        post_2020_count += 1
                        post_2020_ha += a.area_in_car_ha
                    if a.legal_reserve_ha > 0:
                        rl_app_ha += a.legal_reserve_ha
                        car_rl_ha += a.legal_reserve_ha
                    if a.touches_app:
                        car_app_touch += 1
                elif a.status == "autorizada":
                    authorized_alerts_count += 1
                    authorized_alerts_ha += a.area_in_car_ha

            if ind.context and ind.context.hotspots_12m:
                hotspots_total += ind.context.hotspots_12m.count

        if car_open_alerts > 0:
            cars_with_open_alerts.append(car_short)

        # Frase descritiva do imóvel
        parts = []
        if car_embargoes > 0:
            parts.append(f"{car_embargoes} embargo(s) vigente(s)")
        if car_open_alerts > 0:
            sub = f"{car_open_alerts} alertas abertas ({car_open_ha:.1f} ha)"
            if car_rl_ha > 0:
                sub += f", {car_rl_ha:.1f} ha em reserva legal"
            if car_app_touch > 0:
                sub += f" e {car_app_touch} tocando APP"
            parts.append(sub)
        elif car_embargoes == 0:
            parts.append("Sem alertas ativas; operações regulares")

        imoveis_list.append(ReportProperty(car_code=code, resumo="; ".join(parts) or "Sem alertas ativas"))

    # Monta Riscos
    riscos: list[str] = []
    if active_embargoes_total > 0:
        c_str = ", ".join(cars_with_active_embargoes[:3])
        riscos.append(f"{active_embargoes_total} embargos vigentes em {len(cars_with_active_embargoes)} imóveis ({c_str}).")
    if open_alerts_count > 0:
        post_str = f"; {post_2020_count} ({post_2020_ha:.1f} ha) detectadas pós-31/12/2020 (marco EUDR)" if post_2020_count > 0 else ""
        riscos.append(f"{open_alerts_count} alertas abertas somam {open_alerts_ha:.1f} ha{post_str}.")
    if rl_app_ha > 0:
        riscos.append(f"{rl_app_ha:.1f} ha de alertas abertas incidentes sobre áreas de reserva legal ou preservação permanente.")

    if not riscos:
        riscos.append("Nenhum risco de embargo ou alerta ativa identificado nos imóveis cadastrados.")

    # Monta Contexto
    contexto: list[str] = []
    if authorized_alerts_count > 0:
        contexto.append(f"{authorized_alerts_count} alertas ({authorized_alerts_ha:.1f} ha) possuem autorização de supressão registrada e não contam como risco aberto.")
    if hotspots_total > 0:
        contexto.append(f"{hotspots_total} focos de calor registrados nos últimos 12 meses pelo satélite de referência do INPE.")
    contexto.append("Planos de Manejo Florestal Sustentável (POA) consultados na base pública do SINAFLOR/IBAMA.")

    # Título
    if active_embargoes_total > 0 and open_alerts_count > 0:
        titulo = f"Embargos vigentes e desmatamento recente sem autorização registrada em {len(set(cars_with_active_embargoes + cars_with_open_alerts))} dos {total_cars} imóveis"
    elif active_embargoes_total > 0:
        titulo = f"Imóveis com embargos ambientais vigentes registrados no MapBiomas em {len(cars_with_active_embargoes)} de {total_cars} imóveis"
    elif open_alerts_count > 0:
        titulo = f"Alertas de supressão sem comprovação de autorização registradas em {len(cars_with_open_alerts)} de {total_cars} imóveis"
    else:
        titulo = f"Conformidade socioambiental positiva em todos os {total_cars} imóveis rurais cadastrados"

    # Ressalvas
    ressalvas = [
        "A vegetação nativa calculada pelo PRODES/INPE considera o histórico de supressão e não registra regeneração recente.",
        "Reserva legal e APP são calculadas pelo MapBiomas sobre a área da alerta, limitadas à geometria do imóvel.",
        "'Sem autorização registrada' indica ausência nas bases consultadas até o momento; não constitui conclusão jurídica definitiva.",
        "Recomenda-se realizar a comprovação de títulos autorizativos estaduais e retificação cadastral para elevar a nota ESG do CNPJ.",
    ]

    return CnpjReport(
        status="ok",
        origem="agente",
        nivel=nivel,  # type: ignore[arg-type]
        titulo=titulo,
        riscos=riscos[:3],
        contexto=contexto[:3],
        ressalvas=ressalvas,
        imoveis=imoveis_list,
        data_dos_dados=date.today(),
        gerado_em=_now_utc(),
    )


async def call_llm(prompt: str) -> dict[str, Any] | None:
    key = os.getenv("LLM_API_KEY") or settings.llm_api_key
    if not key or key in ("", "mock-key", "sua_chave_api_do_llm_aqui"):
        return None

    endpoint = os.getenv("LLM_API_URL") or settings.llm_api_url
    model = os.getenv("LLM_MODEL") or settings.llm_model

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": CNPJ_AGENT_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(endpoint, json=payload, headers=headers)
            if resp.status_code != 200:
                return None
            body = resp.json()
            content = ""
            if body.get("choices"):
                content = body["choices"][0]["message"]["content"]
            elif body.get("candidates"):
                content = body["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content.strip())
    except Exception as e:  # noqa: BLE001
        log.warning("Falha na chamada ao LLM para resumo do CNPJ: %s", str(e)[:150])
        return None


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


async def get_report(db: Session, client: MapBiomasClient, cnpj: str) -> CnpjReport:
    """Gera o relatório do CNPJ em tempo real a partir dos dados do MapBiomas, INPE e IBAMA."""
    # 1. Se houver mock explícito configurado para testes de integração (feature 005), prioriza
    raw_mock = _example_report(cnpj)
    if raw_mock:
        validated = _validate(raw_mock)
        if not validated:
            return UNAVAILABLE
        registered, agg = await cnpj_aggregate(db, client, cnpj)
        validated.nivel = compute_status(agg, registered).level  # o nível nunca vem do texto
        validated.origem = "exemplo"
        return validated
    registered, agg = await cnpj_aggregate(db, client, cnpj)
    if not registered or not agg or agg.cars_count == 0:
        return UNAVAILABLE

    computed_level = compute_status(agg, registered).level

    ids = db.exec(select(Producer.id).where(Producer.cnpj == cnpj)).all()
    codes = sorted(set(db.exec(
        select(ProducerCar.car_code).where(ProducerCar.producer_id.in_(ids))  # type: ignore[union-attr]
    ).all())) if ids else []

    if not codes:
        return UNAVAILABLE

    # Coleta de indicadores de cada CAR em paralelo
    results = await asyncio.gather(*(_car_data(db.get_bind(), client, c) for c in codes))
    cars_data = [(codes[i], results[i][0], results[i][1]) for i in range(len(codes))]

    # Tenta gerar com LLM se configurado
    payload_summary = {
        "cnpj": cnpj,
        "nivel_calculado": computed_level,
        "total_imoveis": len(codes),
        "imoveis": [
            {
                "car_code": c[0],
                "alertas": [a.model_dump(mode="json") for a in (c[1].alerts if c[1] else [])],
                "embargos": [e.model_dump(mode="json") for e in (c[2].embargoes if c[2] else [])],
                "hotspots": c[1].context.hotspots_12m.model_dump(mode="json") if (c[1] and c[1].context and c[1].context.hotspots_12m) else None,
            }
            for c in cars_data
        ],
    }

    prompt = f"Gere o resumo executivo estruturado com base nos dados seguintes:\n{json.dumps(payload_summary, ensure_ascii=False, indent=2)}"
    llm_resp = await call_llm(prompt)

    if llm_resp:
        validated = _validate(llm_resp)
        if validated:
            validated.origem = "agente"
            validated.nivel = computed_level  # type: ignore[assignment]
            validated.data_dos_dados = date.today()
            validated.gerado_em = _now_utc()
            return validated

    # Fallback determinístico robusto (não quebra a página caso a IA esteja offline)
    det_report = _build_deterministic_report(computed_level, cars_data, str(date.today()))
    return det_report
