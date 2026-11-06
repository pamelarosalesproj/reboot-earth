"""Tablas persistidas (ver specs/001-producer-car-dashboard/data-model.md)."""

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.db import utcnow


class MapBiomasStatus(StrEnum):
    found = "found"
    not_in_mapbiomas = "not_in_mapbiomas"


class Producer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)  # siempre en minúsculas
    password_hash: str
    cnpj: str = Field(max_length=14)  # solo dígitos
    created_at: datetime = Field(default_factory=utcnow)

    cars: list["ProducerCar"] = Relationship(
        back_populates="producer", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProducerCar(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("producer_id", "car_code"),)

    id: int | None = Field(default=None, primary_key=True)
    producer_id: int = Field(
        sa_column=Column(Integer, ForeignKey("producer.id", ondelete="CASCADE"), nullable=False)
    )
    car_code: str = Field(index=True)  # en mayúsculas
    mapbiomas_status: MapBiomasStatus = MapBiomasStatus.found
    added_at: datetime = Field(default_factory=utcnow)

    producer: Producer | None = Relationship(back_populates="cars")


class AuthSession(SQLModel, table=True):
    __tablename__ = "session"

    token: str = Field(primary_key=True)
    producer_id: int = Field(
        sa_column=Column(Integer, ForeignKey("producer.id", ondelete="CASCADE"), nullable=False)
    )
    expires_at: datetime


class CarSnapshot(SQLModel, table=True):
    """Caché de MapBiomas, compartida entre productores."""

    car_code: str = Field(primary_key=True)
    summary_json: dict = Field(sa_column=Column(JSON, nullable=False))
    detail_json: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    fetched_at: datetime = Field(default_factory=utcnow)


class CarIndicatorsSnapshot(SQLModel, table=True):
    """Caché de indicadores por CAR (feature 003, research R5). Tabla nueva: sin migración."""

    __tablename__ = "car_indicators_snapshot"

    car_code: str = Field(primary_key=True)
    payload: dict = Field(sa_column=Column(JSON, nullable=False))
    fetched_at: datetime = Field(default_factory=utcnow)


class SinaflorCar(SQLModel, table=True):
    """Resumen por CAR del POA Amazônia Legal (IBAMA/SINAFLOR), reemplazado en cada sync."""

    __tablename__ = "sinaflor_car"

    car_code: str = Field(primary_key=True)
    autorizacoes: int
    vigentes: int
    volume_m3: float
    ultima_emissao: date | None = None


class SinaflorSync(SQLModel, table=True):
    """Fila única (id=1). Si no existe, SINAFLOR nunca se sincronizó → "indisponível"."""

    __tablename__ = "sinaflor_sync"

    id: int = Field(default=1, primary_key=True)
    synced_at: datetime = Field(default_factory=utcnow)
    source_last_modified: str | None = None
    rows: int = 0
