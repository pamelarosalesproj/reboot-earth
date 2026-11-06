from datetime import date
from pathlib import Path

from app.sources.sinaflor import aggregate_csv

SAMPLE = Path(__file__).parents[1] / "fixtures" / "sinaflor_poa_sample.csv"
MT = "MT-5102504-FB5206A8AF224FDC8B7E1D19FCF26A8E"
AM = "AM-1301902-193D8AE16C334FD093F23497AF0B94D9"


def rows():
    with SAMPLE.open(encoding="utf-8-sig") as f:
        return aggregate_csv(f)


def test_dedup_decimal_and_non_m3():
    mt = rows()[MT]
    # 100.5 (duplicada cuenta una vez) + 1234.5 (coma decimal) + 20 (A2); Lenha(st) excluida
    assert mt.volume_m3 == 1355.0
    assert mt.autorizacoes == 2 and mt.vigentes == 1
    assert mt.ultima_emissao == date(2024, 4, 5)


def test_retificada_counts_as_active_and_rows_without_car_ignored():
    r = rows()
    assert r[AM].vigentes == 1 and r[AM].volume_m3 == 5.5
    assert set(r) == {MT, AM}
