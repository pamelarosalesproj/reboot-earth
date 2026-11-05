"""Agregación compartida por el panel y la ficha pública (constitución IV)."""

from datetime import UTC, date, datetime

from app.schemas import Alert, CarDetail, CarSummary, Embargo
from app.services.cnpj_report import aggregate_cars

T1 = datetime(2026, 11, 1, tzinfo=UTC)
T2 = datetime(2026, 11, 5, tzinfo=UTC)


def detail(code, alerts=(), embargoes=(), emb_status="ok", fetched=T2, stale=False):
    return CarDetail(
        summary=CarSummary(car_code=code, alerts_count=len(alerts), embargoes_count=len(embargoes),
                           embargoes_status=emb_status, fetched_at=fetched, stale=stale),
        alerts=[Alert(alert_code=a, detected_at=date(2026, 1, 1), area_ha=1.0, area_in_car_ha=1.0,
                      embargoes_count=0) for a in alerts],
        embargoes=[Embargo(source=s, process_code=p, area_ha=1.0, registered_at=None, expired_at=None,
                           descriptions=[]) for s, p in embargoes],
    )


def test_shared_alert_counts_once():
    a = aggregate_cars([detail("A", alerts=[1, 2]), detail("B", alerts=[2, 3])], 2)
    assert a.alerts_count == 3


def test_repeated_embargo_counts_once():
    a = aggregate_cars([detail("A", embargoes=[("IBAMA", "P1")]),
                        detail("B", embargoes=[("IBAMA", "P1"), ("ICMBio", "P1")])], 2)
    assert a.embargoes_count == 2


def test_not_determinable_embargoes_excluded_and_counted_unknown():
    a = aggregate_cars([detail("A", embargoes=[("IBAMA", "P1")]),
                        detail("B", embargoes=[("IBAMA", "P9")], emb_status="not_determinable")], 2)
    assert a.embargoes_count == 1 and a.cars_embargoes_unknown == 1


def test_all_unavailable_is_null_never_zero():
    a = aggregate_cars([None, None], 2)
    assert a.alerts_count is None and a.embargoes_count is None
    assert (a.cars_with_data, a.cars_unavailable) == (0, 2)
    assert a.oldest_fetched_at is None


def test_no_cars_is_zero():
    a = aggregate_cars([], 0)
    assert (a.alerts_count, a.embargoes_count, a.cars_count) == (0, 0, 0)


def test_oldest_fetch_and_stale():
    a = aggregate_cars([detail("A", fetched=T2), detail("B", fetched=T1, stale=True), None], 3)
    assert a.oldest_fetched_at == T1 and a.stale is True and a.cars_unavailable == 1
