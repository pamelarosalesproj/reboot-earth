"""Serviço de Auditoria e Consultoria ESG com IA para cruzamento NF x CAR/MapBiomas.

Segue as diretrizes de AGENTS.md e constitution.md:
- Tolerância a falhas: Chamadas com timeout rígido. Se o provedor de IA falhar ou estiver sem rede,
  retorna status="indisponivel" sem quebrar o sistema.
- Idioma estritamente em português do Brasil (pt-BR).
- Consultor ESG: gera de 3 a 5 sugestões práticas de melhoria de transparência e processos.
- Regra determinística preliminar:
  1. Falta de CAR na NF compromete a rastreabilidade e penaliza Score.
  2. Volume extraído na NF maior que o permitido no CAR invalida com status="nao_apto".
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from app.schemas_audit import AIAuditResult, AuditCrossCheckRequest

log = logging.getLogger("app.ai_auditor")

DEFAULT_AI_TIMEOUT_S = 10.0
AI_AUDITOR_PROMPT = """Você é um Consultor e Auditor Sênior Socioambiental/ESG especializado na cadeia de valor de madeira nativa e silvicultura no Brasil, com foco em rastreabilidade, compliance com o Código Florestal Brasileiro, CAR (Cadastro Ambiental Rural), DOF (Documento de Origem Florestal / IBAMA / Sisflora) e dados de desmatamento/embargos (MapBiomas).

Sua tarefa é auditar os dados de uma Nota Fiscal (NF) de madeira cruzados com os dados do imóvel rural no CAR (MapBiomas) e emitir um parecer estruturado.

Regras centrais do negócio:
1. Rastreabilidade e CAR: Se a NF NÃO contiver o número do CAR, a rastreabilidade está severamente comprometida. A empresa perde pontuação significativa no Score ESG.
2. Limite de Volume: Se o volume total extraído/transportado na NF for MAIOR que o volume autorizado/permitido para o imóvel rural, o status de validação é estritamente "nao_apto".
3. Status permitidos: "apto" ou "nao_apto".
4. Score ESG: Número inteiro de 0 a 100 refletindo transparência e integridade da operação.
5. Justificativa: Explicação técnica, clara e formal em português do Brasil (pt-BR).
6. Sugestões de melhoria: OBRIGATORIAMENTE entre 3 e 5 sugestões práticas, focadas em governança florestal, auditoria de cadeia de custódia, conformidade documental e transparência para o produtor.

