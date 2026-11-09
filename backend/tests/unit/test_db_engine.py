from sqlalchemy.pool import NullPool

from app.db import engine


def test_engine_has_no_connection_limit():
    """Regresión: con un pool limitado, muchos CARs en paralelo colgaban el servidor."""
    assert isinstance(engine.pool, NullPool)
