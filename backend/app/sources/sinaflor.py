"""SINAFLOR (IBAMA): planes de manejo de la Amazônia Legal por CAR (research R4).

El IBAMA publica un CSV diario de ~90 MB (sin consulta por CAR). Este módulo lo agrega por CAR
en la tabla `sinaflor_car`. Uso diario (p. ej. cron):  uv run python -m app.sources.sinaflor
"""

import csv
import logging
from collections.abc import Iterable
from datetime import date, datetime

import httpx
from sqlmodel import Session, delete

from app.config import settings
from app.db import utcnow
from app.models import SinaflorCar, SinaflorSync
from app.schemas import ForestManagement

log = logging.getLogger("app.sinaflor")

AMAZONIA_LEGAL_UF = {"AC", "AM", "AP", "MA", "MT", "PA", "RO", "RR", "TO"}
ACTIVE = {"Autorização Emitida", "Autorização Retificada"}


def _float(v: str) -> float:
    """'17.0402' → 17.0402; '1.234,5' → 1234.5 (el CSV mezcla separadores entre columnas)."""
    v = (v or "").strip()
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    try:
        return float(v or 0)
    except ValueError:
        return 0.0


def _date(v: str) -> date | None:
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime((v or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def aggregate_csv(lines: Iterable[str]) -> dict[str, SinaflorCar]:
    """Agrega por CAR. Filas repetidas de (autorización, especie, producto) cuentan una vez (máximo)."""
    reader = csv.reader(lines, delimiter=";")
    header = [h.strip().lstrip("﻿").upper() for h in next(reader)]
    ix = {h: i for i, h in enumerate(header)}
    vol: dict[tuple, float] = {}
    auths: dict[str, set[str]] = {}
    active: dict[str, set[str]] = {}
    last: dict[str, date] = {}
    for row in reader:
        if len(row) < len(header):
            continue
        car = row[ix["NRO_CAR_IMOVEL_RURAL"]].strip().upper()
        if not car:
            continue
        auth = row[ix["NRO_AUTORIZACAO"]].strip()
        auths.setdefault(car, set()).add(auth)
        if row[ix["SITUACAO"]].strip() in ACTIVE:
            active.setdefault(car, set()).add(auth)
        if (d := _date(row[ix["DATA_DE_EMISSAO"]])) and d > last.get(car, date.min):
            last[car] = d
        product = row[ix["PRODUTO"]]
        if "m³" in product:
            key = (car, auth, row[ix["NOME_CIENTIFICO"]].strip().lower(), product.replace(" ", ""))
            vol[key] = max(vol.get(key, 0.0), _float(row[ix["VOLUME"]]))
    volume: dict[str, float] = {}
    for (car, *_), v in vol.items():
        volume[car] = volume.get(car, 0.0) + v
    return {car: SinaflorCar(car_code=car, autorizacoes=len(a), vigentes=len(active.get(car, ())),
                             volume_m3=round(volume.get(car, 0.0), 2), ultima_emissao=last.get(car))
            for car, a in auths.items()}


def save(db: Session, rows: dict[str, SinaflorCar], last_modified: str | None = None) -> None:
    db.exec(delete(SinaflorCar))
    db.add_all(rows.values())
    sync = db.get(SinaflorSync, 1) or SinaflorSync(id=1)
    sync.synced_at, sync.source_last_modified, sync.rows = utcnow(), last_modified, len(rows)
    db.add(sync)
    db.commit()


def sync(db: Session, url: str | None = None) -> int:
    """Descarga en streaming y reemplaza el resumen. Devuelve el n.º de CARs."""
    url = url or settings.sinaflor_poa_url
    with httpx.Client(timeout=httpx.Timeout(60, read=300)) as http, http.stream("GET", url) as r:
        r.raise_for_status()
        rows = aggregate_csv(line for line in r.iter_lines())
        save(db, rows, r.headers.get("last-modified"))
    return len(rows)


def forest_management(db: Session, code: str) -> tuple[str, ForestManagement | None]:
    """(status, bloque) para la tarjeta: nao_se_aplica fuera de la Amazônia Legal, indisponivel sin sync."""
    if code[:2].upper() not in AMAZONIA_LEGAL_UF:
        return "nao_se_aplica", None
    if not db.get(SinaflorSync, 1):
        return "indisponivel", None
    row = db.get(SinaflorCar, code.upper())
    if not row:
        return "ok", ForestManagement(authorizations=0, active=0, volume_m3=0.0)
    return "ok", ForestManagement(authorizations=row.autorizacoes, active=row.vigentes,
                                  volume_m3=row.volume_m3, last_issued=row.ultima_emissao)


if __name__ == "__main__":
    from app.db import create_db_and_tables, engine

    logging.basicConfig(level=logging.INFO)
    create_db_and_tables()
    with Session(engine) as s:
        n = sync(s)
    print(f"SINAFLOR: {n} CARs con autorizaciones de manejo")
