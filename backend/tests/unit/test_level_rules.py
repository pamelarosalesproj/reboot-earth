"""Regras de nível da feature 006 (FR-601…606): funções puras car_level e cnpj_level."""

from datetime import UTC, date, datetime

import pytest

from app.schemas import (
    AlertIndicator,
    CarDetail,
    CarIndicators,
    CarSummary,
    Context,
    Deter,
    DeterClass,
    Embargo,
    OpenRisks,
    SourceStatus,
    Status,
)
from app.services.cnpj_report import get_score
from app.services.level_rules import car_level, cnpj_level

TODAY = date(2026, 11, 6)
NOW = datetime(2026, 11, 6, tzinfo=UTC)


def detail(area=1000.0, embargoes=(), emb_status="ok"):
    return CarDetail(
        summary=CarSummary(car_code="PA-1", area_ha=area, alerts_count=0, embargoes_count=len(embargoes),
                           embargoes_status=emb_status, fetched_at=NOW),
        alerts=[],
        embargoes=[Embargo(source="IBAMA", process_code=p, area_ha=1.0, registered_at=None,
                           expired_at=exp, descriptions=[]) for p, exp in embargoes],
    )


def alert(status="pendente", area=5.0, post_2020=True, rl=0.0, app=False, ti=0.0, uc=0.0, code=1):
    return AlertIndicator(alert_code=code, detected_at=date(2024, 1, 1), area_in_car_ha=area, status=status,
                          post_2020=post_2020, authorized_ha=0.0, legal_reserve_ha=rl, touches_app=app,
                          indigenous_land_ha=ti, integral_protection_ha=uc, sustainable_use_ha=0.0)


def ind(alerts=(), deter=None, mapbiomas="ok", deter_status="ok", **context):
    sources = {"mapbiomas": SourceStatus(status=mapbiomas), "prodes": SourceStatus(status="indisponivel"),
               "deter": SourceStatus(status=deter_status), "focos": SourceStatus(status="indisponivel"),
               "sinaflor": SourceStatus(status="indisponivel")}
    return CarIndicators(
        car_code="PA-1", fetched_at=NOW, sources=sources, alerts_by_status={}, open=OpenRisks(),
        context=Context(deter=Deter(by_class={k: DeterClass(n=n, ha=ha, last=last)
                                              for k, (n, ha, last) in (deter or {}).items()}), **context),
        alerts=list(alerts),
    )


def codes(s: Status) -> list[str]:
    return [r.code for r in s.reasons]


# --- CAR -------------------------------------------------------------------------------------

def test_gold_without_open_risks():
    s = car_level(detail(), ind(), TODAY)
    assert (s.level, s.reasons, s.partial, s.eudr_attention) == ("gold", [], False, False)


def test_superseded_alerts_never_downgrade():
    alerts = [alert(status=st, rl=5.0, app=True, ti=1.0, code=i)
              for i, st in enumerate(("autorizada", "embargo_levantado", "suspensa_judicial"))]
    s = car_level(detail(embargoes=[("P1", date(2023, 1, 1))]), ind(alerts), TODAY)  # embargo levantado
    assert s.level == "gold"
    assert s.eudr_attention is True  # EUDR: desmatamento pós-2020 mesmo autorizado (FR-606)


def test_active_embargo_is_bronze():
    s = car_level(detail(embargoes=[("P1", None), ("P2", None)]), ind(), TODAY)
    assert s.level == "bronze" and s.reasons[0].model_dump(exclude_none=True) == {
        "code": "EMBARGO_VIGENTE", "severity": "bronze", "n": 2}


@pytest.mark.parametrize("kw", [{"ti": 2.0}, {"uc": 1.5}])
def test_open_alert_in_indigenous_land_or_integral_uc_is_bronze(kw):
    s = car_level(detail(), ind([alert(post_2020=False, **kw)]), TODAY)
    assert s.level == "bronze" and codes(s) == ["TI_UC_INTEGRAL", "ALERTA_ABERTA"]


@pytest.mark.parametrize(("area", "kw", "level"), [
    (10.0, {"rl": 3.0}, "bronze"),     # 10 ha de 1000 = 1 % → Bronze
    (9.9, {"rl": 3.0}, "silver"),      # 0,99 % → Silver
    (20.0, {"app": True}, "bronze"),   # APP conta igual
])
def test_rl_app_after_2020_threshold(area, kw, level):
    s = car_level(detail(area=1000.0), ind([alert(area=area, **kw)]), TODAY)
    assert s.level == level
    r = s.reasons[0]
    assert (r.code, r.severity, r.n, r.ha) == ("RL_APP_POS2020", level, 1, area)
    assert r.pct == round(100 * area / 1000, 2)


def test_rl_app_before_2021_is_only_open_alert():
    s = car_level(detail(), ind([alert(post_2020=False, rl=50.0, app=True)]), TODAY)
    assert s.level == "silver" and codes(s) == ["ALERTA_ABERTA"] and s.eudr_attention is False


def test_unknown_car_area_is_conservative_bronze():
    s = car_level(detail(area=None), ind([alert(area=0.1, rl=0.1)]), TODAY)
    assert s.level == "bronze" and s.reasons[0].pct is None


