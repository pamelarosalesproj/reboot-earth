# Tasks: Início del productor como resumen del CNPJ

**Input**: [plan.md](plan.md), [spec.md](spec.md), [contracts/openapi.yaml](contracts/openapi.yaml)

**Tests**: incluidos (constitución VI).

## Phase 1: Foundational

- [X] T001 En `backend/app/config.py`, añadir `mock_reports_dir` (por defecto `backend/data/mock_reports`). En `backend/app/schemas.py`, añadir `CnpjOverview`, `ReportProperty` y `CnpjReport` según el contrato
- [X] T002 [P] En `frontend/src/types.ts`, añadir los tipos `CnpjOverview` y `CnpjReport`; en `frontend/src/api/client.ts`, añadir `getOverview()` y `getReport()`

## Phase 2: US1 — Estado y números (P1)

- [X] T003 [US1] Crear `backend/tests/integration/test_dashboard_overview.py`:
  - CAR de referencia con 3 alertas pendientes → `open_alerts.n == 3` y `superseded` 0;
  - una alerta autorizada pasa a superada;
  - la misma alerta en dos CARs del CNPJ cuenta una vez;
  - embargos vigentes únicos entre CARs, y los levantados no cuentan;
  - con MapBiomas caído y sin caché → `alerts_total` y `open_alerts` en null, con `cars_without_alert_data` > 0;
  - 401 sin sesión.
- [X] T004 [US1] Crear `backend/app/services/cnpj_overview.py` con `cnpj_overview(db, client, cnpj)`: los CARs del CNPJ, `get_indicators` y `get_detail` por CAR en paralelo, la deduplicación de alertas por código (una alerta es abierta si lo es en algún CAR; el ha se suma por CAR) y la de embargos vigentes por (source, process_code) sin `expired_at`. Añadir `GET /dashboard/overview` en `backend/app/routers/dashboard.py`
- [X] T005 [US1] En `frontend/src/pages/HomePage.tsx`, `HomePage.css` e `i18n/pt-BR.ts`:
  - bloque de estado (`StatusBadge` del `cnpj_status`, score y enlace "Ver como o comprador vê");
  - 3 números (`getOverview`), con "de N; X superadas" y los avisos de CARs sin datos;
  - quitar `LotOverview` del Início.

## Phase 3: US2 — Informe (P1)

- [X] T006 [US2] Crear `backend/tests/integration/test_dashboard_report.py` (con `settings.mock_reports_dir` en un `tmp_path`):
  - sin archivo → `status=indisponivel`;
  - con archivo → `ok`, `origem=exemplo` y `nivel` igual a `compute_status`, aunque el archivo diga otro;
  - un archivo con "ilegal" o con más de 3 riesgos → `indisponivel` (rechazado);
  - 401.
- [X] T007 [US2] Crear `backend/app/reports/__init__.py` con `get_report(db, client, cnpj)`: lee `<dir>/<cnpj>.json`, valida con `CnpjReport` (máximo de 3 riesgos y 3 elementos de contexto, sin palabras prohibidas) e impone `nivel` y `origem="exemplo"`. Documentar ahí el punto de sustitución por el agente. Añadir `GET /dashboard/report`
- [X] T008 [US2] Crear `frontend/src/components/CnpjReportView.tsx`: título, riesgos, contexto, salvedades, imóveis con enlace a `/painel/cars/<code>`, aviso de origen (FR-507) y fecha; "Relatório ainda não disponível" si es `indisponivel` o hay error
- [X] T009 [US2] Escribir los ejemplos locales `backend/data/mock_reports/88419439000102.json` y `11444777000161.json`, redactados por Claude a partir de los indicadores reales del 2026-11-06 (fuera del repositorio)

## Phase 4: Vista previa y tests del frontend

- [X] T010 En `frontend/src/preview/DesignPreview.tsx`: `/preview/painel` muestra el Início nuevo con datos ficticios (overview e informe de ejemplo) y `/preview/lotes` muestra el `LotOverview` del rediseño. Actualizar `frontend/tests/DesignPreview.test.tsx`
- [X] T011 [P] Actualizar `frontend/tests/HomePage.test.tsx`: estado, 3 números, sin módulos de lotes e informe ausente sin romper la página. Crear `frontend/tests/CnpjReportView.test.tsx`: aviso de ejemplo, enlaces de imóveis y sin "ilegal"

## Phase 5: Polish

- [X] T012 Actualizar `docs/arquitetura.md`, `README.md` y `AGENTS.md`: endpoints nuevos, el informe de ejemplo fuera del repositorio y el punto de integración del agente
- [X] T013 Gates: ruff, pytest, build y vitest. Validación en vivo con el CNPJ de referencia (SC-501)
