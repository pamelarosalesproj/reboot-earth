# Implementation Plan: Consulta pública de score por CNPJ

**Branch**: `002-cnpj-score-search` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-cnpj-score-search/spec.md`

## Summary

Añadir una búsqueda pública por CNPJ, sin sesión, para compradores. Devuelve una ficha agregada: nivel Gold / Silver / Bronze / Sem dados, score en estado "Em cálculo" y fecha de los datos. Nunca incluye códigos de CAR, mapas ni datos de la cuenta.

Técnicamente:
- La agregación que hoy vive en el endpoint del panel se extrae a un servicio compartido (`aggregate_cars`).
- Sobre ese servicio se añaden dos funciones puras: `compute_status`, con la regla provisional, y `get_score`, que hoy siempre devuelve "Em cálculo" y se podrá sustituir más adelante.
- Se expone `GET /api/public/cnpj/{cnpj}` con límite de búsquedas por IP. No hay cambios de esquema en la base de datos.
- El panel del productor muestra el mismo nivel y score, que salen del mismo código.
- En el frontend:
  - página pública "Consultar CNPJ" en `/consulta` y `/consulta/:cnpj`, también accesible dentro del panel en `/painel/consulta`;
  - pestaña "Consultar CNPJ" en la barra superior pública y en la barra lateral del panel;
  - en la landing, solo un botón "É comprador? Consulte o status do seu produtor", sin buscador;
  - un componente `StatusBadge`.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 7 / React 19 (frontend). Sin cambios respecto a 001.

**Primary Dependencies**: FastAPI, SQLModel, httpx (backend); React Router 7, Vite 8 (frontend). **Sin dependencias nuevas** (el rate limit es propio; research R6).

**Storage**: SQLite existente, **sin cambios de esquema**. El status se calcula sobre la caché `CarSnapshot` (TTL 24 h).

**Testing**: pytest con MapBiomas simulado (backend); vitest + Testing Library (frontend).

**Target Platform**: servidor Linux/macOS con un solo proceso uvicorn; navegadores modernos, móvil y escritorio.

**Project Type**: aplicación web (backend + frontend).

**Performance Goals**: ficha en menos de 3 s para el 95% de las búsquedas con caché (SC-102); el cálculo del status es O(CARs del CNPJ).

**Constraints**:
- Nunca devolver 503 por fallos de MapBiomas (FR-107).
- No exponer `car_code`, `geometry` ni `email` en la respuesta pública (FR-105).
- 30 búsquedas por hora por IP (FR-106).

**Scale/Scope**: decenas o cientos de productores, pocos CARs por CNPJ. 1 endpoint nuevo, 1 modificado, 2 rutas y 3 componentes de frontend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluado contra la [constitución v1.0.0](../../.specify/memory/constitution.md), ratificada el 2026-11-05.

| Principio | Estado | Cómo se cumple |
|---|---|---|
| **I.** Fuentes externas solo desde el servidor | ✅ | La ficha pública pasa por `GET /api/public/cnpj/{cnpj}`; el navegador nunca llama a MapBiomas; se reutiliza el cliente existente, que no registra credenciales |
| **II.** Tolerancia a fallos | ✅ | Reutiliza `get_detail` (timeout 20 s, caché 24 h con `fetched_at`, `stale`); un CAR sin datos no tumba la ficha; los conteos son `null` cuando no hay datos, nunca 0; el endpoint público nunca devuelve 503 (R5) |
| **III.** Privacidad por agregación | ✅ diseño · ⚠️ gate | `PublicCnpjReport` es un modelo propio con `additionalProperties: false`, más un test que recorre el JSON buscando `car_code`, `geometry`, `email` e `id` (R8). Rate limit de 30/h por IP (R6). El status del panel se calcula a nivel CNPJ, pero solo expone el nivel, nunca CARs de otras cuentas (R4). **Gate**: la visibilidad pública sin opt-in es un supuesto de privacidad y MUST confirmarse con el usuario antes de `/speckit-implement` (sección *Flujo de desarrollo*) |
| **IV.** Una sola fuente de verdad | ✅ | `aggregate_cars`, `compute_status` y `get_score` viven solo en `cnpj_report.py`; el dashboard deja de tener su propia agregación (R1); hay un test de paridad entre el panel y la ficha. La validación del CNPJ en el frontend (`lib/cnpj.ts`) está permitida por *Restricciones adicionales* (el frontend MAY validar y el backend siempre vuelve a validar), así que no es una regla de negocio duplicada |
| **V.** Simplicidad (YAGNI) | ✅ | Sin dependencias ni tablas nuevas. Status y score se calculan en el momento (R2, R3). **Corregido en el re-check**: se elimina el índice en `producer.cnpj` que se había propuesto (ver abajo). La limitación del rate limit en memoria está documentada en *Riesgos* |
| **VI.** Calidad verificable | ✅ | MapBiomas simulado en todos los tests; los gates ruff, pytest, build y vitest están en [quickstart.md](quickstart.md) §1; hay tests de fallo (MapBiomas caído con y sin caché) y de privacidad (claves prohibidas); existe `quickstart.md` |
| **VII.** Fidelidad de datos e idioma | ✅ | No se editan alertas ni embargos; la ficha indica `data_as_of`, `stale` y `status.basis`; el nivel provisional se presenta como tal (FR-112); la UI está en pt-BR y los artefactos en español |
| Restricciones · identificadores | ✅ | El CNPJ se valida y normaliza en el backend con el `normalize_cnpj` existente |
| Flujo · supuestos de alcance | ⚠️ gate | La regla provisional Gold / Silver / Bronze (FR-111a), incluida su consecuencia para CARs `not_in_mapbiomas` (R5), cambia el alcance y MUST confirmarse antes de implementar |

**Resultado**: el diseño cumple los principios I–VII. **No hay violaciones que justificar**, así que se puede pasar a `/speckit-tasks`.

Quedan **dos confirmaciones del usuario** que bloquean `/speckit-implement`, no la generación de tareas:
1. Visibilidad pública de todo CNPJ registrado, sin opt-in del productor.
2. La regla FR-111a, incluido que un CAR sin registro en MapBiomas impide llegar a Gold.

**Re-check post-diseño (Fase 1)**: se detectó una desviación del principio V. El índice en `producer.cnpj` no responde a ninguna necesidad demostrada: con cientos de productores, la búsqueda sin índice es instantánea, y además `create_all` no añade índices a una tabla que ya existe, así que habría hecho falta una migración. Se elimina del diseño (data-model, research R4 y estructura). El resto, sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/002-cnpj-score-search/
├── plan.md              # Este archivo
├── research.md          # Decisiones R1–R8
├── data-model.md        # Aggregate, Status, Score, PublicCnpjReport
├── quickstart.md        # Validación automática y manual
├── contracts/
│   └── openapi.yaml     # GET /api/public/cnpj/{cnpj} + cambio en /api/dashboard
├── checklists/
│   └── requirements.md
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py                 # + public_search_limit_per_hour, trust_proxy_headers
│   ├── schemas.py                # + Status, Score, PublicCnpjReport; DashboardSummary + cnpj_status/cnpj_score
│   ├── rate_limit.py             # NUEVO: ventana deslizante en memoria por IP (R6)
│   ├── services/
│   │   └── cnpj_report.py        # NUEVO: aggregate_cars, compute_status, get_score, build_cnpj_report
│   ├── routers/
│   │   ├── public.py             # NUEVO: GET /api/public/cnpj/{cnpj}
│   │   └── dashboard.py          # usa aggregate_cars; añade cnpj_status/cnpj_score
│   └── main.py                   # include_router(public.router)
└── tests/
    ├── unit/test_cnpj_status.py      # tabla de reglas de data-model.md
    ├── unit/test_rate_limit.py
    └── integration/test_public_cnpj.py  # 200/422/429, privacidad, MapBiomas caído, paridad con dashboard

frontend/
├── src/
│   ├── lib/cnpj.ts               # NUEVO: normalizar/validar/formatear (réplica de validators.py)
│   ├── api/client.ts             # + getPublicCnpj
│   ├── types.ts                  # + Status, Score, PublicCnpjReport
│   ├── i18n/pt-BR.ts             # textos de niveles, motivos, avisos
│   ├── components/
│   │   ├── StatusBadge.tsx       # NUEVO: nivel con color y texto
│   │   ├── CnpjSearch.tsx        # NUEVO: input + validación + navegación
│   │   └── CnpjReportCard.tsx    # NUEVO: ficha
│   ├── pages/
│   │   ├── PublicCnpjPage.tsx    # NUEVO: /consulta, /consulta/:cnpj y /painel/consulta
│   │   ├── LandingPage.tsx       # botón "É comprador?..." + sección "para quem compra" (sin buscador)
│   │   ├── HomePage.tsx          # StatusBadge + score del CNPJ
│   │   └── RegisterPage.tsx      # aviso de visibilidad pública
│   ├── layout/AppLayout.tsx      # + "Consultar CNPJ" en la barra lateral
│   └── App.tsx                   # rutas /consulta, /consulta/:cnpj, /painel/consulta(/:cnpj); pestaña en Header
└── tests/
    ├── cnpj.test.ts
    ├── StatusBadge.test.tsx
    └── PublicCnpjPage.test.tsx
```

**Structure Decision**: se mantiene la estructura web de 001 (`backend/app`, `frontend/src`). La lógica nueva va en un servicio propio (`cnpj_report.py`) para que el panel y la ficha pública dependan del mismo código.

## Riesgos y notas

- **Rate limit en memoria**: es válido solo con un proceso. Antes de escalar a varios workers o réplicas hay que moverlo a un almacén compartido (R6).
- **IP detrás de un proxy**: en desarrollo, todo llega desde el proxy de Vite (127.0.0.1), así que todos los visitantes comparten el límite. En producción hay que activar `trust_proxy_headers` solo si hay un proxy de confianza delante.
- **CAR `not_in_mapbiomas`**: impide llegar a Gold (R5). Pendiente de confirmar con el usuario.
- **MapBiomas caído (502 hoy)**: los CNPJs sin caché salen "Sem dados". Es el comportamiento correcto, pero conviene saberlo durante la demo.

## Complexity Tracking

Sin violaciones; no aplica.
