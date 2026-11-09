# Implementation Plan: Relatório do CNPJ explicado pela IA a partir dos dados de cada CAR

**Branch**: `006-regras-nivel` (misma rama, a pedido de la responsable) | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/008-relatorio-ia/spec.md`

## Summary

`get_report` deja de enviar datos crudos a la IA. Arma, con los datos que ya calcula (detalle, indicadores,
nivel y motivos de cada CAR, y nivel del CNPJ), un JSON compacto con totales ya sumados y seudónimos en
lugar de códigos de CAR. Un prompt nuevo pide a la IA solo consolidar y explicar. La respuesta se valida
(formato, recorte a 3/3, vocabulario, números presentes en los datos, seudónimos existentes), se traducen
los seudónimos a los códigos reales y se guarda en una caché en memoria hasta que cambien los datos. Si
algo falla, se usa el texto por reglas, ahora con `origem="regras"`. El ejemplo escrito a mano solo vale en
modo demostración. El frontend muestra "Gerado por IA" arriba del relatório cuando corresponde.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / React 19 (frontend)
**Primary Dependencies**: FastAPI, httpx, pydantic (ya presentes; sin dependencias nuevas)
**Storage**: ninguna nueva; caché en memoria del proceso
**Testing**: pytest + respx (`FakeLlm`), Vitest
**Target Platform**: servidor web local / Linux
**Project Type**: web (backend + frontend)
**Performance Goals**: relatório desde caché al instante; generación con IA ≤ `LLM_TIMEOUT_S` (10 s)
**Constraints**: sin códigos de CAR ni CNPJ hacia la IA; nunca romper el Início; sin red en tests
**Scale/Scope**: hasta 40 imóveis por pedido; ~4 archivos de backend, ~3 de frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Evaluación |
|---|---|
| I. Fuentes externas solo desde el servidor | ✅ La IA se llama solo desde `app/reports/`; la clave sigue en el `.env`. |
| II. Tolerancia a fallos | ✅ Timeout configurable, un reintento, texto por reglas como respaldo; el Início nunca queda roto. Estados "indisponível" llegan como tales, nunca como 0. |
| III. Privacidad por agregación | ✅ La IA recibe datos agregados con seudónimos, sin CNPJ, sin códigos ni geometrías. El relatório sigue siendo solo para el productor autenticado. Test que lo verifica. |
| IV. Una sola fuente de verdad | ✅ Nivel y motivos de `level_rules`; datos de `car_inputs`. La IA no calcula ni decide el nivel. |
| V. Simplicidad | ✅ Sin dependencias ni tablas; caché en un diccionario. |
| VI. Calidad verificable | ✅ Tests sin red con el LLM simulado para cada fallo y para la privacidad. |
| VII. Fidelidad e idioma | ✅ Origen veraz del texto ("Gerado por IA" / por reglas / ejemplo) y fecha de los datos; números solo de los datos; pt-BR, sin "ilegal"/"crime". |

**Resultado**: sin violaciones. Re-evaluado tras la fase 1: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/008-relatorio-ia/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/openapi.yaml
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py               # report_demo_mode
│   ├── schemas.py              # CnpjReport.origem += "regras"
│   └── reports/
│       ├── __init__.py         # get_report: flujo nuevo, caché, validación, fallback "regras"
│       ├── facts.py            # NUEVO: build_report_facts, seudónimos, números permitidos (puro)
│       └── prompt.py           # NUEVO: prompt + PROMPT_VERSION
└── tests/
    ├── conftest.py             # FakeLlm + fixture autouse sin clave LLM
    ├── unit/test_report_facts.py           # NUEVO
    └── integration/test_dashboard_report.py  # actualizado + casos de IA
frontend/
└── src/
    ├── types.ts                # origem 'regras'
    ├── i18n/pt-BR.ts           # textos "Gerado por IA", regras, exemplo
    └── components/CnpjReportView.tsx  # aviso arriba
docs/arquitetura.md · docs/desenvolvimento.md · docs/proposta-agente.md · AGENTS.md · CLAUDE.md
```

**Structure Decision**: web app existente; el relatório sigue en `app/reports/`, separado en datos
(`facts.py`, puro y testeable), prompt (`prompt.py`) y orquestación (`__init__.py`).

## Complexity Tracking

Sin violaciones que justificar.
