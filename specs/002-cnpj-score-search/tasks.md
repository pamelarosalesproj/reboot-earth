---

description: "Task list for feature 002-cnpj-score-search"
---

# Tasks: Consulta pública de score por CNPJ

**Input**: Design documents from `/specs/002-cnpj-score-search/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml), [quickstart.md](quickstart.md)

**Tests**: se incluyen. La [constitución](../../.specify/memory/constitution.md), principio VI, exige tests automáticos para el comportamiento ante fallos (II) y la privacidad (III), y además MapBiomas simulado.

**Organization**: tareas agrupadas por user story (spec.md: US1 P1, US2 P1, US3 P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece (US1, US2, US3)

## Path Conventions

Aplicación web: `backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/tests/`.

**Convenciones de test existentes** (`backend/tests/conftest.py`):
- Los fixtures `client`, `engine` y `mapbiomas_mock` (un `FakeMapBiomas`) dan acceso a `.properties` (dict por código de CAR), `.embargoes` (dict de código a lista), `.down` (bool, simula un 502) y `.count(op)`.
- La función `register(client, email=..., cars=(REF_CAR,), cnpj=VALID_CNPJ)` crea un productor con CARs.
- Las constantes `REF_CAR`, `OTHER_CAR` y `VALID_CNPJ` vienen del mismo archivo.

---

## Phase 1: Setup

**Purpose**: gate de la constitución y configuración.

- [x] T001 **Gate (constitución, *Flujo de desarrollo*)**: confirmar con el usuario (a) que todo CNPJ registrado es consultable públicamente sin opt-in y (b) la regla FR-111a, incluido que un CAR `not_in_mapbiomas` impide llegar a Gold (research R5). Registrar las respuestas con fecha en la sección "Assumptions" de `specs/002-cnpj-score-search/spec.md`. **No empezar Phase 3 sin esto.** Si cambia la regla, actualizar antes `specs/002-cnpj-score-search/data-model.md` (tabla "Regla provisional"). ✅ Resuelto el 2026-11-05: (a) sí, por ahora; (b) sí, regla confirmada sin cambios
- [X] T002 Añadir a `Settings` en `backend/app/config.py`: `public_search_limit_per_hour: int = 30` y `trust_proxy_headers: bool = False`, con un comentario que explique que `trust_proxy_headers` solo se activa detrás de un proxy de confianza (plan, *Riesgos*)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: la agregación compartida, las reglas de nivel y score y los tipos que usan las tres stories (principio IV).

**⚠️ CRITICAL**: ninguna user story empieza antes de terminar esta fase.

### Backend

- [X] T003 Añadir a `backend/app/schemas.py` los modelos de `data-model.md` como `BaseModel` con `model_config = ConfigDict(extra="forbid")`:
  - `Status`: `level: Literal["gold","silver","bronze","sem_dados"]`, `reason: Literal["not_registered","no_properties","data_unavailable"] | None` ("solo con sem_dados"), `partial: bool`, `basis: Literal["provisional","score"]`.
  - `Score`: `state: Literal["em_calculo","nao_calculavel","disponivel"]`, `value: float | None`, `computed_at: datetime | None`, `method_version: str | None`.
  - `PublicCnpjReport`: `cnpj: str` (14 dígitos), `cnpj_formatted: str`, `registered: bool`, `status: Status`, `score: Score`, `cars_count: int`, `cars_with_data: int`, `stale: bool`, `data_as_of: datetime | None`.

  `PublicCnpjReport` MUST NOT reutilizar `CarSummary` ni `Me` (research R8).
- [X] T004 Crear `backend/app/services/cnpj_report.py` con:
  - un dataclass `CarsAggregate` con los campos de `data-model.md` §CarsAggregate;
  - una función pura `aggregate_cars(details: list[CarDetail | None], cars_count: int) -> CarsAggregate`, que mueve aquí, sin cambiarla, la lógica de `backend/app/routers/dashboard.py`. Reglas: alertas únicas por `alert_code`; embargos únicos por `(source, process_code)`, contados solo en CARs con `embargoes_status == "ok"`; `alerts_count` es `None` si ningún CAR tiene datos y `cars_count > 0`; `embargoes_count` es `None` si no hay CARs con embargos `ok` y `cars_count > 0`; `stale` y `oldest_fetched_at`.
- [X] T005 En `backend/app/services/cnpj_report.py`, añadir la función pura `compute_status(agg: CarsAggregate | None, registered: bool) -> Status`. Aplica la tabla de `data-model.md` §Status en orden; gana la primera que se cumple:
  1. no registrado → `sem_dados` / `not_registered`;
  2. `cars_count == 0` → `sem_dados` / `no_properties`;
  3. `cars_with_data == 0` → `sem_dados` / `data_unavailable`;
  4. `embargoes_count ≥ 1` → `bronze`;
  5. `alerts_count ≥ 1` o `partial` → `silver`;
  6. en otro caso → `gold`.

  `partial = cars_unavailable > 0 or cars_embargoes_unknown > 0`; `basis="provisional"`.
- [X] T006 En `backend/app/services/cnpj_report.py`, añadir `get_score(status: Status) -> Score`: si `status.level == "sem_dados"` devuelve `state="nao_calculavel"`; en otro caso `state="em_calculo"`. `value`, `computed_at` y `method_version` siempre `None`. Documentar en el docstring que es el punto que se sustituirá cuando exista el método (FR-110, research R3)
- [X] T007 En `backend/app/services/cnpj_report.py`, añadir `async def cnpj_aggregate(db: Session, client: MapBiomasClient, cnpj: str) -> tuple[bool, CarsAggregate | None]`:
  - `registered` es True si existe algún `Producer` con ese `cnpj` normalizado.
  - Los CARs son el conjunto sin repetir de `ProducerCar.car_code` de todos esos productores (research R4).
  - Obtiene cada detalle con `get_detail` en paralelo (una `Session(bind)` por CAR, como hoy en el dashboard), capturando `MapBiomasUnavailable` y `MapBiomasError` como `None`.
  - Devuelve `aggregate_cars(...)`. Nunca propaga errores de MapBiomas (principio II).
- [X] T008 Refactorizar `backend/app/routers/dashboard.py` para usar `aggregate_cars` de `cnpj_report.py`, eliminando la agregación inline y `_detail_or_none` si queda sin uso. La respuesta de `/api/dashboard` no cambia en esta tarea: `uv run pytest tests/integration/test_dashboard.py` MUST seguir pasando
- [X] T009 [P] Crear `backend/tests/unit/test_cnpj_status.py` con tests parametrizados de `compute_status` y `get_score` construyendo `CarsAggregate` a mano:
  - las 6 filas de la tabla de reglas;
  - Bronze con alertas y embargos a la vez;
  - Silver por `cars_unavailable=1` sin alertas;
  - Silver por `cars_embargoes_unknown=1` (caso CAR `not_in_mapbiomas`);
  - `score.state` correspondiente a cada nivel.
- [X] T010 [P] Crear `backend/tests/unit/test_aggregate_cars.py`:
  - una alerta compartida por dos CARs cuenta 1;
  - un embargo repetido (mismo `source` + `process_code`) cuenta 1;
  - un CAR con `embargoes_status="not_determinable"` no suma embargos y sí suma `cars_embargoes_unknown`;
  - todos `None` → `alerts_count is None` (nunca 0, principio II).

### Frontend

- [X] T011 [P] Crear `frontend/src/lib/cnpj.ts` con `normalizeCnpj(value): string | null` (solo dígitos; exige 14, no todos iguales y los dos dígitos verificadores, como `normalize_cnpj` en `backend/app/validators.py`) y `formatCnpj(digits): string` (`00.000.000/0000-00`)
- [X] T012 [P] Crear `frontend/tests/cnpj.test.ts`: `04.654.691/0001-06` y `04654691000106` → `04654691000106`; `11.222.333/0001-81` válido; `11.222.333/0001-00` → `null`; `00000000000000` → `null`; 13 dígitos → `null`; `formatCnpj` correcto
- [X] T013 [P] Añadir a `frontend/src/types.ts` las interfaces `Status`, `Score` y `PublicCnpjReport`, idénticas a `contracts/openapi.yaml` (mismos nombres de campo y uniones literales)
- [X] T014 [P] Añadir a `frontend/src/i18n/pt-BR.ts` un bloque `status`:
  - etiquetas `gold: 'Gold'`, `silver: 'Silver'`, `bronze: 'Bronze'`, `sem_dados: 'Sem dados'`;
  - motivos: `not_registered: 'CNPJ não cadastrado na plataforma'`, `no_properties: 'Nenhuma propriedade informada'`, `data_unavailable: 'Dados indisponíveis'`;
  - estados del score: `em_calculo: 'Score em cálculo'`, `nao_calculavel: 'Score não calculável'`.

  Más un bloque `publicSearch` con los textos del buscador, del error de CNPJ inválido, del límite alcanzado (con minutos) y de "dados parciais: {x} de {y} propriedades"
- [X] T015 Crear `frontend/src/components/StatusBadge.tsx`: recibe `status: Status` y muestra el nivel con **texto y color** (no solo color; también legible sin color), más el motivo si es `sem_dados`. Estilos `.status-badge.gold|silver|bronze|sem_dados` en `frontend/src/index.css`

**Checkpoint**: las reglas y la agregación están testeadas, el dashboard funciona igual que antes y los tipos del frontend están listos.

---

## Phase 3: User Story 1 - El comprador consulta un CNPJ sin registrarse (Priority: P1) 🎯 MVP

**Goal**: cualquier visitante busca un CNPJ y ve la ficha agregada, sin datos privados.

**Independent Test**: sin sesión, buscar `04.654.691/0001-06` (registrado) y `11.222.333/0001-81` (no registrado). El primero muestra nivel, score y fecha; el segundo, "Sem dados" con el motivo "CNPJ não cadastrado na plataforma" (spec US1).

### Tests for User Story 1 ⚠️

> Escribirlos primero y verificar que fallan.

- [X] T016 [P] [US1] Crear `backend/tests/integration/test_public_cnpj.py` con:
  - (a) un CNPJ registrado (`register(client)`, sin cookie después: usar un `TestClient` nuevo o borrar las cookies) → 200, con `registered=true`, `cars_count=1` y `score.state="em_calculo"`;
  - (b) `11222333000181` → 200, con `registered=false` y `status={level:"sem_dados", reason:"not_registered"}`;
  - (c) `11222333000100` → 422 con `field="cnpj"`;
  - (d) `04.654.691%2F0001-06` y `04654691000106` → mismo JSON;
  - (e) un productor registrado con `cars=()` → `sem_dados` / `no_properties` y `score.state="nao_calculavel"`;
  - (f) dos cuentas con el mismo CNPJ y el mismo `REF_CAR`, más `OTHER_CAR` en una de ellas → `cars_count=2`.
- [X] T017 [P] [US1] En `backend/tests/integration/test_public_cnpj.py`, añadir los tests de privacidad (principio III, SC-104):
  - una función recursiva recorre el JSON de (a) y comprueba que no existe ninguna clave en `{"car_code","geometry","email","id","alerts","embargoes"}`;
  - el JSON tampoco contiene el string `REF_CAR` ni el email del productor.
- [X] T018 [P] [US1] En `backend/tests/integration/test_public_cnpj.py`, añadir los tests de fallo (principio II, SC-105):
  - (a) consulta con datos, luego `mapbiomas_mock.down = True` y caché vencida (forzar `fetched_at` antiguo en `CarSnapshot`) → 200 con `stale=true` y el mismo nivel;
  - (b) `down = True` sin caché previa → 200 con `sem_dados` / `data_unavailable`;
  - nunca 503.
- [X] T019 [P] [US1] Crear `backend/tests/unit/test_rate_limit.py`, que prueba el limitador con un reloj inyectado:
  - 30 llamadas permitidas;
  - la 31ª rechazada con `retry_after_s > 0`;
  - tras avanzar el reloj 3600 s, se vuelve a permitir;
  - las IPs distintas son independientes.

  Añadir también un test de integración en `backend/tests/integration/test_public_cnpj.py`: con `settings.public_search_limit_per_hour` parcheado a 2, la 3ª petición → 429 con la cabecera `Retry-After` y `retry_after_s` en el cuerpo.

### Implementation for User Story 1

- [X] T020 [US1] Crear `backend/app/rate_limit.py`:
  - clase `SlidingWindowLimiter(limit: int, window_s: int = 3600, clock=time.monotonic)` con `hit(key) -> int | None` (None si se permite; si no, segundos hasta el siguiente hueco) y `reset()`;
  - una instancia de módulo, más una dependencia FastAPI `public_search_limit(request)` que usa `request.client.host` o, si `settings.trust_proxy_headers`, la primera IP de `X-Forwarded-For`;
  - si se rechaza, lanza `HTTPException(429, detail={"detail": "Limite de consultas atingido. Tente novamente mais tarde.", "retry_after_s": n}, headers={"Retry-After": str(n)})` o devuelve una `JSONResponse` equivalente con el cuerpo plano del contrato.

  Documentar en el docstring la limitación de un solo proceso. Añadir en `backend/tests/conftest.py` un fixture `autouse` que llame a `reset()`
- [X] T021 [US1] En `backend/app/services/cnpj_report.py`, añadir `async def build_public_report(db, client, cnpj: str) -> PublicCnpjReport`, que combina `cnpj_aggregate` + `compute_status` + `get_score`. Cuando no hay CARs o no está registrado, `cars_count=0`, `cars_with_data=0`, `stale=false` y `data_as_of=None`. `cnpj_formatted` va en el formato `00.000.000/0000-00`
- [X] T022 [US1] Crear `backend/app/routers/public.py` con `router = APIRouter(prefix="/public", tags=["public"])` y `GET /cnpj/{cnpj}`:
  - sin `current_producer`, con la dependencia `public_search_limit`;
  - valida con `normalize_cnpj` (si `ValueError` → 422 `{"detail": "CNPJ inválido", "field": "cnpj", "invalid_values": []}`);
  - devuelve `build_public_report` con `response_model=PublicCnpjReport`.

  Registrar el router en `backend/app/main.py` (`app.include_router(public.router, prefix="/api")`)
- [X] T023 [P] [US1] Añadir `getPublicCnpj(cnpj: string)` en `frontend/src/api/client.ts` (`GET /api/public/cnpj/${enc(cnpj)}`). Debe funcionar sin sesión y exponer `retry_after_s` del cuerpo en el `ApiError` 429
- [X] T024 [P] [US1] Crear `frontend/src/components/CnpjSearch.tsx`:
  - un input con máscara opcional y un botón "Consultar";
  - valida con `normalizeCnpj` **antes** de navegar (si es inválido, muestra el error y no hace ninguna petición);
  - si es válido, `navigate(basePath + '/' + digits)`;
  - props: `basePath: '/consulta' | '/painel/consulta'` (por defecto `'/consulta'`) e `initialValue` opcional.
- [X] T025 [US1] Crear `frontend/src/components/CnpjReportCard.tsx`: recibe `PublicCnpjReport` y muestra `cnpj_formatted`, `StatusBadge`, el estado del score (texto de i18n), "{cars_count} propriedades informadas pelo produtor" y "Dados de {data_as_of}" (más la marca "desatualizado" si `stale`). Para `not_registered`, añade el texto de que la ausencia no indica ni riesgo ni ausencia de riesgo. **No** muestra mapa, códigos de CAR ni email
- [X] T026 [US1] Crear `frontend/src/pages/PublicCnpjPage.tsx` (página "Consultar CNPJ"):
  - título "Consultar CNPJ" y una frase "Veja o status socioambiental de um produtor, sem cadastro";
  - siempre `CnpjSearch`;
  - con un `:cnpj` válido, llama a `getPublicCnpj` y muestra un estado de carga, `CnpjReportCard`, el error 422 o el mensaje 429 con los minutos;
  - prop `basePath`, que se pasa a `CnpjSearch`.

  Añadir en `frontend/src/App.tsx`:
  - las rutas públicas `/consulta` y `/consulta/:cnpj`, fuera de `RequireAuth`;
  - dentro de `/painel`, las rutas hijas `consulta` y `consulta/:cnpj`, que renderizan la misma página con `basePath="/painel/consulta"`.
- [X] T027 [US1] En `frontend/src/pages/LandingPage.tsx`, `frontend/src/pages/LandingPage.css` y `frontend/src/i18n/pt-BR.ts`, implementar FR-115. **La landing NO lleva buscador** (FR-101):
  - en el hero, junto a los accesos de productor, un botón destacado (un `Link` estilizado como botón secundario) "É comprador? Consulte o status do seu produtor" que lleva a `/consulta`;
  - una sección "Para quem compra" que explique la consulta sin registro y los niveles Gold / Silver / Bronze / Sem dados, y termine con el mismo botón;
  - ajustar el subtítulo para que nombre a los dos públicos (productor y comprador).
- [X] T028 [US1] Pestaña "Consultar CNPJ" en los dos menús (FR-101):
  - en `frontend/src/App.tsx` (`Header` público), un `NavLink` "Consultar CNPJ" a `/consulta`, antes de "Entrar" / "Cadastrar-se", visible también con sesión activa;
  - en `frontend/src/layout/AppLayout.tsx`, un `NavLink` "Consultar CNPJ" a `/painel/consulta` después de "Meus CARs";
  - el texto `t.nav.search = 'Consultar CNPJ'` y `t.sidebar.search = 'Consultar CNPJ'` en `frontend/src/i18n/pt-BR.ts`.
- [X] T029 [US1] En `frontend/src/pages/RegisterPage.tsx` y `frontend/src/i18n/pt-BR.ts`, añadir bajo el campo CNPJ el aviso: "O resumo do seu CNPJ (nível e score) poderá ser consultado publicamente; códigos de CAR e mapas não." Ajustar el texto según la respuesta de T001
- [X] T030 [P] [US1] Crear `frontend/tests/PublicCnpjPage.test.tsx` (con `fetch` simulado):
  - un CNPJ inválido no llama a `fetch` y muestra el error;
  - una respuesta registrada muestra la etiqueta del nivel y "Score em cálculo", y no contiene "PE-" (ningún código de CAR);
  - `not_registered` muestra "CNPJ não cadastrado na plataforma";
  - 429 muestra el mensaje del límite.

  Además, en `frontend/tests/LandingPage.test.tsx`: la landing **no** contiene ningún input de CNPJ y el botón "É comprador? Consulte o status do seu produtor" apunta a `/consulta`. En `frontend/tests/AppLayout.test.tsx`: la barra lateral incluye "Consultar CNPJ" con enlace a `/painel/consulta`

**Checkpoint**: US1 completa. La búsqueda pública funciona sola y se puede hacer una demo con el quickstart §2.

---

## Phase 4: User Story 2 - Status Gold / Silver / Bronze / Sem dados (Priority: P1)

**Goal**: el nivel refleja los datos reales de punta a punta y el comprador entiende qué significa y que es provisional.

**Independent Test**: con MapBiomas simulado, CNPJs cuyos CARs tengan (a) 0 alertas y 0 embargos, (b) alertas sin embargos, (c) algún embargo y (d) ningún dato muestran Gold, Silver, Bronze y Sem dados respectivamente (spec US2).

### Tests for User Story 2 ⚠️

- [X] T031 [P] [US2] Crear `backend/tests/integration/test_public_status_levels.py`, que modifica `mapbiomas_mock` antes de la primera consulta:
  - Gold: vaciar `properties[REF_CAR]["alerts"]` y sin embargos;
  - Silver: el fixture tal cual, con alertas y sin embargos;
  - Bronze: `mapbiomas_mock.embargoes[REF_CAR] = [<un embargo con source y process_code>]`;
  - Sem dados: `down=True` sin caché;
  - Silver parcial: dos CARs, uno limpio y otro sin datos (por ejemplo, borrado de `properties` tras registrarlo y con `down` solo para ese código, o un CAR `not_in_mapbiomas`), con `status.partial=true`.

  Comprobar `status.level`, `status.basis="provisional"` y que nunca sale Gold con `partial=true`
- [X] T032 [P] [US2] Crear `frontend/tests/StatusBadge.test.tsx`: cada nivel renderiza su etiqueta de texto; `sem_dados` + `data_unavailable` muestra "Dados indisponíveis"; la explicación del nivel y el aviso provisional aparecen cuando `basis="provisional"`

### Implementation for User Story 2

- [X] T033 [US2] En `frontend/src/i18n/pt-BR.ts`, añadir `status.explain` con una frase por nivel:
  - Gold: "Sem alertas de desmatamento nem embargos nas propriedades informadas";
  - Silver: "Há alertas de desmatamento, ou parte dos dados não pôde ser verificada";
  - Bronze: "Há embargos registrados";
  - Sem dados: "Não há dados suficientes para avaliar".

  Añadir también `status.provisional`: "Indicador preliminar baseado apenas em alertas e embargos do MapBiomas Alerta; não é o score definitivo." (FR-112)
- [X] T034 [US2] En `frontend/src/components/StatusBadge.tsx`, mostrar debajo del nivel la explicación de `status.explain[level]` y, si `basis === "provisional"`, el aviso `status.provisional`
- [X] T035 [US2] En `frontend/src/components/CnpjReportCard.tsx`, mostrar "dados parciais: {cars_with_data} de {cars_count} propriedades" cuando `status.partial` sea true (edge case de datos parciales)

**Checkpoint**: US1 + US2 funcionan juntas. El nivel es correcto para todos los casos de la tabla y se explica al comprador.

---

## Phase 5: User Story 3 - El productor ve su propio score y cómo lo ve el comprador (Priority: P2)

**Goal**: el panel "Início" muestra el mismo nivel y score que la ficha pública de su CNPJ (FR-114, SC-106).

**Independent Test**: iniciar sesión como productor y comparar el nivel y el score de "Início" con `/consulta/{cnpj}` abierta en una ventana privada: coinciden (spec US3).

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] En `backend/tests/integration/test_dashboard.py`, añadir tests de paridad (principio IV):
  - para un productor con CARs, `GET /api/dashboard` → `cnpj_status` y `cnpj_score` son iguales a `status` y `score` de `GET /api/public/cnpj/{cnpj}`;
  - repetirlo tras `DELETE /api/cars/{REF_CAR}` (cambia a `sem_dados`/`no_properties`);
  - con una segunda cuenta del mismo CNPJ que tiene `OTHER_CAR`, el `cnpj_status` del panel considera los dos CARs, mientras que `cars_count` del panel sigue siendo el de la cuenta (research R4).

### Implementation for User Story 3

- [X] T037 [US3] En `backend/app/schemas.py`, añadir a `DashboardSummary` `cnpj_status: Status` y `cnpj_score: Score`. En `backend/app/routers/dashboard.py`, calcularlos con `cnpj_aggregate(db, client, producer.cnpj)` + `compute_status(agg, registered=True)` + `get_score`, reutilizando el mismo código que la ruta pública (sin duplicar ninguna regla)
- [X] T038 [P] [US3] Añadir `cnpj_status: Status` y `cnpj_score: Score` a `DashboardSummary` en `frontend/src/types.ts`
- [X] T039 [US3] En `frontend/src/pages/HomePage.tsx` y `frontend/src/i18n/pt-BR.ts`, añadir una tarjeta "Como compradores veem seu CNPJ" con `StatusBadge` (`cnpj_status`), el texto del estado del score y un enlace "Ver ficha pública" a `/consulta/{cnpj}`
- [X] T040 [P] [US3] Crear `frontend/tests/HomePage.test.tsx` (con `fetch` simulado): la tarjeta muestra el nivel de `cnpj_status` y el enlace apunta a `/consulta/<cnpj del productor>`

**Checkpoint**: las tres stories funcionan y el panel y la ficha pública coinciden.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T041 [P] Actualizar `README.md`: los dos públicos (productor / comprador), la ruta `/consulta/:cnpj`, el endpoint `GET /api/public/cnpj/{cnpj}`, las variables `PUBLIC_SEARCH_LIMIT_PER_HOUR` y `TRUST_PROXY_HEADERS` en el bloque `.env` y la limitación del rate limit con un solo proceso
- [X] T042 Ejecutar los gates de la constitución (principio VI): `cd backend && uv run ruff check . && uv run pytest` y `cd frontend && npm run build && npm test`. Todos MUST pasar
- [X] T043 Ejecutar la validación manual de `specs/002-cnpj-score-search/quickstart.md` §2 y §3 con los servidores levantados, y anotar en el §4 de ese archivo el nivel real obtenido con los CARs de ejemplo
- [X] T044 Re-check de la constitución al cerrar la feature (*Governance*): confirmar que existen y pasan los tests de privacidad (T017), de fallo (T018) y de paridad (T036), y marcar `specs/002-cnpj-score-search/checklists/requirements.md` como revisado. ✅ Tests verificados: `test_public_report_exposes_no_private_data`, `test_mapbiomas_down_*`, `test_dashboard_status_matches_public` y similares. El checklist no se modificó: `/speckit-implement` lo trata como solo lectura y ya estaba 16/16

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 bloquea el inicio de la Phase 3 (gate de supuestos). T002 no depende de nada.
- **Foundational (Phase 2)**: depende de T002 (solo para T020, más adelante). Bloquea todas las stories.
- **US1 (Phase 3)**: depende de la Phase 2 y de T001.
- **US2 (Phase 4)**: depende de la Phase 2. Sus tests de integración (T031) usan el endpoint de US1 (T022), y T035 modifica `CnpjReportCard` (T025). En la práctica va **después de US1**.
- **US3 (Phase 5)**: depende de la Phase 2. El test de paridad (T036) usa el endpoint de US1 (T022). La implementación backend (T037) es independiente de US1.
- **Polish (Phase 6)**: después de las stories elegidas.

### Within Each Phase

- T003 → T004 → T005 → T006 → T007 (mismo archivo o dependencia de tipos) → T008.
- T009 y T010 se pueden hacer en cuanto existan T004–T006.
- T011–T014 son independientes del backend y entre sí. T015 depende de T013 y T014.
- US1: tests T016–T019 primero → T020 → T021 → T022. En el frontend: T023, T024 → T025 → T026 → T027, T028, T029 → T030.
- US2: T031 y T032 primero → T033 → T034 → T035.
- US3: T036 primero → T037. T038 → T039.

### Parallel Opportunities

- Phase 2: el bloque de frontend (T011–T014) en paralelo con el de backend (T003–T010).
- US1: T016, T017, T018 y T019 (tests) en paralelo; T023 y T024 en paralelo con T020–T022.
- US2: T031 en paralelo con T032.
- US3: T038 en paralelo con T036 y T037.

---

## Parallel Example: User Story 1

```bash
# Tests de US1 a la vez (archivos o secciones distintas):
Task: "T016 tests 200/422/agregación en backend/tests/integration/test_public_cnpj.py"
Task: "T019 limitador en backend/tests/unit/test_rate_limit.py"

# Frontend mientras se hace el backend:
Task: "T023 getPublicCnpj en frontend/src/api/client.ts"
Task: "T024 CnpjSearch en frontend/src/components/CnpjSearch.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 (confirmaciones) + T002.
2. Phase 2 completa (el dashboard sigue igual: test de regresión).
3. Phase 3 (US1). **Parar y validar** con el quickstart §2: la búsqueda pública ya muestra un nivel correcto, porque `compute_status` es foundational.
4. Demo o despliegue.

### Incremental Delivery

1. Foundation → US1 (MVP: el comprador consulta y ve el nivel).
2. + US2: explicaciones, aviso provisional, datos parciales y validación de punta a punta de cada nivel.
3. + US3: el productor ve lo mismo que el comprador.
4. Polish: README, gates y re-check de la constitución.

---

## Notes

- **Total**: 44 tareas. Setup 2 · Foundational 13 · US1 15 · US2 5 · US3 5 · Polish 4.
- Cuando exista el método del score, solo cambia `get_score` (y `compute_status` pasa a `basis="score"`, FR-111b). El contrato y la UI no cambian (FR-110).
- Hacer un commit al terminar cada fase o grupo lógico.
