from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# NullPool: cada Session abre y cierra su propia conexión SQLite. Con el QueuePool por defecto
# (5 + 10) las vistas que cargan varios CARs en paralelo (una Session por CAR con asyncio.gather)
# agotaban el pool; el checkout bloqueaba el event loop y el servidor entero se colgaba.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False},
                       poolclass=NullPool)


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Asegura tzinfo UTC (por si la BD devuelve fechas sin zona)."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def create_db_and_tables() -> None:
    from app import models  # noqa: F401  (registra las tablas)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
