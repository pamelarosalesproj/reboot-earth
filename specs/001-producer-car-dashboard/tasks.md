---

description: "Task list for Panel del productor por CAR"
---

# Tasks: Panel del productor por CAR

**Input**: Design documents from `specs/001-producer-car-dashboard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: la spec no exige TDD, pero plan.md define pytest + respx y Vitest, y quickstart.md ejecuta `uv run pytest`. Por eso se incluye un conjunto **mínimo** de tests para la lógica crítica: validadores, conversión de geometría, deduplicación de embargos y endpoints con MapBiomas mockeado. No hay tests exhaustivos de UI.

**Organization**: tareas agrupadas por historia de usuario (US1–US4 de spec.md).

- **Cambio 2026-11-05 (pedido por el usuario)**: el registro pide solo email, CNPJ y contraseña; los CARs se añaden desde el panel (US4 sube a P1) y se puede quitar el último CAR. Se ajustaron T021, T024, T026, T041–T043 y los tests correspondientes; `CarInput.tsx` se sustituyó por `frontend/src/lib/car.ts` y un formulario de alta en `DashboardPage.tsx` con estado vacío.
- **Cambio 2026-11-05 (pedido por el usuario)**: nuevo inicio del panel con barra lateral (avatar con iniciales, email, CNPJ, "Início", "Meus CARs", "Sair") y números grandes (CARs, alertas únicas, embargos únicos). Backend: `GET /api/dashboard` en `backend/app/routers/dashboard.py` + `backend/tests/integration/test_dashboard.py`. Frontend: `frontend/src/layout/AppLayout.tsx`, `frontend/src/pages/HomePage.tsx`; las tarjetas pasan a `frontend/src/pages/CarsPage.tsx` en `/painel/cars` y el detalle a `/painel/cars/:code` (`/car/:code` redirige).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario a la que pertenece (US1…US4)
- Rutas relativas a la raíz del repo: `backend/app/`, `backend/tests/`, `frontend/src/`

## Contexto clave para quien implemente

- Referencia de lógica MapBiomas ya probada: `mapbiomas_api.py` (métodos `desmatamento_por_car`, `embargos_car`, `poligono_car`, funciones `wkt_to_geojson`, `_punto_interior`). **Portar**, no importar.
- Credenciales en `.env` de la raíz: `MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD`, `MAPBIOMAS_API_URL`. No exponer nunca al frontend (FR-017).
- Datos de prueba: `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0_completo.json` (CAR de referencia: 3 alertas 1571779/1581449/1580505, 0 embargos, 264,23 ha). CNPJ válido: `04.654.691/0001-06`; inválido: `04.654.691/0001-07`.
- Decisión R6 (confirmada): si `ruralProperty` devuelve `null`, el CAR **se acepta** con `mapbiomas_status = not_in_mapbiomas`.
- La API de MapBiomas es inestable: timeout de 20 s, y nunca bloquear una tarjeta por otra.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: inicialización de backend y frontend

- [X] T001 Crear `backend/pyproject.toml` (proyecto `rebootearth-backend`, `requires-python = ">=3.12"`) con dependencias `fastapi`, `uvicorn[standard]`, `sqlmodel`, `httpx`, `pwdlib[argon2]`, `pydantic-settings`, `email-validator` y grupo dev `pytest`, `pytest-asyncio`, `respx`, `ruff`; crear paquetes vacíos `backend/app/__init__.py`, `backend/app/mapbiomas/__init__.py`, `backend/app/services/__init__.py`, `backend/app/routers/__init__.py`, `backend/tests/__init__.py`, y ejecutar `cd backend && uv sync`
- [X] T002 [P] Crear el frontend con Vite React-TS en `frontend/` (`npm create vite@latest frontend -- --template react-ts`), añadir `react-router-dom`, `leaflet`, `react-leaflet`, `@types/leaflet` y, en dev, `vitest`, `@testing-library/react`, `jsdom`; añadir script `"test": "vitest run"` en `frontend/package.json`
- [X] T003 [P] Configurar `frontend/vite.config.ts` con `server.proxy: { '/api': 'http://localhost:8000' }` y `test.environment: 'jsdom'`
- [X] T004 [P] Añadir a `.gitignore` de la raíz: `backend/data/`, `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/`; crear `backend/data/.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: infraestructura que necesitan todas las historias

