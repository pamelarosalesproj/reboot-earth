"""Serviço de Auditoria e Consultoria ESG com IA para análise mensal de Notas Fiscais x CARs.

Implementa as 4 regras de inteligência de conformidade:
1. De-para de Cobertura Documental: CARs totais do CNPJ vs. CARs evidenciados nas NFs.
2. Estouro Acumulado de Volume por CAR: Soma de várias NFs para o mesmo imóvel rural.
3. Detecção de 'CAR Coringa' / Sobrecarga: Concentração anômala de volume em um único imóvel (>80%).
4. Violação de Embargos: Emissão de NFs em imóveis com embargos ativos no MapBiomas.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import settings
from app.schemas_audit import (
    CarVolumeBalance,
    MonthlyAuditReportResponse,
    MonthlyInvoiceInput,
)

log = logging.getLogger("app.ai_auditor")

DEFAULT_AI_TIMEOUT_S = 10.0
AI_AUDITOR_PROMPT = """Você é um Consultor e Auditor Sênior Socioambiental/ESG especializado na cadeia florestal brasileira (SINAFLOR, DOF, CAR, MapBiomas Alerta e INPE).
Sua missão é emitir um parecer executivo de auditoria mensal cruzando Notas Fiscais (NFs) com o inventário cadastral de CARs do CNPJ auditado.

Diretrizes de Linguagem e Termos (Constituição do ELO Rural):
- Tom técnico, neutro, objetivo e baseado exclusivamente em dados documentais e cadastrais.
- Vocabulário obrigatório: utilize "sem autorização registrada" ou "sem comprovação documental", e NUNCA utilize termos sensacionalistas ou jurídicos conclusivos como "crime" ou "ilegal" no corpo explicativo.
- No campo "status": retorne "legal" para operações regulares/aptas, ou "ilegal" para operações irregulares/não aptas.

Regras Analíticas Mandatórias:
1. Status Geral ("legal" ou "ilegal"):
   - "ilegal" se:
     a) Houve estouro de cota volumétrica em qualquer CAR (soma das NFs superior à cota máxima autorizada SINAFLOR/capacidade).
     b) Houve emissão de NF em CAR com embargo ambiental ativo.
     c) Omissão severa de imóveis cadastrados ou concentração massiva (>80%) de volume em um único CAR ("CAR coringa").
   - "legal" se as operações respeitam as cotas de corte, sem embargos e com cobertura e rastreabilidade adequadas.
2. Cobertura Documental: Se o CNPJ possui mais CARs cadastrados do que os evidenciados nas NFs do mês, sinalize a falta de comprovação operacional dos imóveis não movimentados.
3. Risco de Sobrecarga ("CAR Coringa"): Se mais de 80% do volume faturado se concentrou em um único CAR com os demais inativos, alerte expressamente para o risco de canalização artificial de saldo florestal.
4. Idioma: Estritamente em português do Brasil (pt-BR).
5. Sugestões Práticas: OBRIGATORIAMENTE entre 3 e 5 sugestões construtivas e acionáveis para o produtor aprimorar sua governança ESG e regularidade florestal.

