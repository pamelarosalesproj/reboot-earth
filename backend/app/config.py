"""Configuración leída del `.env` de la raíz del repo (y del entorno)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    mapbiomas_email: str = ""
    mapbiomas_password: str = ""
    mapbiomas_api_url: str = "https://plataforma.alerta.mapbiomas.org/api/v2/graphql"
    mapbiomas_timeout_s: float = 20.0

    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}"
    cache_ttl_hours: int = 24
    session_days: int = 7
    # En producción (HTTPS) debe ser True para que la cookie solo viaje cifrada.
    cookie_secure: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
