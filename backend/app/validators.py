"""Validación de CNPJ y código CAR (research.md R8, data-model.md)."""

import re

CAR_RE = re.compile(r"^[A-Z]{2}-\d{7}-[0-9A-F]{32}$")
_W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_W2 = [6, *_W1]


def _dv(digits: list[int], weights: list[int]) -> int:
    rest = sum(d * w for d, w in zip(digits, weights)) % 11
    return 0 if rest < 2 else 11 - rest


def normalize_cnpj(value: str) -> str:
    """Devuelve el CNPJ con 14 dígitos o lanza ValueError."""
    raw = (value or "").strip()
    if re.search(r"[^\d./\-\s]", raw):
        raise ValueError("CNPJ deve conter apenas números")
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos")
    if len(set(digits)) == 1:
        raise ValueError("CNPJ inválido")
    nums = [int(c) for c in digits]
    if _dv(nums[:12], _W1) != nums[12] or _dv(nums[:13], _W2) != nums[13]:
        raise ValueError("CNPJ inválido (dígitos verificadores)")
    return digits


def normalize_car(value: str) -> str:
    """Devuelve el código CAR en mayúsculas o lanza ValueError."""
    code = (value or "").strip().upper()
    if not CAR_RE.match(code):
        raise ValueError(f"Código CAR inválido: {value!r}")
    return code