Responda OBRIGATORIAMENTE em JSON válido com exatamente esta estrutura:
{
  "status": "apto" ou "nao_apto",
  "score": <número inteiro de 0 a 100>,
  "justification": "<texto detalhado em pt-BR>",
  "suggestions": [
    "<sugestão prática 1>",
    "<sugestão prática 2>",
    "<sugestão prática 3>"
  ]
}
"""


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _build_deterministic_evaluation(req: AuditCrossCheckRequest) -> tuple[str, int, list[str]]:
    """Gera avaliação base determinística em caso de indisponibilidade de LLM ou validação inicial."""
    invoice = req.invoice
    car = req.car_context

    has_car = bool(invoice.car_code and invoice.car_code.strip())
    volume_extracted = invoice.volume_extracted_m3
    max_volume = car.max_volume_allowed_m3 if car else None
    alerts_count = car.alerts_count if car else None
    embargoes_count = car.embargoes_count if car else None

    # Base score
    score = 100
    reasons: list[str] = []
    suggestions: list[str] = []

    # 1. Checagem de CAR
    if not has_car:
        score -= 40
        reasons.append(
            "A Nota Fiscal não contém a identificação do código do CAR de origem, inviabilizando a rastreabilidade direta da madeira."
        )
        suggestions.append(
            "Incluir obrigatoriamente a identificação do CAR nos dados adicionais da NF-e e na guia florestal (DOF/Sisflora)."
        )
    elif car and car.mapbiomas_status == "not_in_mapbiomas":
        score -= 20
        reasons.append(
            "O CAR informado na NF não consta na base de polígonos validados do MapBiomas Alerta."
        )
        suggestions.append(
            "Verificar a regularidade cadastral do imóvel no SICAR e a atualização dos polígonos geoespaciais."
        )

    # 2. Checagem de volume
    volume_exceeded = False
    if max_volume is not None and volume_extracted > max_volume:
        volume_exceeded = True
        score -= 50
        reasons.append(
            f"O volume declarado na NF ({volume_extracted:.2f} m³) ultrapassa o volume máximo autorizado para o imóvel ({max_volume:.2f} m³)."
        )
        suggestions.append(
            "Ajustar os planos de corte e remessas para que não superem os saldos autorizados pelo órgão ambiental competente."
        )
    elif max_volume is not None:
        reasons.append(
            f"Volume declarado ({volume_extracted:.2f} m³) compatível com a cota autorizada ({max_volume:.2f} m³)."
        )

    # 3. Alertas e embargos
    if alerts_count and alerts_count > 0:
        score -= min(30, alerts_count * 10)
        reasons.append(f"Imóvel rural possui {alerts_count} alerta(s) de desmatamento registrado(s) no MapBiomas.")
        suggestions.append(
            "Realizar auditoria de sobreposição espacial entre as áreas de corte e os alertas de desmatamento recentes."
        )

    if embargoes_count and embargoes_count > 0:
        score -= min(40, embargoes_count * 20)
        reasons.append(f"Imóvel rural possui {embargoes_count} embargo(s) ativo(s) registrado(s).")
        suggestions.append(
            "Suspender imediatamente retiradas em parcelas com embargos administrativos ou judiciais vigentes."
        )

    # Sugestões gerais se faltarem itens para atingir o mínimo de 3
    default_suggestions = [
        "Implantar sistema de custódia com código QR integrando a NF-e ao DOF e ao CAR.",
        "Disponibilizar relatórios periódicos de conformidade florestal aos compradores na plataforma.",
        "Adotar certificação voluntária de manejo florestal sustentável (ex.: FSC ou PEFC).",
    ]
    for s in default_suggestions:
        if len(suggestions) >= 5:
            break
        if s not in suggestions:
            suggestions.append(s)

    score = max(0, min(100, score))
    is_apto = has_car and not volume_exceeded and (embargoes_count or 0) == 0

    status = "apto" if is_apto else "nao_apto"
    return status, score, suggestions[:5]


def _build_prompt_payload(req: AuditCrossCheckRequest) -> str:
    """Prepara os dados em formato JSON textual para envio ao modelo."""
    payload = {
        "nota_fiscal": {
            "numero": req.invoice.invoice_number,
            "cnpj_emitente": req.invoice.issuer_cnpj,
            "data_emissao": str(req.invoice.issue_date) if req.invoice.issue_date else None,
            "car_declarado": req.invoice.car_code,
            "volume_extraido_m3": req.invoice.volume_extracted_m3,
            "itens": [item.model_dump() for item in req.invoice.items],
        },
        "contexto_imovel_car": {
            "car_codigo": req.car_context.car_code if req.car_context else None,
            "uf": req.car_context.state if req.car_context else None,
            "area_ha": req.car_context.area_ha if req.car_context else None,
            "alertas_desmatamento": req.car_context.alerts_count if req.car_context else None,
            "embargos_ativos": req.car_context.embargoes_count if req.car_context else None,
            "volume_maximo_permitido_m3": req.car_context.max_volume_allowed_m3 if req.car_context else None,
            "status_mapbiomas": req.car_context.mapbiomas_status if req.car_context else None,
        } if req.car_context else None,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


async def call_llm_api(
    prompt: str,
    system_instruction: str = AI_AUDITOR_PROMPT,
    timeout_s: float = DEFAULT_AI_TIMEOUT_S,
    api_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    """Executa chamada assíncrona HTTP ao endpoint do LLM com timeout garantido."""
    endpoint = api_url or os.getenv("LLM_API_URL") or "https://api.rebootearth.local/v1/chat/completions"
    key = api_key or os.getenv("LLM_API_KEY") or "mock-key"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": os.getenv("LLM_MODEL", "gemini-2.5-flash"),
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

            # Suporte para formato OpenAI/Gemini-compatible chat completions
            content = ""
            if body.get("choices"):
                content = body["choices"][0]["message"]["content"]
            elif body.get("candidates"):
                content = body["candidates"][0]["content"]["parts"][0]["text"]
            elif "response" in body:
                content = body["response"]
            else:
                content = json.dumps(body)

            # Limpa possíveis blocos markdown ```json
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


async def audit_invoice_with_car(
    req: AuditCrossCheckRequest,
    timeout_s: float = DEFAULT_AI_TIMEOUT_S,
    llm_api_url: str | None = None,
    allow_fallback: bool = True,
) -> AIAuditResult:
    """Realiza a auditoria ESG cruzando NF e CAR.

    Tolerância a falhas:
    - Se a IA estiver disponível, extrai o julgamento enriquecido com sugestões.
    - Se a API cair ou der timeout:
        - Se allow_fallback=True e houver dados básicos, usa avaliação determinística segura.
        - Caso contrário, retorna status="indisponivel" sem lançar erro 500.
    """
    now = _now_utc()
    invoice = req.invoice
    car = req.car_context

    # 1. Regra estrita mandatória: Sem CAR = penalização imediata no Score e perda de rastreabilidade
    missing_car = not (invoice.car_code and invoice.car_code.strip())

    # 2. Regra estrita mandatória: Volume NF > Volume CAR = Não Apto
    volume_exceeded = False
    if car and car.max_volume_allowed_m3 is not None and invoice.volume_extracted_m3 > car.max_volume_allowed_m3:
        volume_exceeded = True

    # Prepara prompt
    user_prompt = f"Por favor audite a seguinte operação florestal:\n{_build_prompt_payload(req)}"

    llm_result = await call_llm_api(user_prompt, timeout_s=timeout_s, api_url=llm_api_url)

    if llm_result:
        raw_status = str(llm_result.get("status", "")).lower().strip()
        status = "apto" if raw_status == "apto" else "nao_apto"

        # Impor restrições invioláveis do negócio sobre a resposta do LLM:
        if missing_car or volume_exceeded:
            status = "nao_apto"

        score = llm_result.get("score")
        if score is not None:
            try:
                score = int(score)
                if missing_car and score > 50:
                    score = 45  # penalidade de transparência
                if volume_exceeded and score > 40:
                    score = 30  # penalidade por excesso de cota
                score = max(0, min(100, score))
            except (ValueError, TypeError):
                score = 30 if (missing_car or volume_exceeded) else 75
        else:
            score = 30 if (missing_car or volume_exceeded) else 80

        justification = llm_result.get("justification", "Auditoria concluída com sucesso.")
        suggestions = llm_result.get("suggestions", [])
        if not isinstance(suggestions, list) or len(suggestions) < 3:
            _, _, default_suggs = _build_deterministic_evaluation(req)
            suggestions = default_suggs

        return AIAuditResult(
            status=status,
            score=score,
            justification=justification,
            suggestions=suggestions[:5],
            audited_at=now,
        )

    # Caso o LLM esteja indisponível:
    if allow_fallback:
        det_status, det_score, det_suggestions = _build_deterministic_evaluation(req)
        justification_parts = [
            "Auditoria preliminar processada via motor de contingência (serviço de IA indisponível no momento)."
        ]
        if missing_car:
            justification_parts.append(
                "Aviso crítico: Ausência do código do CAR na NF compromete a rastreabilidade florestal."
            )
        if volume_exceeded and car and car.max_volume_allowed_m3 is not None:
            justification_parts.append(
                f"Violação de volume: {invoice.volume_extracted_m3} m³ declarado excede {car.max_volume_allowed_m3} m³ permitido."
            )

        return AIAuditResult(
            status=det_status,
            score=det_score,
            justification=" ".join(justification_parts),
            suggestions=det_suggestions,
            audited_at=now,
        )

    # Se fallback não for permitido e a API de IA cair:
    return AIAuditResult(
        status="indisponivel",
        score=None,
        justification="O serviço de auditoria com IA está temporariamente indisponível. Tente novamente mais tarde.",
        suggestions=[],
        audited_at=now,
    )