**⚠️ CRITICAL**: no empezar ninguna historia hasta completar esta fase

- [X] T005 Implementar `backend/app/config.py` con `pydantic-settings`: lee `../.env` (raíz del repo); campos `mapbiomas_email`, `mapbiomas_password`, `mapbiomas_api_url` (default `https://plataforma.alerta.mapbiomas.org/api/v2/graphql`), `secret_key`, `database_url` (default `sqlite:///./data/app.db`), `mapbiomas_timeout_s = 20`, `cache_ttl_hours = 24`, `session_days = 7`, `cors_origins = ["http://localhost:5173"]`
- [X] T006 Implementar `backend/app/db.py`: engine SQLModel desde `settings.database_url` (`check_same_thread=False`), `create_db_and_tables()` y dependencia `get_session()`
- [X] T007 Implementar en `backend/app/models.py` las 4 tablas de data-model.md: `Producer` (email "único, en minúsculas"; `password_hash`; `cnpj` "str(14) solo dígitos"; `created_at` UTC), `ProducerCar` (FK `producer_id` cascade; `car_code` en mayúsculas; `mapbiomas_status` enum `found` · `not_in_mapbiomas`; `added_at`; UniqueConstraint(`producer_id`, `car_code`)), `Session` (`token` PK, `producer_id`, `expires_at` = creación + 7 días), `CarSnapshot` (`car_code` PK, `summary_json`, `detail_json` nullable, `fetched_at`)
- [X] T008 [P] Implementar `backend/app/schemas.py` con modelos Pydantic idénticos a `components/schemas` de `contracts/openapi.yaml`: `RegisterRequest`, `LoginRequest`, `Me`, `ProducerCarOut`, `CarSummary`, `Alert`, `Embargo`, `CarDetail`, `ValidationErrorOut` (`detail`, `field`, `invalid_values`)
- [X] T009 [P] Portar a `backend/app/mapbiomas/geo.py` `wkt_to_geojson` y `_punto_interior` desde `mapbiomas_api.py`, más `parse_ewkt(ewkt) -> (srid, geojson_geometry)` que quita el prefijo `SRID=4674;`
- [X] T010 Implementar `backend/app/mapbiomas/client.py`: clase `MapBiomasClient` async con `httpx.AsyncClient(timeout=settings.mapbiomas_timeout_s)`, `execute(query, variables)` que lanza `MapBiomasError` ante errores GraphQL/HTTP y `MapBiomasUnavailable` ante timeout/5xx/conexión; login perezoso con la mutation `signIn` y token en memoria; ante un error de autenticación, re-login una vez y reintento; instancia única que expone `get_mapbiomas_client()` como dependencia FastAPI
- [X] T011 [P] Implementar `backend/app/mapbiomas/queries.py` con las cadenas GraphQL de research.md R4: `RURAL_PROPERTY_QUERY` (propertyCode, propertyType, carType, areaHa, stateAcronym, geomRuralProperty, alerts { alertCode detectedAt areaHa crossedRuralProperties(carCode: $code) { code alertAreaInCar } crossedEmbargoesTotal crossedEmbargoesIds crossedEmbargoesList }), `CAR_EMBARGOES_VIA_ALERTS_QUERY` y `CAR_EMBARGOES_VIA_POINT_QUERY` (copiados de `embargos_car` en `mapbiomas_api.py`, con los campos `EMBARGO_FIELDS`)
- [X] T012 Implementar `backend/app/auth.py`: `hash_password`/`verify_password` con `pwdlib` (Argon2), `create_session(db, producer) -> token` (`secrets.token_urlsafe(32)`), `set_session_cookie(response, token)` (cookie `session`, HttpOnly, SameSite=Lax, `max_age` 7 días), dependencia `current_producer` que lee la cookie, valida que no haya expirado y devuelve 401 si no hay sesión válida
- [X] T013 Implementar `backend/app/main.py`: app FastAPI, CORS con `settings.cors_origins` y `allow_credentials=True`, `create_db_and_tables()` en lifespan, registro de los routers `auth` y `cars` bajo `/api`, handler de `MapBiomasUnavailable` → 503 `{"detail": "MapBiomas Alerta no disponible, inténtalo más tarde"}`
- [X] T014 [P] Crear `frontend/src/types.ts` con los tipos TS de `contracts/openapi.yaml` (`Me`, `ProducerCar`, `CarSummary`, `Alert`, `Embargo`, `CarDetail`, `ApiValidationError`)
- [X] T015 [P] Crear `frontend/src/api/client.ts`: `apiFetch<T>(path, init)` con `credentials: 'include'` que lanza `ApiError { status, body }` si la respuesta no es OK; funciones `register`, `login`, `logout`, `me`, `listCars`, `addCar`, `removeCar`, `getSummary(code, refresh?)`, `getDetail(code, refresh?)`
- [X] T016 [P] Crear `frontend/src/i18n/pt-BR.ts` con todos los textos de UI en portugués (labels, errores, "alertas", "embargos", "não determinável", "dados indisponíveis", "desatualizado", "Tentar novamente", "Atualizar") y los textos de la landing (título, subtítulo, qué se ve por CAR, fuente de datos, 3 pasos, botones "Cadastrar-se", "Entrar", "Ir para o painel")
- [X] T017 Crear `frontend/src/main.tsx` y `frontend/src/App.tsx` con rutas `/` (landing pública, US5), `/registro`, `/login`, `/painel` (panel, protegida), `/car/:code` (detalle, protegida), y un `AuthProvider` en `frontend/src/auth/AuthContext.tsx` que llama a `me()` al cargar, expone `producer | null` y, solo en rutas protegidas, redirige a `/login` en 401; importar `leaflet/dist/leaflet.css`
- [X] T018 [P] Crear `backend/tests/conftest.py`: BD SQLite en memoria, override de `get_session`, `TestClient`, fixture `mapbiomas_mock` con respx sobre `settings.mapbiomas_api_url` que responde `signIn` y devuelve el contenido de `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0_completo.json` (copiado a `backend/tests/fixtures/pe_2607505_completo.json`) para `ruralProperty`
- [X] T019 [P] Test unitario de `parse_ewkt`/`wkt_to_geojson` con el `geomRuralProperty` del fixture (MultiPolygon, coordenadas lon/lat) en `backend/tests/unit/test_geo.py`

