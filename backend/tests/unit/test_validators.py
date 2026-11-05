import pytest

from app.validators import normalize_car, normalize_cnpj

CAR = "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"


@pytest.mark.parametrize("value", ["04.654.691/0001-06", "04654691000106", " 04.654.691/0001-06 "])
def test_cnpj_valid(value):
    assert normalize_cnpj(value) == "04654691000106"


@pytest.mark.parametrize("value", ["04.654.691/0001-07", "11111111111111", "0465469100010", "", "04.654.691/0001-0A"])
def test_cnpj_invalid(value):
    with pytest.raises(ValueError):
        normalize_cnpj(value)


def test_car_valid_and_uppercased():
    assert normalize_car(CAR) == CAR
    assert normalize_car(CAR.lower()) == CAR
    assert normalize_car(f"  {CAR} ") == CAR


@pytest.mark.parametrize("value", ["PE-123", "", "PE2607505F2671DDFDA3D47CC917EB3E0DFEEB8B0",
                                   "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B", "XYZ-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"])
def test_car_invalid(value):
    with pytest.raises(ValueError):
        normalize_car(value)
