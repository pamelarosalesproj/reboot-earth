# Implementation Plan: Panel del productor por CAR

**Branch**: `001-producer-car-dashboard` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-producer-car-dashboard/spec.md`

## Summary

Aplicación web mínima donde un productor se registra (email, contraseña, CNPJ, ≥1 CAR) y, al entrar, ve una tarjeta por CAR con el polígono en un mapa, el número de alertas de desmatamento y el número de embargos, más un detalle con alertas (y embargos superpuestos a cada alerta) y la lista de embargos del CAR. Una landing pública en `/` explica la plataforma y lleva al registro o al login; el panel vive en `/painel`.

Enfoque técnico: **backend Python (FastAPI)** que actúa de intermediario hacia la API GraphQL de MapBiomas Alerta, reutilizando la lógica ya probada en `mapbiomas_api.py` (polígono WKT→GeoJSON, alertas por CAR, embargos deduplicados por órgano + proceso). Guarda usuarios/CARs en **SQLite** y cachea las respuestas de MapBiomas 24 h. **Frontend TypeScript (React 19 + Vite)** con mapas **Leaflet** sobre teselas OpenStreetMap. Cada tarjeta pide sus datos por separado, así que el fallo de un CAR no bloquea los demás (FR-012).

## Technical Context

**Language/Version**: Python 3.12 (backend, gestionado con `uv`; ya instalado en la máquina); TypeScript 5.x sobre Node 24 (frontend)

**Primary Dependencies**: Backend: FastAPI, Uvicorn, SQLModel (SQLAlchemy), httpx, pwdlib[argon2], pydantic-settings. Frontend: React 19, Vite, react-router, Leaflet + react-leaflet

**Storage**: SQLite (archivo local `backend/data/app.db`): productores, CARs asociados, sesiones y caché de MapBiomas

**Testing**: Backend: pytest + respx (mock de MapBiomas) + TestClient de FastAPI. Frontend: Vitest + Testing Library

**Target Platform**: Desarrollo local (macOS); navegador de escritorio moderno; servidor Linux en un despliegue futuro

**Project Type**: Aplicación web (frontend + backend)

**Performance Goals**: Panel con ≤5 CARs completo en <10 s (SC-002). Con caché, cada tarjeta <1 s

**Constraints**: Credenciales de MapBiomas solo en el servidor (FR-017). Timeout de 20 s por consulta a MapBiomas; si falla, se sirve la caché antigua marcada como "desactualizada" o un estado "no disponible". La API de MapBiomas es inestable (el 2026-11-05 producción no respondía y staging devolvía 502)

**Scale/Scope**: MVP: decenas de productores, ~5 CARs cada uno, 5 pantallas (landing, registro, login, panel, detalle de CAR)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` sigue siendo la plantilla sin rellenar: no hay principios ratificados, así que no hay gates que evaluar. **PASS (vacío)**. Recomendación: ejecutar `/speckit-constitution` si se quieren fijar principios (p. ej. test-first, simplicidad) antes de `/speckit-tasks`.

Re-check post-diseño: sin cambios, **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/001-producer-car-dashboard/
├── plan.md              # Este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/
│   └── openapi.yaml     # Fase 1: API REST backend ↔ frontend
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── app/
│   ├── main.py              # App FastAPI, CORS, routers
│   ├── config.py            # Settings (.env: MAPBIOMAS_*, SECRET_KEY, DB)
│   ├── db.py                # Motor SQLite + sesión
│   ├── models.py            # Producer, ProducerCar, Session, CarSnapshot
│   ├── schemas.py           # Modelos de request/response (contrato)
│   ├── validators.py        # CNPJ (dígitos verificadores), formato CAR
│   ├── auth.py              # Hash de contraseñas, cookie de sesión, dependencia current_producer
│   ├── mapbiomas/
│   │   ├── client.py        # Cliente GraphQL async (login de servicio, re-login ante 401)
│   │   ├── queries.py       # Queries GraphQL (polígono, alertas, embargos)
│   │   └── geo.py           # WKT → GeoJSON, punto interior (portado de mapbiomas_api.py)
│   ├── services/
│   │   └── car_service.py   # Resumen/detalle de CAR + caché 24 h + deduplicación de embargos
│   └── routers/
│       ├── auth.py          # /api/auth/*
│       └── cars.py          # /api/cars/*
└── tests/
    ├── fixtures/            # Respuestas de MapBiomas grabadas (PE-2607505… completo)
    ├── unit/                # validators, geo, deduplicación
    └── integration/         # endpoints con MapBiomas mockeado

frontend/
├── package.json
├── vite.config.ts           # proxy /api → backend:8000
├── src/
│   ├── main.tsx
│   ├── api/client.ts        # fetch tipado según contracts/openapi.yaml
│   ├── types.ts
│   ├── pages/
│   │   ├── LandingPage.tsx  # Pública en "/": qué es, qué muestra por CAR, fuente, cómo empezar
│   │   ├── RegisterPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── CarDetailPage.tsx
│   └── components/
│       ├── CarCard.tsx      # Carga independiente; estados: cargando / ok / desactualizado / no disponible
│       ├── CarMap.tsx       # Leaflet GeoJSON + fitBounds
│       └── CarInput.tsx     # Lista dinámica de CARs con validación de formato
└── tests/
```

**Structure Decision**: aplicación web con `backend/` y `frontend/` en la raíz. Los scripts existentes (`mapbiomas_api.py`, `dof_ibama.py`) se quedan como herramientas de exploración. La lógica necesaria se porta a `backend/app/mapbiomas/` (sin importar los scripts directamente) para poder hacerla async y testearla.

## Complexity Tracking

Sin violaciones de la constitución que justificar (constitución vacía).
