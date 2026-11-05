"""Regla provisional de nivel (FR-111a) y estado del score (FR-108/109)."""

from datetime import UTC, datetime

import pytest

from app.services.cnpj_report import CarsAggregate, compute_status, get_score


def agg(cars=1, with_data=1, emb_unknown=0, alerts=0, embargoes=0):
    return CarsAggregate(
        cars_count=cars, cars_with_data=with_data, cars_unavailable=cars - with_data,
        cars_embargoes_unknown=emb_unknown, alerts_count=alerts, embargoes_count=embargoes,
        stale=False, oldest_fetched_at=datetime(2026, 11, 5, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("aggregate", "registered", "level", "reason", "score_state"),
    [
        (None, False, "sem_dados", "not_registered", "nao_calculavel"),
        (agg(cars=0, with_data=0), True, "sem_dados", "no_properties", "nao_calculavel"),
        (None, True, "sem_dados", "no_properties", "nao_calculavel"),
        (agg(cars=2, with_data=0, alerts=None, embargoes=None), True, "sem_dados", "data_unavailable",
         "nao_calculavel"),
        (agg(embargoes=1), True, "bronze", None, "em_calculo"),
        (agg(alerts=3, embargoes=2), True, "bronze", None, "em_calculo"),  # embargo gana a alerta
        (agg(alerts=1), True, "silver", None, "em_calculo"),
        (agg(), True, "gold", None, "em_calculo"),
    ],
)
def test_rule_table(aggregate, registered, level, reason, score_state):
    s = compute_status(aggregate, registered)
    assert (s.level, s.reason, s.basis) == (level, reason, "provisional")
    assert get_score(s).state == score_state
    assert get_score(s).value is None


def test_partial_unavailable_car_blocks_gold():
    s = compute_status(agg(cars=2, with_data=1), True)
    assert (s.level, s.partial) == ("silver", True)


def test_partial_embargoes_unknown_blocks_gold():
    """Caso CAR not_in_mapbiomas: embargos no determinables (research R5)."""
    s = compute_status(agg(cars=2, with_data=2, emb_unknown=1), True)
    assert (s.level, s.partial) == ("silver", True)


def test_partial_with_embargo_is_still_bronze():
    s = compute_status(agg(cars=2, with_data=1, embargoes=1), True)
    assert (s.level, s.partial) == ("bronze", True)


def test_gold_is_never_partial():
    for a in (agg(), agg(cars=3, with_data=3)):
        s = compute_status(a, True)
        assert s.level == "gold" and s.partial is False
