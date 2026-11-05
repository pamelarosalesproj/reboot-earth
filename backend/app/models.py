"""Tablas persistidas (ver specs/001-producer-car-dashboard/data-model.md)."""

from datetime import datetime
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
