# Implementation Plan: Indicadores socioambientales en la tarjeta del CAR

**Branch**: `003-car-indicators` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-car-indicators/spec.md`

## Summary

Añadir a cada CAR un conjunto de indicadores, separado en "Riscos abertos" y "Contexto":
- alertas por situación legal;
- desmatamento después de 2020;
- reserva legal y APP;
- embargos;
- territorios;
- % de vegetación nativa;
- DETER;
- focos de calor;
- manejo forestal SINAFLOR.

Las fuentes son:
- **MapBiomas**: campos adicionales de la misma API.
- **INPE**: WFS público de TerraBrasilis, con intersección geométrica mediante `shapely`.
- **IBAMA**: sincronización diaria del CSV del POA a una tabla resumida.

El backend expone `GET /api/cars/{code}/indicators`, con caché de 24 h y fallos aislados por fuente. El frontend lo muestra en la tarjeta y en el detalle. La regla de niveles y la ficha pública no cambian.

## Technical Context

**Language/Version**: Python 3.12 / TypeScript 7 (sin cambios).

**Primary Dependencies**: las mismas, más **`shapely`** (backend; justificado en Complexity Tracking).

**Storage**: SQLite con 3 tablas **nuevas**: `car_indicators_snapshot`, `sinaflor_car` y `sinaflor_sync`. `create_all` las crea sin migración y no se modifica ninguna tabla existente.

**Testing**: pytest con MapBiomas simulado (`FakeMapBiomas` ampliado) y los WFS del INPE simulados con respx; vitest en el frontend.

**Target Platform**: la misma.

**Project Type**: aplicación web.

**Performance Goals**: menos de 3 s con caché (SC-306). Sin caché, de 2 a 8 consultas a fuentes externas en paralelo, con timeout de 30 s cada una.

**Constraints**: nunca 503 por una fuente externa; los tres estados distinguibles (valor, indisponível, não se aplica); sin la palabra "ilegal"; solo el dueño del CAR ve los indicadores.

**Scale/Scope**: 1 endpoint, 1 comando de sincronización y 2 componentes nuevos en el frontend, más cambios en la tarjeta y el detalle.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Cómo |
|---|---|---|
| I. Fuentes solo desde el servidor | ✅ | INPE e IBAMA se consultan desde el backend; el navegador solo llama a `/api/cars/{code}/indicators` |
| II. Tolerancia a fallos | ✅ | Timeout de 30 s, caché de 24 h por CAR, estado por fuente, `stale`, nunca 503, `null` en lugar de 0 cuando no hay dato (R5, FR-313) |
| III. Privacidad | ✅ | Endpoint autenticado con `own_car` (404 para un CAR ajeno); la ficha pública no cambia (FR-316/317) |
| IV. Una sola fuente de verdad | ✅ | `classify_alert` y `build_indicators` viven solo en `app/services/car_indicators.py`; la tarjeta y el detalle usan el mismo endpoint (R6) |
| V. Simplicidad | ⚠️ justificado | Una dependencia (`shapely`) y 3 tablas nuevas: ver Complexity Tracking |
| VI. Calidad verificable | ✅ | Todas las fuentes simuladas en los tests; hay tests de fallo por fuente y de autorización; existe quickstart |
| VII. Fidelidad e idioma | ✅ | Fuente y fecha en cada bloque; aviso en el % de vegetación; "Sem autorização registrada"; UI en pt-BR |
| Flujo · supuestos | ✅ | Sin supuestos nuevos de privacidad ni de alcance. La regla de niveles queda explícitamente fuera (FR-316) |

**Re-check post-diseño**: sin cambios. Las justificaciones del principio V siguen vigentes.

## Project Structure

### Documentation (this feature)

```text
specs/003-car-indicators/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/openapi.yaml
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                    # + shapely
├── app/
│   ├── config.py                     # + inpe_wfs_url, inpe_fire_wfs_url, inpe_timeout_s, sinaflor_poa_url
│   ├── models.py                     # + CarIndicatorsSnapshot, SinaflorCar, SinaflorSync
│   ├── schemas.py                    # + CarIndicators, AlertIndicator, SourceStatus…
│   ├── mapbiomas/queries.py          # + ALERT_INDICATORS_QUERY, JUDICIAL_ALERTS_QUERY
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── geo.py                    # NUEVO: area_ha, parse del polígono del CAR (shapely)
│   │   ├── inpe.py                   # NUEVO: biomes, prodes_loss, deter_by_class, hotspots_12m
│   │   └── sinaflor.py               # NUEVO: aggregate_csv, sync (CLI: python -m app.sources.sinaflor)
│   ├── services/car_indicators.py    # NUEVO: classify_alert, build_indicators, get_indicators (caché)
│   └── routers/cars.py               # + GET /{car_code}/indicators
└── tests/
    ├── fixtures/sinaflor_poa_sample.csv
    ├── unit/test_classify_alert.py · test_inpe_geo.py · test_sinaflor_aggregate.py
    └── integration/test_indicators.py

frontend/src/
├── types.ts · api/client.ts · i18n/pt-BR.ts
├── components/IndicatorValue.tsx     # NUEVO: valor / indisponível / não se aplica
├── components/CarIndicators.tsx      # NUEVO: Riscos abertos + Contexto
├── components/CarCard.tsx            # añade <CarIndicators>
└── pages/CarDetailPage.tsx           # columnas por alerta
frontend/tests/CarIndicators.test.tsx
```

**Structure Decision**: un paquete nuevo, `app/sources/`, para las fuentes externas que no son MapBiomas (el cliente de MapBiomas sigue en `app/mapbiomas/`). La lógica de negocio va en un servicio propio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Dependencia `shapely` | Intersección, unión y punto en polígono para FR-309, FR-310 y FR-311 | El `INTERSECTS` del servidor devuelve los polígonos sin recortar (el área queda mal); unir capas a mano no es viable |
| Tablas `sinaflor_car` + `sinaflor_sync` | El IBAMA solo publica un CSV de unos 90 MB, sin consulta por CAR | Descargarlo en cada petición tarda minutos y supera el timeout; sin `sinaflor_sync` no se puede distinguir "0" de "sin sincronizar" |
| Tabla `car_indicators_snapshot` | Caché de 24 h con estado por fuente (constitución II) | Añadir una columna a `CarSnapshot` exigiría una migración (`create_all` no altera tablas existentes) |

## Riesgos

- **Fuentes del INPE lentas** (hasta 30 s por capa en el prototipo): se mitiga con la caché de 24 h y con consultas en paralelo. La primera visita a un CAR grande puede tardar.
- **SINAFLOR sin sincronizar**: la tarjeta muestra "indisponível" hasta que alguien ejecute el comando. Documentarlo en el README.
- **Situaciones no observadas en datos reales** (`autorizada`, `com_fiscalizacao` y `suspensa_judicial`): se prueban solo con datos simulados.
