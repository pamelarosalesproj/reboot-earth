"""Nível por CAR (feature 006): car_level com o detalhe e os indicadores do imóvel."""

from tests.conftest import OTHER_CAR, REF_CAR, register
from tests.integration.test_public_status_levels import EMBARGO


def test_summary_and_detail_carry_car_level(client, mapbiomas_mock):
    register(client, cars=(REF_CAR, OTHER_CAR))
    mapbiomas_mock.embargoes[OTHER_CAR] = [EMBARGO]
    ref = client.get(f"/api/cars/{REF_CAR}/summary").json()["status"]
    assert ref["level"] == "bronze" and ref["alerts_count"] == 3  # RL/APP pós-2020 ≥ 1 %
    rl = ref["reasons"][0]
    assert rl["code"] == "RL_APP_POS2020" and rl["n"] == 3 and rl["pct"] >= 1
    # O embargo de outro imóvel do CNPJ não muda o nível deste CAR.
    other = client.get(f"/api/cars/{OTHER_CAR}/detail").json()["summary"]["status"]
    assert other["level"] == "bronze" and other["embargoes_count"] == 1
    assert other["reasons"][0] == {"code": "EMBARGO_VIGENTE", "severity": "bronze", "n": 1,
                                   "ha": None, "pct": None, "cars": None}
