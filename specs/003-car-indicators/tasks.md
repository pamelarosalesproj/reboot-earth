---

description: "Task list for feature 003-car-indicators"
---

# Tasks: Indicadores socioambientales en la tarjeta del CAR

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml), [quickstart.md](quickstart.md)

**Tests**: incluidos, porque la constitución VI exige tests de fallo por fuente y de autorización, con todas las fuentes simuladas.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Añadir `shapely>=2.0` a `dependencies` en `backend/pyproject.toml` y ejecutar `uv sync` (Complexity Tracking del plan)
- [X] T002 Añadir a `Settings` en `backend/app/config.py`:
  - `inpe_wfs_url = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"`
  - `inpe_fire_wfs_url = "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs"`
  - `inpe_timeout_s = 30.0`
  - `sinaflor_poa_url = "https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/dados/SINAFLOR/poaAmazoniaLegal/sinaflor-poa-amazonia-legal.csv"`

---

## Phase 2: Foundational

- [X] T003 En `backend/app/models.py`, añadir las tablas `CarIndicatorsSnapshot` (`car_code` PK, `payload` JSON, `fetched_at`), `SinaflorCar` (`car_code` PK, `autorizacoes`, `vigentes`, `volume_m3`, `ultima_emissao: date | None`) y `SinaflorSync` (`id` PK = 1, `synced_at`, `source_last_modified: str | None`, `rows`), según `data-model.md`
- [X] T004 En `backend/app/schemas.py`, añadir `SourceStatus`, `Count`, `Situacao` (Literal de 6 valores), `AlertIndicator`, `OpenRisks`, `Context` y `CarIndicators`, con los nombres de campo exactos de `contracts/openapi.yaml`
- [X] T005 [P] Crear `backend/app/sources/geo.py`:
  - `car_polygon(ewkt) -> BaseGeometry` (quitando `SRID=…;`);
  - `area_ha(geom) -> float`, con una aproximación equirectangular en la latitud del centroide (R3).
- [X] T006 [P] En `frontend/src/types.ts`, añadir los tipos de `CarIndicators` según el contrato; en `frontend/src/api/client.ts`, añadir `getIndicators(code, refresh?)`
- [X] T007 [P] Crear `frontend/src/components/IndicatorValue.tsx`: recibe `value: number | null`, `status: 'ok' | 'indisponivel' | 'nao_se_aplica'`, un `format` y una `unit`. Renderiza el valor formateado (también el 0), "Indisponível" o "Não se aplica", cada uno con su clase CSS (FR-313)

---

## Phase 3: User Story 1 - Riscos abertos (P1) 🎯 MVP

**Independent Test**: con MapBiomas simulado, un CAR con 3 alertas pendientes (2 tocando APP, 27 ha en reserva legal) y otro con alertas bajo embargo vigente muestran esos valores.

### Tests

- [X] T008 [P] [US1] Crear `backend/tests/unit/test_classify_alert.py`: un caso por cada fila de la tabla de prioridad de `data-model.md`, más los conflictos (suspendida y embargada → `suspensa_judicial`; embargada y autorizada con un embargo sin fin → `embargo_vigente`; autorizada y con acción → `autorizada`; embargos no determinables y cruce con embargo → `embargo_vigente`)
- [X] T009 [P] [US1] Crear `backend/tests/integration/test_indicators.py`. Ampliar `FakeMapBiomas` en `backend/tests/conftest.py` para responder a `AlertIndicators` y `SuspendedJudicial` a partir de un dict `alert_extra[alert_code]`, y simular los WFS del INPE con respx (respuestas vacías por defecto). Casos:
  - (a) el CAR de referencia → `alerts_by_status.pendente == {n: 3, ha: …}` y la suma por situación es igual al total;
  - (b) `post_2020` solo suma las alertas posteriores al 31/12/2020;
  - (c) `legal_reserve_ha` y `app_alerts` solo cuentan las alertas abiertas;
  - (d) el CAR de otro productor → 404;
  - (e) sin sesión → 401;
  - (f) MapBiomas caído sin caché → `sources.mapbiomas.status == "indisponivel"`, `open.*` null y 200;
  - (g) caché vencida y MapBiomas caído → `stale = true` con los valores anteriores.

### Implementation

