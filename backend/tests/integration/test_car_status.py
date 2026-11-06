"""Nível por CAR: a regra do CNPJ (compute_status) aplicada a um único imóvel."""

from tests.conftest import OTHER_CAR, REF_CAR, register
from tests.integration.test_public_status_levels import EMBARGO


def test_summary_and_detail_carry_car_level(client, mapbiomas_mock):
    register(client, cars=(REF_CAR, OTHER_CAR))
    mapbiomas_mock.embargoes[OTHER_CAR] = [EMBARGO]
    ref = client.get(f"/api/cars/{REF_CAR}/summary").json()["status"]
    assert ref["level"] == "silver" and ref["alerts_count"] == 3
    # O embargo de outro imóvel do CNPJ não muda o nível deste CAR.
    other = client.get(f"/api/cars/{OTHER_CAR}/detail").json()["summary"]["status"]
    assert other["level"] == "bronze" and other["embargoes_count"] == 1