**Checkpoint**: backend arranca (`uv run uvicorn app.main:app`), frontend arranca; `/painel` sin sesión redirige a `/login`

---

## Phase 3: User Story 1 - Registro del productor con sus CARs (Priority: P1) 🎯 MVP

**Goal**: un productor crea su cuenta con email, contraseña, CNPJ y ≥1 CAR verificado, inicia y cierra sesión.

**Independent Test**: registrar con `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` + CNPJ `04.654.691/0001-06`, cerrar sesión, volver a entrar y comprobar con `GET /api/auth/me` que el CAR está asociado (quickstart escenarios 1–5).

### Tests for User Story 1

- [X] T020 [P] [US1] Tests unitarios en `backend/tests/unit/test_validators.py`: CNPJ `04.654.691/0001-06` y `04654691000106` válidos → `"04654691000106"`; `04.654.691/0001-07` inválido; `11111111111111` inválido; menos de 14 dígitos inválido; CAR `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` válido (también en minúsculas → normaliza a mayúsculas); `PE-123` inválido
- [X] T021 [P] [US1] Tests de integración en `backend/tests/integration/test_auth.py` (con `mapbiomas_mock`): registro OK → 201 y cookie `session`; email duplicado → 409; CNPJ inválido → 422 con `field="cnpj"`; CAR mal formado → 422 con `field="car_codes"` e `invalid_values=["PE-123"]`; CAR repetido dos veces → se asocia una sola vez; login con contraseña errónea → 401 con mensaje genérico; logout → `/me` da 401; MapBiomas devuelve 503 → registro 503 sin crear la cuenta

### Implementation for User Story 1

