"""Regras de nível Gold/Silver/Bronze/Sem dados por CAR e por CNPJ (feature 006, FR-601…606).

Funções puras: recebem os dados já calculados (detalhe da 001 e indicadores da 003) e devolvem
`Status`. São a única implementação da regra (constituição IV): painel, ficha pública e relatório
usam estas funções. O texto da página "Entenda o nível" descreve exatamente estas constantes.
"""

from datetime import date, timedelta

from app.schemas import OPEN_SITUACOES, CarDetail, CarIndicators, CarsByLevel, Reason, Status

RL_APP_THRESHOLD_PCT = 1.0  # Bronze se as alertas abertas pós-2020 em RL/APP somam ≥ 1 % do CAR
DETER_WINDOW_DAYS = 730  # "últimos 24 meses"
DETER_GRAVE = ("CS_DESORDENADO", "MINERACAO")
DETER_DEGRADACAO = ("DEGRADACAO",)

ORDER = {"bronze": 0, "silver": 1, "gold": 2}  # do pior ao melhor (sem_dados à parte)
CODE_ORDER = ("EMBARGO_VIGENTE", "TI_UC_INTEGRAL", "RL_APP_POS2020", "DETER_GRAVE",
              "ALERTA_ABERTA", "DETER_DEGRADACAO", "DADOS_PARCIAIS")


def _ok(ind: CarIndicators | None, source: str) -> bool:
    return bool(ind and ind.sources.get(source) and ind.sources[source].status == "ok")  # type: ignore[index]


def _deter_recent(ind: CarIndicators, classes: tuple[str, ...], since: str) -> tuple[int, float]:
    """(nº, ha) das classes DETER com detecção mais recente dentro da janela."""
    deter = ind.context.deter
    n, ha = 0, 0.0
    for name in classes:
        c = deter.by_class.get(name) if deter else None
        if c and c.last and c.last >= since:
            n, ha = n + c.n, ha + c.ha
    return n, round(ha, 2)


def car_level(detail: CarDetail | None, ind: CarIndicators | None, today: date) -> Status:
    """Nível de um CAR (FR-601). Avalia todos os critérios para listar todos os motivos (FR-602)."""
    if detail is None:
        return Status(level="sem_dados", reason="data_unavailable", partial=True, basis="regras")

    reasons: list[Reason] = []
    emb_ok = detail.summary.embargoes_status == "ok"
    active = [e for e in detail.embargoes if not e.expired_at] if emb_ok else []
    if active:
        reasons.append(Reason(code="EMBARGO_VIGENTE", severity="bronze", n=len(active)))

    mb_ok = _ok(ind, "mapbiomas")
    open_alerts = [a for a in ind.alerts if a.status in OPEN_SITUACOES] if (mb_ok and ind) else []
    if mb_ok and ind:
        ti_uc = [a for a in open_alerts if a.indigenous_land_ha > 0 or a.integral_protection_ha > 0]
        if ti_uc:
            ha = sum(a.indigenous_land_ha + a.integral_protection_ha for a in ti_uc)
            reasons.append(Reason(code="TI_UC_INTEGRAL", severity="bronze", n=len(ti_uc), ha=round(ha, 2)))

        rl_app = [a for a in open_alerts if a.post_2020 and (a.legal_reserve_ha > 0 or a.touches_app)]
        if rl_app:
            ha = round(sum(a.area_in_car_ha for a in rl_app), 2)
            area = detail.summary.area_ha
            pct = round(100 * ha / area, 2) if area else None
            # Área do CAR desconhecida: conservador, conta como Bronze (spec, Edge Cases).
            severity = "bronze" if pct is None or pct >= RL_APP_THRESHOLD_PCT else "silver"
            reasons.append(Reason(code="RL_APP_POS2020", severity=severity, n=len(rl_app), ha=ha, pct=pct))

    if ind and _ok(ind, "deter"):
        since = (today - timedelta(days=DETER_WINDOW_DAYS)).isoformat()
        n, ha = _deter_recent(ind, DETER_GRAVE, since)
        if n:
            reasons.append(Reason(code="DETER_GRAVE", severity="bronze", n=n, ha=ha))
        n, ha = _deter_recent(ind, DETER_DEGRADACAO, since)
        if n:
            reasons.append(Reason(code="DETER_DEGRADACAO", severity="silver", n=n, ha=ha))

    if open_alerts:
        ha = round(sum(a.area_in_car_ha for a in open_alerts), 2)
        reasons.append(Reason(code="ALERTA_ABERTA", severity="silver", n=len(open_alerts), ha=ha))

    partial = not emb_ok or not mb_ok
    if partial:
        reasons.append(Reason(code="DADOS_PARCIAIS", severity="silver"))

    reasons.sort(key=lambda r: CODE_ORDER.index(r.code))
    level = ("bronze" if any(r.severity == "bronze" for r in reasons)
             else "silver" if reasons else "gold")
    return Status(
        level=level, reason=None, partial=partial, basis="regras", reasons=reasons,
        eudr_attention=any(a.post_2020 for a in ind.alerts) if (mb_ok and ind) else None,
        alerts_count=len(open_alerts) if mb_ok else None,
        embargoes_count=len(active) if emb_ok else None,
    )


def cnpj_level(cars: list[Status], registered: bool) -> Status:
    """Nível do CNPJ = o pior dos seus CARs com dados (FR-604/605)."""
    def sem_dados(reason, partial=False, by=None):
        return Status(level="sem_dados", reason=reason, partial=partial, basis="regras", cars_by_level=by)

    if not registered:
        return sem_dados("not_registered")
    if not cars:
        return sem_dados("no_properties", by=CarsByLevel())
    by = CarsByLevel(**{lvl: sum(1 for c in cars if c.level == lvl)
                        for lvl in ("gold", "silver", "bronze", "sem_dados")})
    with_data = [c for c in cars if c.level != "sem_dados"]
    if not with_data:
        return sem_dados("data_unavailable", partial=True, by=by)

    worst = min((c.level for c in with_data), key=ORDER.__getitem__)
    missing = by.sem_dados > 0
    if worst == "gold" and missing:
        worst = "silver"

    # Motivos que definem o nível de cada CAR nesse nível, contando CARs (sem somar números: princípio IV).
    # Só conta um motivo num CAR se ele tem a gravidade do nível: ex. RL/APP abaixo de 1 % (Silver)
    # num CAR Bronze por embargo não entra nos motivos de um CNPJ Bronze.
    deciding = [c for c in with_data if c.level == worst] if worst != "gold" else []
    counts: dict[str, tuple[str, int]] = {}
    for c in deciding:
        for r in {r.code: r for r in c.reasons if r.severity == worst}.values():
            counts[r.code] = (r.severity, counts.get(r.code, (r.severity, 0))[1] + 1)
    partial = missing or any(c.partial for c in with_data)
    if partial and "DADOS_PARCIAIS" not in counts:
        counts["DADOS_PARCIAIS"] = ("silver", by.sem_dados + sum(1 for c in with_data if c.partial))
    reasons = [Reason(code=code, severity=sev, cars=n)  # type: ignore[arg-type]
               for code, (sev, n) in sorted(counts.items(), key=lambda kv: CODE_ORDER.index(kv[0]))]

    eudr = [c.eudr_attention for c in with_data]
    return Status(
        level=worst, reason=None, partial=partial, basis="regras", reasons=reasons, cars_by_level=by,
        eudr_attention=True if any(eudr) else (None if None in eudr or missing else False),
    )