Responda OBRIGATORIAMENTE em JSON válido com exatamente esta estrutura:
{
  "status": "legal" ou "ilegal",
  "score": <número inteiro de 0 a 100>,
  "justification": "<texto detalhado em pt-BR>",
  "suggestions": [
    "<sugestão prática 1>",
    "<sugestão prática 2>",
    "<sugestão prática 3>"
  ]
}
    "<sugestão prática 1>",
    "<sugestão prática 2>",
    "<sugestão prática 3>"
  ]
}
"""


def _now_utc() -> datetime:
    return datetime.now(UTC)


def calculate_monthly_balances(
    registered_cars: list[dict[str, Any]],
    invoices: list[MonthlyInvoiceInput],
) -> tuple[list[CarVolumeBalance], list[str], float, int, int]:
    """Calcula a agregação de volume por CAR, cobertura e anomalias."""
    registered_codes = {c["car_code"] for c in registered_cars}
    invoices_by_car: dict[str, list[MonthlyInvoiceInput]] = {}
    missing_car_count = 0
    total_volume_all = 0.0

    for inv in invoices:
        total_volume_all += inv.volume_extracted_m3
        if not inv.car_code or not inv.car_code.strip():
            missing_car_count += 1
            continue
        code = inv.car_code.strip().upper()
        invoices_by_car.setdefault(code, []).append(inv)

    evidenced_codes = set(invoices_by_car.keys())
    omitted_codes = sorted(registered_codes - evidenced_codes)

    # Detalhe do balanço para cada CAR evidenciado
    car_info_map = {c["car_code"]: c for c in registered_cars}
    balances: list[CarVolumeBalance] = []

    for code, inv_list in invoices_by_car.items():
        car_info = car_info_map.get(code, {})
        area_ha = car_info.get("area_ha") or 30.0
        # Volume máximo permitido mensal estimado (ex: ~1.5 m³/ha/mês de manejo sustentável ou cota fixa)
        max_vol = car_info.get("max_volume_allowed_m3") or round(area_ha * 1.5, 2)
        car_vol_sum = sum(i.volume_extracted_m3 for i in inv_list)
        balance = round(max_vol - car_vol_sum, 2)
        is_exceeded = car_vol_sum > max_vol
        embargoes_count = car_info.get("embargoes_count") or 0
        alerts_count = car_info.get("alerts_count") or 0
        concentration = (
            round((car_vol_sum / total_volume_all) * 100, 1) if total_volume_all > 0 else 0.0
        )

        balances.append(
            CarVolumeBalance(
                car_code=code,
                invoices_count=len(inv_list),
                total_volume_invoices_m3=round(car_vol_sum, 2),
                max_volume_allowed_m3=max_vol,
                balance_m3=balance,
                is_exceeded=is_exceeded,
                has_embargoes=embargoes_count > 0,
                embargoes_count=embargoes_count,
                alerts_count=alerts_count,
                concentration_percentage=concentration,
            )
        )

    return (
        balances,
        omitted_codes,
        round(total_volume_all, 2),
        missing_car_count,
        len(evidenced_codes),
    )


def _build_deterministic_monthly_evaluation(
    total_cars: int,
    evidenced_cars: int,
    omitted_cars: list[str],
    balances: list[CarVolumeBalance],
    missing_car_nfs: int,
    has_concentration_anomaly: bool,
) -> tuple[str, int, list[str]]:
    """Gera o parecer determinístico de contingência caso o LLM esteja indisponível."""
    score = 100
    suggestions: list[str] = []

    # 1. Penalidade por CARs omitidos do CNPJ
    if omitted_cars:
        omission_penalty = min(25, len(omitted_cars) * 5)
        score -= omission_penalty
        suggestions.append(
            f"Vincular operações florestais aos {len(omitted_cars)} CARs cadastrados no CNPJ que não apresentaram NFs no período."
        )

    # 2. Penalidade por NFs sem CAR
    if missing_car_nfs > 0:
        score -= min(30, missing_car_nfs * 10)
        suggestions.append(
            "Incluir obrigatoriamente a identificação do CAR nos dados adicionais de todas as NF-e de madeira emitida."
        )

    # 3. Estouro de cota volumétrica por CAR
    exceeded_cars = [b for b in balances if b.is_exceeded]
    if exceeded_cars:
        score -= 40
        for b in exceeded_cars:
            suggestions.append(
                f"Adequar o volume faturado no CAR {b.car_code[:18]}... (extrapolou {abs(b.balance_m3):.2f} m³ da cota permitida)."
            )

    # 4. Violação de Embargos
    embargoed_cars = [b for b in balances if b.has_embargoes]
    if embargoed_cars:
        score -= 50
        suggestions.append(
            "Suspender imediatamente a comercialização de madeira vinculada a imóveis com embargos ambientais ativos."
        )

    # 5. Concentração anômala (CAR coringa)
    if has_concentration_anomaly:
        score -= 20
        suggestions.append(
            "Redistribuir o plano de extração entre os múltiplos imóveis do CNPJ para evitar sobrecarga de um único CAR."
        )

    default_suggestions = [
        "Implementar sistema integrado de conciliação de saldos DOF/Sinaflor antes da emissão da NF-e.",
        "Disponibilizar relatórios periódicos de custódia florestal aos compradores na plataforma ELO Rural.",
        "Buscar certificação florestal de cadeia de custódia para garantir transparência total aos compradores.",
    ]
    for s in default_suggestions:
        if len(suggestions) >= 5:
            break
        if s not in suggestions:
            suggestions.append(s)

    score = max(0, min(100, score))
    is_legal = (
        not exceeded_cars
        and not embargoed_cars
        and missing_car_nfs == 0
        and score >= 60
    )
    status = "legal" if is_legal else "ilegal"
    return status, score, suggestions[:5]


async def call_llm_api(
    prompt: str,
    system_instruction: str = AI_AUDITOR_PROMPT,
    timeout_s: float = DEFAULT_AI_TIMEOUT_S,
    api_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    key = api_key or os.getenv("LLM_API_KEY") or settings.llm_api_key
    if not key or key in ("", "mock-key", "sua_chave_api_do_llm_aqui"):
        return None

    endpoint = api_url or os.getenv("LLM_API_URL") or settings.llm_api_url

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": os.getenv("LLM_MODEL") or settings.llm_model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(endpoint, json=data, headers=headers)
            if resp.status_code != 200:
                log.warning("Falha na chamada ao LLM (status %s): %s", resp.status_code, resp.text[:200])
                return None
            body = resp.json()

            content = ""
            if body.get("choices"):
                content = body["choices"][0]["message"]["content"]
            elif body.get("candidates"):
                content = body["candidates"][0]["content"]["parts"][0]["text"]
            elif "response" in body:
                content = body["response"]
            else:
                content = json.dumps(body)

            cleaned = content.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            return json.loads(cleaned)
    except (httpx.TimeoutException, httpx.RequestError, json.JSONDecodeError, Exception) as err:  # noqa: BLE001
        log.warning("Exceção ao chamar LLM API: %s", str(err)[:200])
        return None


async def audit_monthly_report(
    cnpj: str,
    reference_period: str,
    registered_cars: list[dict[str, Any]],
    invoices: list[MonthlyInvoiceInput],
    timeout_s: float = DEFAULT_AI_TIMEOUT_S,
    llm_api_url: str | None = None,
    allow_fallback: bool = True,
) -> MonthlyAuditReportResponse:
    """Executa a auditoria mensal consolidada."""
    now = _now_utc()

    (
        balances,
        omitted_codes,
        total_vol,
        missing_car_nfs,
        evidenced_cars_count,
    ) = calculate_monthly_balances(registered_cars, invoices)

    total_cars = len(registered_cars)
    coverage_rate = (
        round((evidenced_cars_count / total_cars) * 100, 1) if total_cars > 0 else 0.0
    )

    has_volume_exceeded = any(b.is_exceeded for b in balances)
    has_embargo_violation = any(b.has_embargoes for b in balances)
    has_concentration_anomaly = any(b.concentration_percentage >= 80.0 for b in balances) and len(registered_cars) > 1

    payload_summary = {
        "cnpj": cnpj,
        "periodo_referencia": reference_period,
        "total_cars_cadastrados": total_cars,
        "total_cars_evidenciados": evidenced_cars_count,
        "taxa_cobertura_percentual": coverage_rate,
        "cars_omitidos_sem_nf": omitted_codes,
        "total_nfs_analisadas": len(invoices),
        "nfs_sem_car": missing_car_nfs,
        "volume_total_m3": total_vol,
        "balancos_por_car": [b.model_dump() for b in balances],
        "houve_estouro_volume": has_volume_exceeded,
        "houve_violacao_embargo": has_embargo_violation,
        "anomalia_concentracao_car_coringa": has_concentration_anomaly,
    }

    user_prompt = f"Analise o seguinte consolidado mensal de NFs e CARs:\n{json.dumps(payload_summary, ensure_ascii=False, indent=2)}"
    llm_result = await call_llm_api(user_prompt, timeout_s=timeout_s, api_url=llm_api_url)

    if llm_result:
        raw_status = str(llm_result.get("status", "")).lower().strip()
        status = "legal" if raw_status == "legal" else "ilegal"

        # Salvaguardas mandatórias de negócio
        if has_volume_exceeded or has_embargo_violation or (missing_car_nfs > len(invoices) * 0.3):
            status = "ilegal"

        score = llm_result.get("score")
        try:
            score = int(score) if score is not None else 65
            if (has_volume_exceeded or has_embargo_violation) and score > 50:
                score = 45
            score = max(0, min(100, score))
        except (ValueError, TypeError):
            score = 40 if (has_volume_exceeded or has_embargo_violation) else 75

        justification = llm_result.get("justification", "Auditoria mensal concluída com sucesso.")
        suggestions = llm_result.get("suggestions", [])
        if not isinstance(suggestions, list) or len(suggestions) < 3:
            _, _, default_suggs = _build_deterministic_monthly_evaluation(
                total_cars,
                evidenced_cars_count,
                omitted_codes,
                balances,
                missing_car_nfs,
                has_concentration_anomaly,
            )
            suggestions = default_suggs

        return MonthlyAuditReportResponse(
            status=status,
            score=score,
            cnpj=cnpj,
            reference_period=reference_period,
            total_cars_registered=total_cars,
            cars_evidenced_count=evidenced_cars_count,
            cars_omitted_count=len(omitted_codes),
            omitted_car_codes=omitted_codes,
            coverage_rate_percentage=coverage_rate,
            total_invoices_count=len(invoices),
            invoices_missing_car_count=missing_car_nfs,
            total_volume_extracted_m3=total_vol,
            car_balances=balances,
            has_volume_exceeded=has_volume_exceeded,
            has_embargo_violation=has_embargo_violation,
            has_concentration_anomaly=has_concentration_anomaly,
            justification=justification,
            suggestions=suggestions[:5],
            generated_at=now,
        )

    # Fallback
    if allow_fallback:
        det_status, det_score, det_suggestions = _build_deterministic_monthly_evaluation(
            total_cars,
            evidenced_cars_count,
            omitted_codes,
            balances,
            missing_car_nfs,
            has_concentration_anomaly,
        )

        parts = [
            f"Relatório de auditoria mensal ({reference_period}) processado via motor analítico ESG."
        ]
        if omitted_codes:
            parts.append(
                f"Atenção à transparência: de {total_cars} CARs registrados para este CNPJ, "
                f"{len(omitted_codes)} não foram evidenciados em nenhuma Nota Fiscal emitida no mês."
            )
        if has_volume_exceeded:
            parts.append(
                "Inconformidade crítica: Um ou mais imóveis rurais tiveram seu volume máximo de corte extrapolado pela soma das NFs."
            )
        if has_concentration_anomaly:
            parts.append(
                "Alerta de concentração: Mais de 80% de todo o volume faturado se concentrou em um único CAR ('CAR coringa')."
            )

        return MonthlyAuditReportResponse(
            status=det_status,
            score=det_score,
            cnpj=cnpj,
            reference_period=reference_period,
            total_cars_registered=total_cars,
            cars_evidenced_count=evidenced_cars_count,
            cars_omitted_count=len(omitted_codes),
            omitted_car_codes=omitted_codes,
            coverage_rate_percentage=coverage_rate,
            total_invoices_count=len(invoices),
            invoices_missing_car_count=missing_car_nfs,
            total_volume_extracted_m3=total_vol,
            car_balances=balances,
            has_volume_exceeded=has_volume_exceeded,
            has_embargo_violation=has_embargo_violation,
            has_concentration_anomaly=has_concentration_anomaly,
            justification=" ".join(parts),
            suggestions=det_suggestions,
            generated_at=now,
        )

    return MonthlyAuditReportResponse(
        status="indisponivel",
        score=None,
        cnpj=cnpj,
        reference_period=reference_period,
        total_cars_registered=total_cars,
        cars_evidenced_count=evidenced_cars_count,
        cars_omitted_count=len(omitted_codes),
        omitted_car_codes=omitted_codes,
        coverage_rate_percentage=coverage_rate,
        total_invoices_count=len(invoices),
        invoices_missing_car_count=missing_car_nfs,
        total_volume_extracted_m3=total_vol,
        car_balances=balances,
        has_volume_exceeded=has_volume_exceeded,
        has_embargo_violation=has_embargo_violation,
        has_concentration_anomaly=has_concentration_anomaly,
        justification="Serviço de IA indisponível temporariamente.",
        suggestions=[],
        generated_at=now,
    )