- [X] T022 [P] [US1] Implementar `backend/app/validators.py`: `normalize_cnpj(value) -> str` (quita `.`, `/` y `-`; exige 14 dígitos; rechaza dígitos todos iguales; verifica DV con módulo 11, pesos `5,4,3,2,9,8,7,6,5,4,3,2` y `6,5,4,3,2,9,8,7,6,5,4,3,2`; resto <2 → 0, si no 11−resto) y `normalize_car(value) -> str` (mayúsculas, trim, regex `^[A-Z]{2}-\d{7}-[0-9A-F]{32}$`); ambos lanzan `ValueError` con mensaje
- [X] T023 [US1] Añadir a `backend/app/services/car_service.py` la función `verify_car_exists(client, code) -> Literal["found","not_in_mapbiomas"]`: ejecuta `RURAL_PROPERTY_QUERY` (basta con `propertyCode`); con datos → `found`; `null` → `not_in_mapbiomas` (decisión R6); `MapBiomasUnavailable` se propaga (→ 503)
- [X] T024 [US1] Implementar `backend/app/routers/auth.py` según `contracts/openapi.yaml`: `POST /auth/register` (valida email en minúsculas y único → 409; `password` minLength 8; CNPJ y cada CAR con `validators` → 422 `ValidationErrorOut` listando todos los CARs inválidos; deduplica `car_codes`; verifica cada CAR en paralelo con `asyncio.gather`; crea `Producer` + `ProducerCar` en una transacción; crea la sesión y la cookie; 201 `Me`), `POST /auth/login` (401 "Email ou senha inválidos" sin distinguir la causa), `POST /auth/logout` (borra la `Session`, limpia la cookie, 204), `GET /auth/me`
- [X] T025 [P] [US1] Crear `frontend/src/components/CarInput.tsx`: lista dinámica de campos CAR (añadir/quitar, mínimo 1), validación de formato en cliente con la misma regex y error resaltado por CAR, incluidos los `invalid_values` devueltos por el backend
- [X] T026 [US1] Crear `frontend/src/pages/RegisterPage.tsx`: formulario email, senha (≥8), CNPJ (máscara `00.000.000/0000-00` al escribir) y `CarInput`; muestra errores por campo a partir de `ApiValidationError.field`; 409 → mensaje con enlace a `/login`; 503 → "tente novamente mais tarde"; éxito → actualiza `AuthContext` y navega a `/painel`
- [X] T027 [P] [US1] Crear `frontend/src/pages/LoginPage.tsx`: email + senha, error genérico en 401, enlace a `/registro`, éxito → `/painel`; botón "Sair" en el layout de `frontend/src/App.tsx` que llama a `logout()`

**Checkpoint**: US1 funciona sola; `uv run pytest backend/tests/unit/test_validators.py backend/tests/integration/test_auth.py` en verde

---

## Phase 4: User Story 2 - Ver resumen de cada CAR al entrar (Priority: P1)

**Goal**: tras el login, una tarjeta por CAR con polígono, nº de alertas y nº de embargos, cada una cargada de forma independiente y con caché de 24 h.

**Independent Test**: con el CAR de referencia asociado, la tarjeta muestra el polígono encuadrado, "3 alertas", "0 embargos" y la fecha de obtención; si MapBiomas falla, la tarjeta muestra "indisponível" o "desatualizado" sin afectar a las demás (quickstart escenarios 6, 8, 9).

### Tests for User Story 2

- [X] T028 [P] [US2] Tests unitarios en `backend/tests/unit/test_embargo_dedup.py`: dos `embargoedAreas` con mismo (`source`, `processCode`) y distinto `code`/`description` → 1 embargo con 2 `descriptions`; distinto proceso → 2; `areaHa` sumada sin duplicar
- [X] T029 [P] [US2] Tests de integración en `backend/tests/integration/test_summary.py`: `GET /api/cars/{CAR ref}/summary` → `alerts_count=3`, `embargoes_count=0`, `embargoes_status="ok"`, `state="PE"`, `geometry.type="MultiPolygon"`, `stale=false`; segunda llamada no consulta MapBiomas (caché); `refresh=true` sí consulta; MapBiomas caído con snapshot antigua (>24 h) → 200 `stale=true`; MapBiomas caído sin snapshot → 503; CAR de otro productor → 404; sin sesión → 401

### Implementation for User Story 2

