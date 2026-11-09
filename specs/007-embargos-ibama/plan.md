# Implementation Plan: Embargos del IBAMA como respaldo cuando MapBiomas no los determina

**Branch**: `006-regras-nivel` (misma rama, a pedido de la responsable) | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/007-embargos-ibama/spec.md`

## Summary

Cuando MapBiomas no puede determinar los embargos de un CAR (hoy: todos los CARs sin alertas, porque
`pointInformation` responde 500), el backend consulta la capa pública de áreas embargadas del IBAMA
con el polígono del CAR, cuenta los embargos que se superponen ≥ 0,1 ha (todos vigentes) y los entrega
con el mismo esquema `Embargo`. La regla de nivel (`level_rules.py`) no cambia: recibe embargos
verificados en lugar de "indisponível". El detalle del CAR muestra la fuente, la fecha y la
superposición, y "Entenda o nível" explica el respaldo.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / React 19 (frontend)
**Primary Dependencies**: FastAPI, httpx, shapely, SQLModel (ya presentes; sin dependencias nuevas)
**Storage**: SQLite: caché existente `CarSnapshot.detail_json` (sin tablas nuevas)
**Testing**: pytest + respx (`FakeIbama` en `conftest.py`), Vitest
**Target Platform**: servidor web local / Linux
**Project Type**: web (backend + frontend)
**Performance Goals**: consulta al IBAMA ~0,3 s; solo cuando MapBiomas falla
**Constraints**: timeout 5 s; sin datos personales; sin red en tests
**Scale/Scope**: 1 fuente nueva, ~6 archivos de backend, ~4 de frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Evaluación |
|---|---|
| I. Fuentes externas solo desde el servidor | ✅ El IBAMA se consulta solo en `app/sources/ibama.py`; capa pública sin credenciales. El frontend no la llama. |
| II. Tolerancia a fallos | ✅ Timeout 5 s; resultado en la caché del CAR con fecha (`embargoes_checked_at`); si falla se sirve la caché anterior con `embargoes_stale`; sin caché sigue "indisponível". Nunca 0 falso: respuesta truncada = no disponible. |
| III. Privacidad por agregación | ✅ `outFields` explícito sin `cpf_cnpj_embargado` ni `nome_embargado`; el esquema `Embargo` no tiene esos campos; la respuesta pública no cambia de forma. Tests de ambas cosas. |
| IV. Una sola fuente de verdad | ✅ La regla de nivel sigue solo en `level_rules.py`. Deduplicación en una función (`merge_embargo_items`) usada por ambas fuentes. Umbral 0,1 ha en una constante. |
| V. Simplicidad | ✅ Sin dependencias, tablas ni servicios nuevos; reutiliza `area_ha`, `car_polygon`, `SourceUnavailable` y el patrón de `inpe.py`. |
| VI. Calidad verificable | ✅ Tests sin red con respx para cada requisito de fallo y de privacidad. |
| VII. Fidelidad e idioma | ✅ Los datos del IBAMA se muestran como vienen (termo, proceso, fechas, área); lo derivado (superposición) indica base y fecha. UI en pt-BR, sin "ilegal"/"crime". |

**Resultado**: sin violaciones. Re-evaluado tras la fase 1 (data-model, contrato): sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/007-embargos-ibama/
├── spec.md
├── plan.md              # este archivo
├── research.md          # R1–R7
├── data-model.md
├── quickstart.md
├── contracts/openapi.yaml
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py                 # ibama_embargoes_url, ibama_timeout_s
│   ├── schemas.py                # Embargo.term/overlap_ha; CarSummary.embargoes_source/_checked_at/_stale
│   ├── sources/ibama.py          # NUEVO: consulta, superposición ≥ 0,1 ha, mapeo a Embargo
│   └── services/car_service.py   # merge_embargo_items; respaldo en build_detail; stale en get_detail
└── tests/
    ├── conftest.py               # FakeIbama (caído por defecto)
    ├── unit/test_ibama.py        # NUEVO: mapeo, umbral, dedupe, truncado, outFields
    └── integration/test_embargoes_ibama.py  # NUEVO: nivel, fallos, stale, privacidad
frontend/
└── src/
    ├── types.ts                  # campos nuevos
    ├── i18n/pt-BR.ts             # textos de fuente, ayuda, columnas y "Entenda o nível"
    ├── pages/CarDetailPage.tsx   # fuente + fecha + ayuda; columnas termo y área no CAR
    └── pages/LevelRulesPage.tsx  # (solo textos vía t.rules)
docs/arquitetura.md               # fuente nueva y su armadilha (pointInformation 500)
AGENTS.md                         # lista de features: 007
```

**Structure Decision**: web app existente (backend + frontend); la fuente nueva sigue el patrón de
`app/sources/` (como `inpe.py` y `sinaflor.py`).

## Complexity Tracking

Sin violaciones que justificar.
