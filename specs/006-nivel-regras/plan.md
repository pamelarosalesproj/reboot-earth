# Implementation Plan: Nueva regla de nivel por CAR y por CNPJ, y página "Entenda o nível"

**Branch**: `006-regras-nivel` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

- **Backend**: un módulo de funciones puras `services/level_rules.py` con `car_level(detail, indicators, today)` y `cnpj_level(car_levels, registered)`. Reemplaza a `compute_status` en todas las vistas: dashboard, "Meus CARs" y detalle, ficha pública e informe del CNPJ. `Status` agrega `reasons`, `cars_by_level` y `eudr_attention`; `basis` pasa a `"regras"`.
- **Frontend**: la explicación del nivel lista los motivos con números, el sello "Atenção EUDR" y un enlace a la página nueva `/painel/nivel` ("Entenda o nível"), que también se agrega al menú lateral.

## Technical Context

- **Stack**: el mismo. **Sin dependencias ni tablas nuevas.**
- **Entradas por CAR**: `get_detail` (001: embargos y área) y `get_indicators` (003: alertas por situación, RL/APP, TI/UC, DETER), ambos con caché de 24 h, consultados en paralelo con una sesión por CAR.
- **Testing**: pytest (unitarios de la regla y de integración con `FakeMapBiomas` y `FakeInpe`) y vitest.
- **Performance**: la ficha pública ahora consulta también los indicadores (caché de 24 h). Sin caché, la primera consulta tarda lo mismo que el Início (005).

## Constitution Check

| Principio | Estado | Cómo |
|---|---|---|
| I. Fuentes en el servidor | ✅ | Todo en el backend |
| II. Tolerancia a fallos | ✅ | MapBiomas caído sin caché → Sem dados. INPE/SINAFLOR caídos no penalizan. EUDR sin datos → `null` (indeterminado), nunca `false` |
| III. Privacidad | ✅ | `Status` solo lleva códigos de motivo, conteos, ha y % agregados. En el CNPJ, los motivos cuentan CARs (`cars`), no listan códigos. El test de privacidad de la ficha pública sigue vigente |
| IV. Una sola fuente de verdad | ✅ | Una sola función por nivel (CAR y CNPJ), reutilizada en todas las vistas. Situación de alertas = `classify_alert` (003) |
| V. Simplicidad | ✅ | Funciones puras sobre datos ya cacheados; sin persistir niveles |
| VI. Calidad | ✅ | Tests por criterio, de no penalización por fallas, de agregación del CNPJ, EUDR, privacidad y UI |
| VII. Fidelidad e idioma | ✅ | Motivos con números y fuentes; pt-BR; sin "ilegal"/"crime" |

## Project Structure

```text
backend/app/
├── schemas.py                    # Status: + reasons[], cars_by_level, eudr_attention; basis += "regras"
├── services/level_rules.py       # NUEVO: car_level(), cnpj_level() (puras), umbral 1 %, 24 meses
├── services/cnpj_report.py       # car_inputs() (detail + indicators en paralelo), cnpj_status(); sin compute_status
├── routers/{dashboard,cars}.py   # usan cnpj_status / car_level
└── reports/__init__.py           # nivel = cnpj_status (sin cambiar el informe)
backend/tests/
├── unit/test_level_rules.py      # reemplaza test_cnpj_status.py
└── integration/test_car_status.py · test_public_status_levels.py (actualizados)

frontend/src/
├── types.ts · i18n/pt-BR.ts · lib/status.ts (reasonText, explain)
├── components/StatusBadge.tsx    # motivos, EUDR, enlace "Entenda o nível"
├── pages/LevelRulesPage.tsx      # NUEVO: /painel/nivel
├── layout/AppLayout.tsx · App.tsx
frontend/tests/StatusBadge.test.tsx · LevelRulesPage.test.tsx
```

## Complexity Tracking

Sin violaciones.