- [X] T010 [US1] En `backend/app/mapbiomas/queries.py`, añadir `ALERT_INDICATORS_QUERY` (`$c: [ID!]`, con los campos de research R1) y `JUDICIAL_ALERTS_QUERY` (`$c: String!`)
- [X] T011 [US1] Crear `backend/app/services/car_indicators.py` con:
  - `classify_alert(raw, embargoes, embargoes_status, judicial_codes) -> Situacao` (FR-302);
  - `alert_indicator(raw, code) -> AlertIndicator`;
  - `mapbiomas_block(client, code, embargoes, emb_status)`, que devuelve `alerts`, `alerts_by_status` (siempre con las 6 claves), `open` y la parte MapBiomas de `context` (`embargoes_lifted`, `sustainable_use_*`).

  Los embargos se obtienen con el `get_detail` existente, que usa la caché de 001. Si la consulta judicial falla, se sigue sin ella y se registra en el log.
- [X] T012 [US1] En `backend/app/services/car_indicators.py`, añadir `get_indicators(db, client, code, refresh)`: caché `CarIndicatorsSnapshot` de 24 h; resuelve cada fuente por separado (`asyncio.gather` con `return_exceptions`); si una falla, reutiliza su bloque de la caché anterior con `stale` o la marca `indisponivel` (R5). Nunca propaga errores de las fuentes
- [X] T013 [US1] En `backend/app/routers/cars.py`, añadir `GET /{car_code}/indicators` con `response_model=CarIndicators`, `own_car` y `refresh: bool = False`
- [X] T014 [US1] En `frontend/src/i18n/pt-BR.ts`, añadir el bloque `indicators`: títulos "Riscos abertos" y "Contexto"; etiquetas de las 6 situaciones (`pendente` = "Sem autorização registrada"); "Desmatamento pós-2020", "Em reserva legal", "Alertas tocando APP", "Embargos vigentes", "Terra indígena" y "UC de proteção integral"; y la nota sobre el área de la alerta completa
- [X] T015 [US1] Crear `frontend/src/components/CarIndicators.tsx`: llama a `getIndicators` (con estado de carga y error propios, para no romper la tarjeta) y renderiza el bloque **Riscos abertos** con `IndicatorValue`: embargo vigente, sin autorización registrada, con fiscalización (n.º · ha), pós-2020, reserva legal, APP, embargos vigentes, tierra indígena y protección integral. Debajo, la fuente y la fecha (FR-315)
- [X] T016 [US1] En `frontend/src/components/CarCard.tsx`, insertar `<CarIndicators code=… />` debajo de los números actuales. Estilos en `frontend/src/index.css`
- [X] T017 [P] [US1] Crear `frontend/tests/CarIndicators.test.tsx` (con `fetch` simulado):
  - muestra "Sem autorização registrada" con n.º y ha;
  - un 0 se muestra como "0" y `indisponivel` como "Indisponível";
  - el texto no contiene "ilegal";
  - un error del endpoint no impide renderizar el resto.

**Checkpoint**: la tarjeta muestra los riscos abertos con datos de MapBiomas.

---

## Phase 4: User Story 2 - Contexto (P2)

**Independent Test**: un CAR de la Caatinga muestra "Não se aplica" en DETER y SINAFLOR; uno de la Amazonía muestra valores.

### Tests

- [X] T018 [P] [US2] Crear `backend/tests/unit/test_inpe_geo.py`:
  - dos polígonos de desmatamento superpuestos (en capas de biomas distintos) dentro de un CAR → el área cuenta una sola vez;
  - un foco dentro y otro fuera del polígono, y uno fuera de la ventana de 12 meses → `count == 1`;
  - la clase DETER `CS_GEOMETRICO` se agrega con su n.º, ha y última fecha.
- [X] T019 [P] [US2] Crear `backend/tests/fixtures/sinaflor_poa_sample.csv` (separado por `;`, con BOM, columnas reales del POA) y `backend/tests/unit/test_sinaflor_aggregate.py`:
  - filas repetidas de la misma (autorización, especie, producto) no suman dos veces;
  - la `,` decimal se normaliza;
  - `Lenha(st)` se excluye del volume_m3;
  - "Autorização Emitida" y "Autorização Retificada" cuentan como vigentes;
  - las filas sin CAR se ignoran.
- [X] T020 [P] [US2] En `backend/tests/integration/test_indicators.py`, añadir:
  - CAR de PE → `sources.deter.status == "nao_se_aplica"` y `sources.sinaflor.status == "nao_se_aplica"`;
  - CAR de MT sin sincronizar SINAFLOR → `sinaflor.status == "indisponivel"`; tras sincronizar el CSV de prueba → valores;
  - WFS del INPE caído (respx 500) → `prodes`, `deter` y `focos` `indisponivel`, con MapBiomas `ok` y 200.

### Implementation

