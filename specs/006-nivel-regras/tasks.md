# Tasks: Nueva regla de nivel por CAR y por CNPJ, y página "Entenda o nível"

**Input**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml)

**Tests**: incluidos (constitución VI).

## Phase 1: Foundational

- [X] T001 En `backend/app/schemas.py`: `Reason` y `CarsByLevel`; `Status` con `reasons`, `cars_by_level`, `eudr_attention` y `basis` += `"regras"` (según el contrato)
- [X] T002 [P] En `frontend/src/types.ts`: los mismos tipos

## Phase 2: US1 + US3 — Nivel por CAR y sello EUDR (P1/P2)

- [X] T003 [US1] `backend/tests/unit/test_level_rules.py`: un caso por criterio de FR-601 (embargo vigente, TI/UC integral, RL/APP ≥ 1 % y < 1 %, área desconocida, DETER grave y degradación dentro y fuera de 24 meses, alerta abierta, superadas → Gold, datos parciales, sin detalle → Sem dados), no penalización por INPE/SINAFLOR caídos (FR-603), todos los motivos presentes (FR-602) y EUDR (true con autorizada post-2020, null sin datos)
- [X] T004 [US1] `backend/app/services/level_rules.py`: `car_level(detail, indicators, today)` puro
- [X] T005 [US1] `backend/app/services/cnpj_report.py`: `car_inputs()` (detalle + indicadores en paralelo) y `car_status` usando `car_level`; `backend/app/routers/cars.py` (summary/detail) con indicadores. Actualizar `backend/tests/integration/test_car_status.py`

## Phase 3: US2 — Nivel del CNPJ (P1)

- [X] T006 [US2] Tests de `cnpj_level` en `test_level_rules.py` (peor CAR, Sem dados + Gold → Silver, ninguno con datos, not_registered/no_properties, `cars` por motivo) y actualizar `backend/tests/integration/test_public_status_levels.py` y `backend/tests/unit/test_cnpj_status.py` (se elimina con `compute_status`)
- [X] T007 [US2] `cnpj_level()` en `level_rules.py`; `cnpj_status()` en `cnpj_report.py`; usarlo en `routers/dashboard.py`, `build_public_report` y `reports/__init__.py`. Eliminar `compute_status`

## Phase 4: US4 — Interfaz y "Entenda o nível" (P2)

- [X] T008 [US4] `frontend/src/i18n/pt-BR.ts` y `frontend/src/lib/status.ts`: textos de los motivos con números, CARs por nivel, EUDR, aviso de fuentes (FR-610) y la página
- [X] T009 [US4] `frontend/src/components/StatusBadge.tsx`: lista de motivos, sello EUDR (también en compacto) y enlace "Entenda o nível" (prop `learnMore`, solo en el panel)
- [X] T010 [US4] `frontend/src/pages/LevelRulesPage.tsx` (+ CSS), ruta `/painel/nivel` en `frontend/src/App.tsx` y opción en `frontend/src/layout/AppLayout.tsx`
- [X] T011 [US4] Tests: `frontend/tests/StatusBadge.test.tsx` y `frontend/tests/LevelRulesPage.test.tsx`; ajustar los tests existentes

## Phase 5: Polish

- [X] T012 Actualizar `docs/arquitetura.md`, `AGENTS.md`, `docs/proposta-regras-nivel-e-agente.md` (implementada) y registrar el cambio en `specs/002-cnpj-score-search/spec.md`
- [X] T013 Gates (ruff, pytest, build, vitest) y validación en vivo; registrar los valores en `quickstart.md`
