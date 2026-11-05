# Quickstart: validar el Panel del productor por CAR

Guía para levantar la app y comprobar de extremo a extremo que cumple la spec. Contrato: [contracts/openapi.yaml](./contracts/openapi.yaml) · Modelo: [data-model.md](./data-model.md).

## Prerrequisitos

- `uv` (Python 3.12) y Node 24 / npm 11.
- `.env` en la raíz del repo con `MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD` y `MAPBIOMAS_API_URL` (ya existe). Opcionales: `DATABASE_URL` (por defecto `backend/data/app.db`) y `COOKIE_SECURE=true` en producción.
- Conectividad con MapBiomas Alerta. Compruébala con:
  `curl -s -X POST -H 'Content-Type: application/json' -d '{"query":"{ version { version } }"}' "$MAPBIOMAS_API_URL"`

## Arranque

```bash
# Backend
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
# Frontend (otra terminal)
cd frontend && npm install && npm run dev      # http://localhost:5173 (proxy /api → :8000)
```

## Tests automáticos

```bash
cd backend && uv run pytest          # unit + integración con MapBiomas mockeado (fixture PE-2607505…)
cd frontend && npm test              # Vitest
```

## Escenarios de validación manual

CAR de referencia: `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` (esperado: 3 alertas, 0 embargos, 264,23 ha).
CNPJ válido de ejemplo: `04.654.691/0001-06`.

| # | Escenario | Pasos | Resultado esperado | Spec |
|---|---|---|---|---|
| 1 | Registro OK | Registrar email nuevo + CNPJ válido + contraseña ≥8 | Entra al panel con la invitación "Adicione seu primeiro CAR" | US1-1, US1-2 |
| 2 | Añadir CARs | En el panel, añadir el CAR de referencia y luego `PE-2600500-99E6E359827B460BAF346B15E27F602D` | 1 tarjeta y luego 2 | US4-1, US2-1 |
| 3 | CNPJ inválido | CNPJ `04.654.691/0001-07` | Error en el campo CNPJ, sin crear la cuenta | US1-3, SC-004 |
| 4 | CAR mal formado | En el panel, añadir `PE-123` | Error de formato, no se añade | US4-2 |
| 5 | Email duplicado | Repetir el registro 1 | 409, invitación a iniciar sesión | US1-5 |
| 6 | Tarjeta | Ver la tarjeta del CAR de referencia | Polígono encuadrado, "3 alertas", "0 embargos", fecha de obtención | US2-2..5, FR-018 |
| 7 | Detalle | Abrir detalle | 3 alertas (1571779, 1581449, 1580505) con fecha, área en el CAR y 0 embargos cada una; lista de embargos vacía | US3-1..3 |
| 8 | Aislamiento de fallos | Con el backend arrancado, apuntar `MAPBIOMAS_API_URL` a una URL inválida y borrar la caché de un CAR | Esa tarjeta muestra "no disponible" + Reintentar; las demás se muestran (desde caché) | FR-012, SC-005 |
| 9 | Caché antigua | Igual que el 8, pero sin borrar la caché | Tarjeta con aviso "desactualizado" | R7 |
| 10 | Quitar CARs | Quitar uno de 2 CARs; luego quitar el último | Desaparece su tarjeta; con 0 CARs vuelve la invitación a añadir uno | US4-5, US4-6 |
| 11 | Aislamiento de cuentas | Con el productor B, pedir `/api/cars/<CAR de A>/summary` | 404 | FR-006 |
| 12 | Credenciales | `curl` a cualquier endpoint y revisar la respuesta / DevTools | No aparecen credenciales ni token de MapBiomas | FR-017 |
| 13 | Landing | Abrir `http://localhost:5173/` sin sesión, pulsar "Cadastrar-se" y "Entrar"; volver con sesión iniciada | Explicación + pasos + fuente MapBiomas; cada botón lleva a su pantalla; con sesión se ve "Ir para o painel" | US5, FR-019..021 |
| 14 | Inicio | Entrar con el CAR de referencia en la cuenta | Lateral con avatar/email/CNPJ + "Início" y "Meus CARs"; números grandes 1 CAR, 3 alertas, 0 embargos | US6, FR-022..023 |

**Pendiente**: un escenario con un CAR que tenga embargos (buscarlo con `alerts(isInEmbargoedAlerta: true, limit: 5)` cuando la API responda) para validar el conteo por alerta y la deduplicación.
