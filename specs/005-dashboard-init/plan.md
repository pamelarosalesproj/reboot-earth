# Implementation Plan: Início del productor como resumen del CNPJ

**Branch**: `005-dashboard-init` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

- **Backend**: dos endpoints autenticados.
  - `GET /api/dashboard/overview`: números a nivel CNPJ (alertas abiertas y superadas a partir de los indicadores de la 003, embargos vigentes a partir de los detalles de la 001).
  - `GET /api/dashboard/report`: el informe, con un proveedor sustituible que hoy lee un ejemplo JSON local fuera del repositorio. El `nivel` lo pone siempre `compute_status`.
- **Frontend**: el Início se rehace con tres bloques (estado, números e informe) y deja de mostrar los módulos de lotes. Esos módulos pasan a la vista previa `/preview/lotes`.

## Technical Context

- **Stack**: el mismo. **Sin dependencias ni tablas nuevas.**
- **Storage**:
  - el ejemplo vive en `backend/data/mock_reports/<cnpj>.json`, una carpeta ya ignorada por git (`backend/data/*`);
  - la ruta es configurable con `MOCK_REPORTS_DIR`.
- **Testing**: pytest (los ejemplos en un directorio temporal de cada test) y vitest.
- **Performance**: el resumen usa la caché de indicadores de 24 h. Sin caché, calcula los CARs en paralelo.

## Constitution Check

| Principio | Estado | Cómo |
|---|---|---|
| I. Fuentes en el servidor | ✅ | Nada nuevo en el navegador; el futuro agente irá en el backend |
| II. Tolerancia a fallos | ✅ | Si una fuente falla, cuenta como CAR sin datos (nunca 0). El informe tiene su propio estado "indisponível" y no bloquea el resto |
| III. Privacidad | ✅ | Endpoints con sesión, solo del CNPJ del productor. El ejemplo, con CARs reales, queda fuera del repositorio |
| IV. Una sola fuente de verdad | ✅ | Situación de las alertas con `classify_alert` (003); nivel con `compute_status` (002); deduplicación de embargos por (órgão, processo), igual que `aggregate_cars` |
| V. Simplicidad | ✅ | Sin dependencias ni tablas; el proveedor es una función, no un framework |
| VI. Calidad | ✅ | Tests de conteo y deduplicación, de "indisponível", de informe ausente o presente, de nivel impuesto y de palabras prohibidas |
| VII. Fidelidad e idioma | ✅ | Origen y fecha del informe visibles; aviso de ejemplo; pt-BR |

## Project Structure

```text
backend/app/
├── config.py                  # + mock_reports_dir
├── schemas.py                 # + CnpjOverview, CnpjReport, ReportProperty
├── services/cnpj_overview.py  # NUEVO: cnpj_overview() (alertas abiertas/superadas, embargos vigentes)
├── reports/__init__.py        # NUEVO: get_report(db, client, cnpj) + validación; proveedor "exemplo"
└── routers/dashboard.py       # + GET /dashboard/overview, GET /dashboard/report
backend/tests/
├── integration/test_dashboard_overview.py
└── integration/test_dashboard_report.py
backend/data/mock_reports/     # local, ignorado por git: 88419439000102.json, 11444777000161.json

frontend/src/
├── types.ts · api/client.ts · i18n/pt-BR.ts
├── components/CnpjReportView.tsx   # NUEVO: secção "Relatório do CNPJ"
├── pages/HomePage.tsx · HomePage.css
└── preview/DesignPreview.tsx       # /preview/painel (Início nuevo) + /preview/lotes (módulo de lotes)
frontend/tests/HomePage.test.tsx · DesignPreview.test.tsx · CnpjReportView.test.tsx
```

## Contrato para el agente (otro integrante del equipo)

Hay que sustituir `_example_report()` en `app/reports/__init__.py` por la generación real. Se mantiene:
- el formato `CnpjReport` de `contracts/openapi.yaml`;
- que `nivel` lo impone el backend;
- la validación (palabras prohibidas, máximo de 3 riesgos y 3 elementos de contexto).

Las reglas del prompt y los controles están en [`docs/proposta-agente.md`](../../docs/proposta-agente.md).

## Complexity Tracking

Sin violaciones.
