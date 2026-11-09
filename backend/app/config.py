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

    # Configurações do Agente de IA (Consultor ESG)
    llm_api_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    llm_timeout_s: float = 10.0
    # Auditoria mensal NFs × CARs: desligada até haver fonte real de notas fiscais (hoje são simuladas).
    audit_enabled: bool = False

    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}"
    cache_ttl_hours: int = 24
    session_days: int = 7
    # En producción (HTTPS) debe ser True para que la cookie solo viaje cifrada.
    cookie_secure: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # Consulta pública por CNPJ (feature 002): límite por IP en ventana de 1 h.
    public_search_limit_per_hour: int = 30
    # Solo True detrás de un proxy de confianza: usa la 1ª IP de X-Forwarded-For como cliente.
    # Sin proxy, un visitante podría falsear la cabecera y saltarse el límite.
    trust_proxy_headers: bool = False

    # Indicadores del CAR (feature 003): fuentes públicas sin credenciales.
    inpe_wfs_url: str = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"
    inpe_fire_wfs_url: str = "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs"
    inpe_timeout_s: float = 3.0
    # Feature 007: áreas embargadas do IBAMA (Pamgia), respaldo quando o MapBiomas não dá os embargos.
    ibama_embargoes_url: str = (
        "https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/"
        "adm_embargos_ibama_a/FeatureServer/0/query"
    )
    ibama_timeout_s: float = 5.0
    # Feature 005: relatório do CNPJ de exemplo (escrito à mão), fora do repositório (backend/data é ignorado).
    mock_reports_dir: str = str(BACKEND_DIR / "data" / "mock_reports")
    sinaflor_poa_url: str = (
        "https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/dados/SINAFLOR/"
        "poaAmazoniaLegal/sinaflor-poa-amazonia-legal.csv"
    )


settings = Settings()
