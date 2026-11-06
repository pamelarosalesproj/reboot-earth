"""Relatório do CNPJ para o Início (feature 005).

HOJE: o relatório é um **exemplo escrito à mão** (gerado por Claude numa conversa a partir dos
indicadores reais), lido de `settings.mock_reports_dir/<cnpj>.json`. Essa pasta fica FORA do
repositório (`backend/data/` é ignorado) porque associa códigos de CAR reais a um CNPJ.

PONTO DE INTEGRAÇÃO DO AGENTE: substituir `_example_report()` pela geração real (ver
docs/proposta-regras-nivel-e-agente.md). Manter: o formato `CnpjReport`, `_validate()` e a regra de
que `nivel` é sempre o calculado por `compute_status` — o texto nunca decide o nível.
"""

import json
import logging
import re
from pathlib import Path

from pydantic import ValidationError
from sqlmodel import Session

from app.config import settings
from app.mapbiomas.client import MapBiomasClient
from app.schemas import CnpjReport
from app.services.cnpj_report import cnpj_aggregate, compute_status

log = logging.getLogger("app.reports")

FORBIDDEN = re.compile(r"\b(ilegal\w*|crime\w*|criminos\w*)", re.IGNORECASE)
UNAVAILABLE = CnpjReport(status="indisponivel")


def _example_report(cnpj: str) -> dict | None:
    path = Path(settings.mock_reports_dir) / f"{cnpj}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _texts(r: CnpjReport) -> list[str]:
    return [r.titulo or "", *r.riscos, *r.contexto, *r.ressalvas, *(p.resumo for p in r.imoveis)]


def _validate(raw: dict) -> CnpjReport | None:
    try:
        report = CnpjReport.model_validate({**raw, "status": "ok"})
    except ValidationError as e:
        log.warning("relatório inválido: %s", str(e)[:200])
        return None
    if any(FORBIDDEN.search(t) for t in _texts(report)):
        log.warning("relatório rejeitado: vocabulário proibido")
        return None
    return report


async def get_report(db: Session, client: MapBiomasClient, cnpj: str) -> CnpjReport:
    try:
        raw = _example_report(cnpj)
    except (OSError, ValueError) as e:
        log.warning("relatório de exemplo ilegível para o CNPJ: %s", type(e).__name__)
        return UNAVAILABLE
    if not raw or not (report := _validate(raw)):
        return UNAVAILABLE
    registered, agg = await cnpj_aggregate(db, client, cnpj)
    report.nivel = compute_status(agg, registered).level  # o nível nunca vem do texto
    report.origem = "exemplo"
    return report