- [X] T030 [US2] Implementar en `backend/app/services/car_service.py` `dedupe_embargoes(rural_properties, car_code) -> list[Embargo]` (portado de `embargos_car` en `mapbiomas_api.py`: filtrar por `carCode == car_code`, agrupar por (`source`, `processCode`), juntar `description` en `descriptions` sin repetir, ordenar por `sourceRegisteredAt`) y `fetch_car_embargoes(client, code) -> (list[Embargo] | None, status)`: vía alertas; si no hay alertas, vía `pointInformation` con un bbox ±0.0001° alrededor de `_punto_interior`; si eso falla → `(None, "not_determinable")`
- [X] T031 [US2] Implementar en `backend/app/services/car_service.py` `build_summary(client, code) -> CarSummary`: ejecuta `RURAL_PROPERTY_QUERY` y `fetch_car_embargoes` en paralelo; `geometry` desde `parse_ewkt` (o `null`); `alerts_count = len(alerts)`; si `ruralProperty` es `null` → `alerts_count=0`, `geometry=null`, `embargoes_status="not_determinable"`; regla FR-011: `embargoes_count` solo es `0` si el estado es `ok`, en otro caso `null`
- [X] T032 [US2] Implementar en `backend/app/services/car_service.py` `get_summary(db, client, code, refresh) -> CarSummary` con caché `CarSnapshot`: si existe y `fetched_at` < 24 h y no `refresh` → devolverla; si no, `build_summary` y guardar; ante `MapBiomasUnavailable` → snapshot antigua con `stale=true`, o propagar (503) si no existe
- [X] T033 [US2] Implementar en `backend/app/routers/cars.py` `GET /cars` (CARs del productor) y `GET /cars/{car_code}/summary?refresh=` con la dependencia `current_producer`; 404 si el CAR no pertenece al productor (FR-006)
- [X] T034 [P] [US2] Crear `frontend/src/components/CarMap.tsx`: `MapContainer` de react-leaflet con teselas OSM (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` y atribución), capa `GeoJSON` con la geometría y `fitBounds` a sus límites al montar; sin geometría → aviso "polígono indisponível"
- [X] T035 [US2] Crear `frontend/src/components/CarCard.tsx`: llama a `getSummary(code)` de forma independiente; estados `loading` / `ok` / `stale` / `unavailable` según data-model.md; muestra código, UF, área (ha), `CarMap`, "N alertas", "N embargos" o "não determinável" (nunca vacío; `0` solo si es dato confirmado), "atualizado em <fecha>", botón "Atualizar" (`refresh=true`), "Tentar novamente" si `unavailable`, aviso si `stale`; enlace a `/car/:code`
- [X] T036 [US2] Crear `frontend/src/pages/DashboardPage.tsx`: `listCars()` y una `CarCard` por CAR en una grilla responsive; un fallo de una tarjeta no afecta a las demás (cada una gestiona su error)

**Checkpoint**: US1 + US2 funcionan; quickstart escenarios 6, 8, 9 y 11 pasan

---

## Phase 5: User Story 3 - Detalle de alertas y embargos por alerta (Priority: P2)

**Goal**: vista de detalle con la lista de alertas (con embargos superpuestos a cada una) y la lista de embargos del CAR.

**Independent Test**: abrir `/car/PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` → 3 alertas (1571779, 1581449, 1580505) con fecha, área en el CAR y "0 embargos" cada una; lista de embargos vacía (quickstart escenario 7).

### Tests for User Story 3

- [X] T037 [P] [US3] Tests de integración en `backend/tests/integration/test_detail.py`: `GET /api/cars/{CAR ref}/detail` → 3 alertas ordenadas por `detected_at` desc, `area_in_car_ha` = suma de `alertAreaInCar` del CAR, `embargoes_count=0` en cada una, `embargoes=[]`; alerta sintética con `crossedEmbargoesIds=[10,10,11]` → `embargoes_count=2`; CAR ajeno → 404

### Implementation for User Story 3

- [X] T038 [US3] Implementar en `backend/app/services/car_service.py` `build_detail(client, code) -> CarDetail` y `get_detail(db, client, code, refresh)` (misma política de caché que `get_summary`, guardada en `CarSnapshot.detail_json`). Por alerta: `area_in_car_ha` = suma de `crossedRuralProperties(carCode).alertAreaInCar`; `embargoes_count` según research R5: si `crossedEmbargoesList` trae órgano + proceso, deduplicar por esa clave; si no, `len(set(crossedEmbargoesIds or []))`; si los campos vienen `null` y `crossedEmbargoesTotal` es `null` → `None`. `embargoes` = `fetch_car_embargoes`
- [X] T039 [US3] Añadir `GET /cars/{car_code}/detail?refresh=` en `backend/app/routers/cars.py` (con `current_producer`, 404 si el CAR es ajeno)
- [X] T040 [US3] Crear `frontend/src/pages/CarDetailPage.tsx`: cabecera con el resumen y `CarMap` grande; tabla de alertas (código, data de detecção, área total ha, área no CAR ha, nº embargos); tabla de embargos (órgão, nº processo, área ha, data de registro, descrições); estados vacíos explícitos ("Nenhuma alerta", "Nenhum embargo"); botón "Voltar" a `/painel`

**Checkpoint**: US1–US3 funcionan de forma independiente

---

## Phase 6: User Story 4 - Gestionar los CARs de la cuenta (Priority: P3)

**Goal**: añadir y quitar CARs desde el panel, manteniendo al menos uno.

**Independent Test**: añadir un CAR → aparece su tarjeta; quitarlo → desaparece; intentar quitar el último → error (quickstart escenario 10).

### Tests for User Story 4

- [X] T041 [P] [US4] Tests de integración en `backend/tests/integration/test_manage_cars.py`: `POST /api/cars` válido → 201; repetido → 409; mal formado → 422; MapBiomas caído → 503; `DELETE` de un CAR con ≥2 → 204; `DELETE` del último → 409; `DELETE` de un CAR ajeno → 404

### Implementation for User Story 4

- [X] T042 [US4] Añadir en `backend/app/routers/cars.py` `POST /cars` (`normalize_car` → 422; ya asociado → 409; `verify_car_exists` → guarda `mapbiomas_status`; 201 `ProducerCarOut`) y `DELETE /cars/{car_code}` (404 si es ajeno; 409 "A conta deve ter pelo menos um CAR" si es el último; 204)
- [X] T043 [US4] En `frontend/src/pages/DashboardPage.tsx` añadir el formulario "Adicionar CAR" (reusa la validación de `CarInput`) y el botón "Remover" en cada `CarCard` (`frontend/src/components/CarCard.tsx`) con confirmación en línea (sin `window.confirm`), deshabilitado si solo queda un CAR; refrescar la lista tras cada acción

**Checkpoint**: todas las historias funcionan

---

## Phase 7: User Story 5 - Página inicial que explica la plataforma (Priority: P3)

**Goal**: landing pública en `/` que explica la plataforma y lleva al registro o al login.

**Independent Test**: abrir `http://localhost:5173/` sin sesión → explicación, 3 pasos, fuente MapBiomas, botones "Cadastrar-se" → `/registro` y "Entrar" → `/login`; con sesión → "Ir para o painel" → `/painel` (quickstart escenario 13). No depende de MapBiomas para mostrarse (FR-021); solo usa `me()` para decidir qué botones mostrar.

### Implementation for User Story 5

- [X] T044 [P] [US5] Crear `frontend/src/pages/LandingPage.tsx` con textos de `frontend/src/i18n/pt-BR.ts`: (1) hero con nombre "RebootEarth", subtítulo de una frase ("Acompanhe a situação ambiental dos seus imóveis rurais pelo CAR") y botones CTA; (2) sección "O que você vê por CAR" con 3 bloques: polígono do imóvel no mapa, alertas de desmatamento, embargos (IBAMA, ICMBio, órgãos estaduais); (3) sección "Como funciona" con 3 pasos numerados: cadastre-se com email, CNPJ e seus CARs → entre na plataforma → veja o painel de cada CAR; (4) sección "De onde vêm os dados" que explica que la información proviene de MapBiomas Alerta, con enlace a `https://alerta.mapbiomas.org`; (5) pie con el CTA repetido. CTA según `AuthContext`: sin sesión, "Cadastrar-se" (`/registro`) y "Entrar" (`/login`); con sesión, "Ir para o painel" (`/painel`). Sin llamadas a MapBiomas. Imagen del hero: `frontend/src/assets/hero.jpg` (versión optimizada de `imagen.jpeg` de la raíz, ~1600 px de ancho) como fondo con capa oscura para que el texto sea legible
- [X] T045 [P] [US5] Crear `frontend/src/pages/LandingPage.css`: una columna en móvil (<640 px) y 3 columnas para los bloques en escritorio; contraste legible; botones CTA bien visibles; importarlo desde `LandingPage.tsx`
- [X] T046 [US5] Test en `frontend/tests/LandingPage.test.tsx` (Vitest + Testing Library, `AuthContext` mockeado): sin sesión se muestran "Cadastrar-se" y "Entrar" con `href` `/registro` y `/login`; con sesión solo "Ir para o painel" con `href` `/painel`; aparece el texto "MapBiomas Alerta"

**Checkpoint**: landing navegable; todas las historias funcionan

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T047 [P] Logging estructurado en `backend/app/mapbiomas/client.py` (duración, query, éxito/error por consulta a MapBiomas, sin credenciales ni tokens) y en `backend/app/main.py`
- [X] T048 [P] Mostrar en `CarCard` el estado `not_in_mapbiomas` ("CAR sem registro no MapBiomas Alerta (sem alertas)") en `frontend/src/components/CarCard.tsx`
- [X] T049 [P] Crear `README.md` en la raíz con arranque de backend/frontend, variables de `.env` y enlace a `specs/001-producer-car-dashboard/quickstart.md`
- [X] T050 Revisión de seguridad: confirmar que ninguna respuesta ni log incluye `MAPBIOMAS_PASSWORD` ni el token de MapBiomas (FR-017), que `password_hash` nunca se serializa y que en producción se active `COOKIE_SECURE=true` (`backend/app/config.py`; no hace falta `secret_key` porque las sesiones son tokens aleatorios en BD)
- [X] T051 Ejecutar `cd backend && uv run ruff check . && uv run pytest` y `cd frontend && npm run build && npm test`; corregir fallos
- [ ] T052 ⚠️ PARCIAL (2026-11-05: MapBiomas no respondía; validados contra el backend real los escenarios 3, 4, 6, 7 con datos sembrados del CAR de referencia, 11 y 12, y el 503 sin crear cuenta; landing y registro revisados con capturas) Validación manual de los escenarios 1–13 de `specs/001-producer-car-dashboard/quickstart.md` contra MapBiomas real; si la API responde, buscar un CAR con embargos (`alerts(isInEmbargoedAlerta: true, limit: 5)`) y validar el conteo por alerta y la deduplicación (riesgo abierto de research R5)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (Phase 3)**: depende de Foundational
- **US2 (Phase 4)**: depende de Foundational. Para probarla por UI necesita login (US1); a nivel de API se prueba sola creando el productor en el fixture
- **US3 (Phase 5)**: reutiliza `fetch_car_embargoes` (T030) y `CarMap` (T034) de US2
- **US4 (Phase 6)**: reutiliza `verify_car_exists` (T023) de US1 y `DashboardPage`/`CarCard` de US2
- **US5 (Phase 7)**: depende solo de T016 (textos) y T017 (rutas y `AuthContext`); puede hacerse en paralelo con US1–US4
- **Polish (Phase 8)**: tras las historias deseadas

### Within Each User Story

- Tests → servicios → endpoints → UI
- Las tareas sobre `backend/app/services/car_service.py` (T023, T030, T031, T032, T038) y `backend/app/routers/cars.py` (T033, T039, T042) tocan el mismo archivo y son **secuenciales**

### Parallel Opportunities

- Setup: T002, T003, T004 en paralelo con T001
- Foundational: T008, T009, T011, T014, T015, T016, T018, T019 en paralelo; T010 → T012 → T013 en orden
- US1: T020, T021, T022 y T025 en paralelo; luego T023 → T024; T026/T027 en paralelo cuando exista T015
- US2: T028, T029 y T034 en paralelo con T030
- Backend (servicios/routers) y frontend (páginas/componentes) de una misma historia pueden avanzar en paralelo usando `contracts/openapi.yaml` como contrato

---

## Parallel Example: User Story 2

```bash
Task: "Tests de deduplicación en backend/tests/unit/test_embargo_dedup.py"            # T028
Task: "Tests de integración del summary en backend/tests/integration/test_summary.py" # T029
Task: "CarMap con Leaflet en frontend/src/components/CarMap.tsx"                     # T034
Task: "dedupe_embargoes + fetch_car_embargoes en backend/app/services/car_service.py" # T030
```

---

## Implementation Strategy

### MVP First

1. Phase 1 + Phase 2
2. Phase 3 (US1) + Phase 4 (US2): ambas son P1. US1 sola solo registra; el valor visible llega con US2
3. **STOP and VALIDATE**: quickstart escenarios 1–6, 8, 9, 11, 12
4. Demo

### Incremental Delivery

1. MVP (US1 + US2) → demo
2. US3 (detalle) → demo
3. US4 (gestión de CARs) → demo
4. US5 (landing) → demo
5. Polish + validación con un CAR con embargos

---

## Notes

- [P] = archivos distintos y sin dependencias pendientes
- Commit tras cada tarea o grupo lógico (el directorio aún no es un repo git: `git init` antes si se desea)
- No usar `window.alert`/`confirm`/`prompt` en el frontend