@pytest.mark.parametrize(("cls", "last", "level"), [
    ("CS_DESORDENADO", "2025-03-01", "bronze"),
    ("MINERACAO", "2024-11-07", "bronze"),       # dentro de 24 meses
    ("MINERACAO", "2024-11-05", "gold"),         # fora da janela
    ("DEGRADACAO", "2026-01-10", "silver"),
    ("CS_GEOMETRICO", "2026-01-10", "gold"),     # padrão de manejo: nunca rebaixa
])
def test_deter_last_24_months(cls, last, level):
    s = car_level(detail(), ind(deter={cls: (2, 4.0, last)}), TODAY)
    assert s.level == level


def test_context_and_failed_context_sources_never_downgrade():
    s = car_level(detail(), ind(deter={"CS_DESORDENADO": (1, 1.0, "2026-01-01")}, deter_status="indisponivel"),
                  TODAY)
    assert s.level == "gold" and not s.partial  # DETER caído: não penaliza (FR-603)


def test_all_reasons_are_listed():
    s = car_level(detail(embargoes=[("P1", None)]),
                  ind([alert(rl=1.0, area=50.0), alert(ti=1.0, code=2)],
                      deter={"DEGRADACAO": (1, 2.0, "2026-05-01")}), TODAY)
    assert codes(s) == ["EMBARGO_VIGENTE", "TI_UC_INTEGRAL", "RL_APP_POS2020", "ALERTA_ABERTA",
                        "DETER_DEGRADACAO"]
    assert (s.alerts_count, s.embargoes_count) == (2, 1)


@pytest.mark.parametrize(("d", "i"), [
    (detail(emb_status="not_determinable"), ind()),
    (detail(), ind(mapbiomas="indisponivel")),
    (detail(), None),
])
def test_partial_data_is_silver(d, i):
    s = car_level(d, i, TODAY)
    assert (s.level, s.partial, codes(s)) == ("silver", True, ["DADOS_PARCIAIS"])


def test_partial_with_active_embargo_is_still_bronze():
    s = car_level(detail(embargoes=[("P1", None)]), ind(mapbiomas="indisponivel"), TODAY)
    assert s.level == "bronze" and s.eudr_attention is None  # EUDR indeterminado, nunca False


def test_without_detail_is_sem_dados():
    s = car_level(None, ind(), TODAY)
    assert (s.level, s.reason) == ("sem_dados", "data_unavailable")
    assert get_score(s).state == "nao_calculavel"


# --- CNPJ ------------------------------------------------------------------------------------

def lvl(level, *reasons, partial=False, eudr=False):
    from app.schemas import Reason
    return Status(level=level, reason=None, partial=partial, basis="regras", eudr_attention=eudr,
                  reasons=[Reason(code=c, severity="bronze" if c in ("EMBARGO_VIGENTE", "RL_APP_POS2020")
                                  else "silver") for c in reasons])


def test_cnpj_is_worst_car_with_reason_counts():
    s = cnpj_level([lvl("gold"), lvl("silver", "ALERTA_ABERTA"),
                    lvl("bronze", "EMBARGO_VIGENTE", "ALERTA_ABERTA"), lvl("bronze", "RL_APP_POS2020")], True)
    assert s.level == "bronze"
    assert s.cars_by_level.model_dump() == {"gold": 1, "silver": 1, "bronze": 2, "sem_dados": 0}
    assert [(r.code, r.cars) for r in s.reasons] == [("EMBARGO_VIGENTE", 1), ("RL_APP_POS2020", 1)]
    assert all(r.n is None and r.ha is None for r in s.reasons)  # não soma entre CARs


def test_cnpj_counts_reason_only_where_it_defines_the_level():
    """RL/APP abaixo de 1 % (Silver) num CAR Bronze por embargo não conta como motivo do CNPJ Bronze."""
    from app.schemas import Reason
    mt = Status(level="bronze", reason=None, partial=False, basis="regras", reasons=[
        Reason(code="EMBARGO_VIGENTE", severity="bronze", n=5),
        Reason(code="RL_APP_POS2020", severity="silver", n=4, pct=0.82)])
    pe = Status(level="bronze", reason=None, partial=False, basis="regras", reasons=[
        Reason(code="RL_APP_POS2020", severity="bronze", n=3, pct=28.18)])
    s = cnpj_level([mt, pe, lvl("silver", "ALERTA_ABERTA")], True)
    assert [(r.code, r.severity, r.cars) for r in s.reasons] == [("EMBARGO_VIGENTE", "bronze", 1),
                                                                 ("RL_APP_POS2020", "bronze", 1)]


def test_cnpj_gold_with_missing_car_is_silver():
    s = cnpj_level([lvl("gold"), car_level(None, None, TODAY)], True)
    assert (s.level, s.partial) == ("silver", True)
    assert [(r.code, r.cars) for r in s.reasons] == [("DADOS_PARCIAIS", 1)]
    assert s.eudr_attention is None


def test_cnpj_without_data_and_registration_cases():
    assert cnpj_level([car_level(None, None, TODAY)], True).reason == "data_unavailable"
    assert cnpj_level([], True).reason == "no_properties"
    assert cnpj_level([], False).reason == "not_registered"


def test_cnpj_gold_and_eudr():
    s = cnpj_level([lvl("gold"), lvl("gold", eudr=True)], True)
    assert (s.level, s.reasons, s.eudr_attention) == ("gold", [], True)
    assert get_score(s).state == "em_calculo"
