"""Situación única por alerta (FR-301/302, data-model.md)."""

from datetime import date

import pytest

from app.schemas import Embargo
from app.services.car_indicators import classify_alert

ACTIVE = Embargo(source="IBAMA", process_code="P1", area_ha=1, registered_at=date(2022, 1, 1),
                 expired_at=None, descriptions=[])
LIFTED = ACTIVE.model_copy(update={"expired_at": date(2024, 1, 1)})


def alert(**kw):
    return {"alertCode": 1, **kw}


@pytest.mark.parametrize(("raw", "embargoes", "emb_status", "judicial", "expected"), [
    (alert(), [], "ok", set(), "pendente"),
    (alert(), [], "ok", {1}, "suspensa_judicial"),
    (alert(crossedEmbargoesArea=2.0), [ACTIVE], "ok", set(), "embargo_vigente"),
    (alert(crossedDeforestationAuthorizationsArea=3.0), [], "ok", set(), "autorizada"),
    (alert(crossedForestManagementsArea=3.0), [], "ok", set(), "autorizada"),
    (alert(crossedEmbargoesArea=2.0), [LIFTED], "ok", set(), "embargo_levantado"),
    (alert(actionsList=[{"type": "AUTO"}]), [], "ok", set(), "com_fiscalizacao"),
    # conflictos: gana la prioridad
    (alert(crossedEmbargoesArea=2.0), [ACTIVE], "ok", {1}, "suspensa_judicial"),
    (alert(crossedEmbargoesArea=2.0, crossedDeforestationAuthorizationsArea=3.0), [ACTIVE, LIFTED], "ok",
     set(), "embargo_vigente"),
    (alert(crossedDeforestationAuthorizationsArea=3.0, actionsList=[{"x": 1}]), [], "ok", set(), "autorizada"),
    (alert(crossedEmbargoesArea=2.0, crossedDeforestationAuthorizationsArea=3.0), [LIFTED], "ok", set(),
     "autorizada"),
    # embargos no determinables + cruce con embargo → no se puede afirmar que estén levantados
    (alert(crossedEmbargoesArea=2.0), None, "not_determinable", set(), "embargo_vigente"),
    # cruce con embargo pero el CAR no tiene embargos listados → vigente (no se puede probar el levantamiento)
    (alert(crossedEmbargoesArea=2.0), [], "ok", set(), "embargo_vigente"),
    (alert(crossedEmbargoesArea=0.0, actionsList=[]), [ACTIVE], "ok", set(), "pendente"),
])
def test_priority(raw, embargoes, emb_status, judicial, expected):
    assert classify_alert(raw, embargoes, emb_status, judicial) == expected


def test_overlaps_are_capped_to_area_in_car():
    from app.services.car_indicators import alert_indicator

    raw = {"alertCode": 747059, "detectedAt": "2022-11-01", "areaHa": 7.96,
           "crossedRuralProperties": [{"code": "MT-X", "alertAreaInCar": 6.55}],
           "crossedLegalReservesArea": 7.69, "crossedFederalProtectedAreaSustainableUsesArea": 9.0}
    a = alert_indicator(raw, "MT-X", "pendente")
    assert a.area_in_car_ha == 6.55 and a.legal_reserve_ha == 6.55 and a.sustainable_use_ha == 6.55
