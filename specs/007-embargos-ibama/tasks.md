# Tasks: Embargos del IBAMA como respaldo cuando MapBiomas no los determina

**Input**: Design documents from `specs/007-embargos-ibama/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: incluidos: el principio VI exige un test automático por cada requisito de fallo y de privacidad.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Añadir `ibama_embargoes_url: str = "https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query"` e `ibama_timeout_s: float = 5.0` a `Settings` en backend/app/config.py
- [X] T002 Añadir `FakeIbama` a backend/tests/conftest.py (respx sobre `url__startswith="https://pamgia.ibama.gov.br/"`, POST): atributos `features: list[dict]` (GeoJSON), `down = True` por defecto (responde 500), `truncated = False` (añade `"exceededTransferLimit": true`), `calls: list[dict]` con los campos del form recibido; colgarlo de `mapbiomas_mock.ibama` y exponer el fixture `ibama`

## Phase 2: Foundational

- [X] T003 Ampliar `Embargo` en backend/app/schemas.py con `term: str | None = None` y `overlap_ha: float | None = None`; ampliar `CarSummary` con `embargoes_source: Literal["mapbiomas", "ibama"] | None = None`, `embargoes_checked_at: datetime | None = None` y `embargoes_stale: bool = False` (todos opcionales: las cachés viejas siguen siendo válidas)
- [X] T004 Refactorizar backend/app/services/car_service.py: extraer `merge_embargo_items(items: list[dict]) -> list[Embargo]` (clave `(source, process_code)` o `(source, "code:<id>")`; une descripciones; suma `overlap_ha` cuando hay) y hacer que `dedupe_embargoes` la use filtrando por `carCode`; los tests existentes de dedupe deben seguir pasando

## Phase 3: User Story 1 - Nivel correcto con embargos del IBAMA (P1) 🎯 MVP

**Goal**: un CAR sin alertas cuyo MapBiomas no da embargos obtiene los del IBAMA y su nivel deja de ser "dados parciais".
**Independent Test**: con MapBiomas sin embargos y `FakeIbama` encendido, el CAR es Gold sin áreas y Bronze con un área ≥ 0,1 ha.

### Tests

- [X] T005 [P] [US1] Tests unitarios en backend/tests/unit/test_ibama.py: mapeo feature→`Embargo` (`source="IBAMA"`, `term="<num_tad>/<serie_tad>"`, `registered_at` desde epoch ms, `expired_at=None`, `descriptions=[des_tad]`); superposición < 0,1 ha no cuenta y ≥ 0,1 ha sí, con `overlap_ha` redondeado; dos polígonos del mismo proceso cuentan una vez sumando `overlap_ha`; sin proceso se agrupa por termo; geometría del embargo inválida cuenta con `overlap_ha=None`; `exceededTransferLimit` → `SourceUnavailable`; HTTP 500 / `{"error":…}` / JSON inválido → `SourceUnavailable`; `outFields` enviado no contiene `cpf` ni `nome`
- [X] T006 [P] [US1] Tests de integración en backend/tests/integration/test_embargoes_ibama.py: (a) CAR sin alertas + MapBiomas falla embargos + IBAMA sin áreas → `embargoes_status="ok"`, `embargoes_source="ibama"`, `embargoes_count=0`, nivel Gold sin `DADOS_PARCIAIS`; (b) con un área que se superpone ≥ 0,1 ha → Bronze `EMBARGO_VIGENTE` n=1; (c) IBAMA caído → `unavailable` + `DADOS_PARCIAIS` (nunca 0); (d) MapBiomas da embargos → `FakeIbama.calls` vacío y `embargoes_source="mapbiomas"`; (e) refresh con ambas fuentes caídas y caché previa del IBAMA → embargos previos con `embargoes_stale=true` y la fecha anterior; (f) CAR sin polígono → no se llama al IBAMA

### Implementation

- [X] T007 [US1] Crear backend/app/sources/ibama.py: constante `IBAMA_MIN_OVERLAP_HA = 0.1`; `OUT_FIELDS = "num_tad,serie_tad,num_processo,dat_embargo,qtd_area_embargada,des_tad"`; función pura `embargoes_from_features(features, car_geom) -> list[Embargo]` (intersección con shapely, `area_ha`, umbral, mapeo y `merge_embargo_items`); `async fetch_embargoes(geometry: dict) -> list[Embargo]` que hace POST form (`f=geojson`, envolvente convexa simplificada en anillos ESRI, `inSR/outSR=4326`, `esriSpatialRelIntersects`, `returnGeometry=true`, `resultRecordCount=2000`) con `settings.ibama_timeout_s`, y lanza `SourceUnavailable` ante error HTTP, JSON inválido, `error` o `exceededTransferLimit`. Nunca pedir `cpf_cnpj_embargado` ni `nome_embargado`
- [X] T008 [US1] En `build_detail` de backend/app/services/car_service.py: si `fetch_car_embargoes` no da `"ok"` y hay geometría, llamar a `ibama.fetch_embargoes`; si responde → `status="ok"`, `embargoes_source="ibama"`; si `SourceUnavailable` → mantener el status de MapBiomas y loguear. Con MapBiomas ok → `embargoes_source="mapbiomas"`. `embargoes_checked_at=now` solo si `status="ok"`
- [X] T009 [US1] En `get_detail` de backend/app/services/car_service.py: si el detalle nuevo no tiene embargos `ok` pero la caché previa sí, copiar `embargoes`, `embargoes_count`, `embargoes_source`, `embargoes_checked_at` previos con `embargoes_status="ok"` y `embargoes_stale=True`
- [X] T010 [US1] Verificar que backend/app/services/level_rules.py no necesita cambios (usa `embargoes_status == "ok"` y `expired_at`) y que el test (a)/(b) de T006 pasa

**Checkpoint**: US1 funcional: los niveles del panel ya usan el respaldo.

## Phase 4: User Story 2 - Ver de dónde salen los embargos (P1)

**Goal**: el detalle del CAR muestra fuente, fecha, ayuda y columnas del IBAMA, sin datos personales.
**Independent Test**: con el IBAMA simulado, `/detail` trae los campos nuevos y la UI los muestra.

- [X] T011 [P] [US2] Ampliar tipos en frontend/src/types.ts: `Embargo.term?: string | null`, `Embargo.overlap_ha?: number | null`, `CarSummary.embargoes_source?: 'mapbiomas' | 'ibama' | null`, `embargoes_checked_at?: string | null`, `embargoes_stale?: boolean`
- [X] T012 [P] [US2] Textos pt-BR en frontend/src/i18n/pt-BR.ts (`detail`): `embargoesSource(fonte, data)`, nombres de fuente ("MapBiomas Alerta", "IBAMA – áreas embargadas"), `embargoesStale`, ayuda del IBAMA ("Cruzamento geográfico do polígono do imóvel com as áreas embargadas publicadas pelo IBAMA; contam as que se sobrepõem 0,1 ha ou mais. Não inclui ICMBio nem órgãos estaduais, e a camada não indica embargos levantados."), columnas `term` ("Termo") y `overlap` ("Área no CAR (ha)"); sin "ilegal"/"crime"
- [X] T013 [US2] En frontend/src/pages/CarDetailPage.tsx, sección de embargos: línea de fuente + fecha (+ aviso stale) con `Help` de frontend/src/components/CarIndicators.tsx cuando la fuente es IBAMA; columnas "Termo" y "Área no CAR (ha)" solo si algún embargo tiene `term`/`overlap_ha`
- [X] T014 [P] [US2] Test de privacidad en backend/tests/integration/test_embargoes_ibama.py: con `FakeIbama` devolviendo features que incluyen `cpf_cnpj_embargado` y `nome_embargado`, ni `/api/cars/{car}/detail` ni `/api/public/cnpj/{cnpj}` contienen esos valores ni esas claves
- [X] T015 [P] [US2] Test Vitest en frontend/src/pages/CarDetailPage.test.tsx (o el archivo de tests existente del detalle): con embargos del IBAMA se ve la fuente "IBAMA – áreas embargadas" y la columna "Área no CAR (ha)"

## Phase 5: User Story 3 - Ficha pública con el nivel corregido (P2)

**Goal**: la ficha pública usa el mismo nivel (sin cambios de forma).
**Independent Test**: CNPJ con CAR sin alertas + IBAMA sin áreas → nivel público Gold y sin listas.

- [X] T016 [US3] Test en backend/tests/integration/test_embargoes_ibama.py: `/api/public/cnpj/{cnpj}` devuelve el mismo nivel que `/api/dashboard` con el respaldo del IBAMA, y sin campos `embargoes`, `term` ni `overlap_ha`

## Phase 6: Polish & Cross-Cutting

- [X] T017 [P] Actualizar "Entenda o nível" en frontend/src/i18n/pt-BR.ts (`t.rules`): texto de "Embargo vigente" (fuentes y respaldo IBAMA ≥ 0,1 ha), "Dados parciais" (solo si tampoco responde el IBAMA) y una entrada en `sources` para "IBAMA – áreas embargadas"
- [X] T018 [P] Documentar en docs/arquitetura.md: fuente IBAMA (URL, parámetros, umbral, campos que no se piden), armadilha de `pointInformation` (500 en campos de embargo desde 2026-11-08), campos nuevos de `CarSummary`/`Embargo` y el `FakeIbama`
- [X] T019 [P] Añadir la feature `007-embargos-ibama` a la lista de features de AGENTS.md
- [X] T020 Correr los cuatro gates (`uv run ruff check .`, `uv run pytest`, `npm run build`, `npm test`) y reportar la salida
- [ ] T021 Validación manual de quickstart.md con datos reales (refresh de AM-1303304, PE-2600500, RO-1100205) — backend validado el 2026-11-08 con las fuentes reales (AM/PE/RO → `ok`/`ibama`/0; PA sigue con MapBiomas); falta revisar la interfaz en el navegador

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T004) → US1 (T005–T010) → US2 (T011–T015) → US3 (T016) → Polish.
- US2 y US3 dependen de US1 (necesitan los embargos del IBAMA en el detalle); US2 y US3 son
  independientes entre sí.
- Dentro de US1: T005/T006 (tests) antes de T007–T009; T008 depende de T007; T009 de T008.

## Parallel Example: User Story 2

```text
T011 types.ts   ║ T012 pt-BR.ts   ║ T014 test de privacidad (backend)
luego T013 CarDetailPage.tsx → T015 test Vitest
```

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): corrige el nivel de los CARs afectados en panel y ficha pública.
- Luego US2 (transparencia de la fuente, exigida por el principio VII antes de entregar) y US3 (test).
- Polish: textos de reglas, docs y gates. No hacer commit sin pedido explícito.
