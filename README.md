# RebootEarth – Panel del productor por CAR

Plataforma donde un productor rural se registra con email, CNPJ y uno o más CARs, y ve por cada CAR
el polígono en un mapa, las alertas de desmatamento y los embargos, con datos de **MapBiomas Alerta**.

- `backend/`: API en Python 3.12 (FastAPI + SQLite), intermediaria hacia MapBiomas Alerta.
- `frontend/`: SPA en TypeScript (React + Vite + Leaflet), con landing pública en `/` y panel en `/painel`.
- `specs/001-producer-car-dashboard/`: spec, plan, contrato (`contracts/openapi.yaml`) y tareas.
- `mapbiomas_api.py`, `dof_ibama.py`: scripts de exploración (no los usa la app).

## Requisitos

- [`uv`](https://docs.astral.sh/uv/) (instala Python 3.12 automáticamente)
- Node 24 y npm

## Configuración

`.env` en la raíz del repo (no se versiona):

```env
MAPBIOMAS_EMAIL=tu@email.com
MAPBIOMAS_PASSWORD=...
MAPBIOMAS_API_URL=https://plataforma.alerta.mapbiomas.org/api/v2/graphql
# Opcionales
# DATABASE_URL=sqlite:////ruta/absoluta/app.db   (por defecto backend/data/app.db)
# COOKIE_SECURE=true                              (obligatorio en producción con HTTPS)
# CORS_ORIGINS=["http://localhost:5173"]
```

Las credenciales de MapBiomas solo se usan en el backend; nunca llegan al navegador.

## Arranque

```bash
# Backend → http://localhost:8000 (docs interactivas en /docs)
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000

# Frontend → http://localhost:5173 (proxy /api → :8000)
cd frontend && npm install && npm run dev
```

## Tests

```bash
cd backend && uv run ruff check . && uv run pytest     # MapBiomas simulado
cd frontend && npm run build && npm test
```

Validación manual de extremo a extremo: [`specs/001-producer-car-dashboard/quickstart.md`](specs/001-producer-car-dashboard/quickstart.md).

## Comportamiento ante fallos de MapBiomas

- Timeout de 20 s por consulta. Los datos se cachean 24 h por CAR (botón "Atualizar" para forzar).
- Si MapBiomas no responde: se muestra la última consulta marcada como "desatualizado", o
  "dados indisponíveis" + "Tentar novamente" si nunca se consultó. Cada tarjeta es independiente.
- El registro (email, CNPJ y contraseña) no depende de MapBiomas. Los CARs se añaden después desde el panel;
  para eso sí se consulta MapBiomas, y si no responde se pide reintentar más tarde.
- Un CAR que MapBiomas no tiene registrado (sin alertas) se acepta y se marca como tal.