- [X] T021 [US2] Crear `backend/app/sources/inpe.py`:
  - `async wfs(http, url, layer, bbox, cql=None, geom_name="geom")`, con las reglas de R2: WFS 1.1.0, orden longitud-latitud y el BBOX dentro del CQL cuando hay filtro;
  - `biomes(http, geom) -> set[str]`, a partir de `prodes-brasil-nb:biomas_brasil`;
  - `prodes_loss(http, geom, biomes) -> {remaining_pct, deforested_ha, by_year}`, con la unión de las capas `yearly_deforestation` y `accumulated_deforestation_*` de los biomas cruzados;
  - `deter_by_class(http, geom) -> {by_class}`, sobre `deter-amz:deter_amz` con `view_date >= '2021-01-01'`;
  - `hotspots_12m(http, geom, today) -> {count, by_month}`, sobre `bdqueimadas2:focos` con `eh_satelite_referencia = true`.

  Timeout `settings.inpe_timeout_s`; los errores se propagan como `SourceUnavailable`.
- [X] T022 [US2] Crear `backend/app/sources/sinaflor.py`:
  - `aggregate_csv(lines) -> dict[car, SinaflorCar]` (R4);
  - `sync(db, url=settings.sinaflor_poa_url)`, que descarga en streaming con httpx, reemplaza `sinaflor_car` y escribe `sinaflor_sync`;
  - `__main__` para el CLI `python -m app.sources.sinaflor`, que imprime cuántos CARs se cargaron;
  - `forest_management(db, code, uf)`, que devuelve el bloque o el estado (`nao_se_aplica` si la UF no está en la Amazônia Legal; `indisponivel` si no hay `SinaflorSync`).
- [X] T023 [US2] En `get_indicators` (`backend/app/services/car_indicators.py`), integrar PRODES, DETER (solo si `"Amazônia"` ∈ biomas; si no, `nao_se_aplica`), focos de calor y SINAFLOR como fuentes independientes. El polígono del CAR sale de la geometría de `get_detail`
- [X] T024 [US2] En `frontend/src/i18n/pt-BR.ts` y `frontend/src/components/CarIndicators.tsx`, añadir el bloque **Contexto**:
  - alertas superadas (autorizada, embargo levantado, suspensa judicial);
  - embargos levantados;
  - UC de uso sustentável con su nombre;
  - vegetação nativa (%) con el aviso de FR-309;
  - DETER por clase con las etiquetas de `data-model.md`, o "Não se aplica a este bioma";
  - focos de calor de 12 meses;
  - manejo forestal (autorizaciones, vigentes, m³), o "Não se aplica".
- [X] T025 [P] [US2] En `frontend/tests/CarIndicators.test.tsx`, añadir: "Não se aplica a este bioma" con DETER `nao_se_aplica`; "Corte seletivo – padrão de manejo" para `CS_GEOMETRICO`; el aviso del % de vegetación visible

---

## Phase 5: User Story 3 - Situación por alerta en el detalle (P2)

- [X] T026 [US3] En `frontend/src/pages/CarDetailPage.tsx`, obtener `getIndicators(code)` y añadir columnas a la tabla de alertas, cruzando por `alert_code`: Situação, Pós-2020, Reserva legal (ha), APP y UC. Si los indicadores no cargan, la tabla actual se muestra igual
- [X] T027 [P] [US3] Crear `frontend/tests/CarDetailIndicators.test.tsx`: una alerta con UC muestra el nombre del APA y su situación, y el detalle se renderiza aunque los indicadores fallen

---

## Phase 6: Polish

- [X] T028 [P] En `README.md`, añadir una sección "Indicadores do CAR" con las fuentes, el comando `uv run python -m app.sources.sinaflor` (ejecutarlo a diario, por ejemplo con cron), los estados (valor, indisponível, não se aplica) y las limitaciones (área de la alerta completa; PRODES no registra regeneración)
- [X] T029 Gates de la constitución: `cd backend && uv run ruff check . && uv run pytest` y `cd frontend && npm run build && npm test`
- [X] T030 Validación manual del `quickstart.md` §2 y §3 contra las fuentes reales con los 3 CARs de referencia, anotando las diferencias en el quickstart. ✅ 2026-11-06: validado por API con los servidores en marcha y la cuenta `qa-003@example.com`; los valores coinciden con el quickstart. No se revisó visualmente en el navegador.

---

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → Polish.
- US2 extiende `get_indicators` y `CarIndicators.tsx` de US1. US3 solo necesita el endpoint de US1.
- **Paralelizables**: T005, T006 y T007; los tests T008 y T009; T018, T019 y T020; T025 y T027.

## Implementation Strategy

MVP = Phases 1–3: la tarjeta con los riscos abertos, solo con MapBiomas. Después, el contexto (INPE + SINAFLOR) y, por último, el detalle por alerta.

## Notes

- Total: 30 tareas. Setup 2 · Foundational 5 · US1 10 · US2 8 · US3 2 · Polish 3.
