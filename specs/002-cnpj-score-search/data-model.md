# Data Model: Consulta pública de score por CNPJ

**Feature**: `002-cnpj-score-search` | Basado en [`../001-producer-car-dashboard/data-model.md`](../001-producer-car-dashboard/data-model.md)

## Cambios en tablas persistidas

**Ninguno.** La búsqueda por CNPJ filtra `Producer.cnpj`, que ya existe, sin índice: a esta escala no hace falta, según el principio V. El status se calcula en el momento (R2) y el score todavía no se persiste (R3).

## Valores calculados (no persistidos)

### CarsAggregate

Resultado de `aggregate_cars`, compartido por el panel y la ficha pública (R1).

| Campo | Tipo | Regla |
|---|---|---|
| `cars_count` | int | CARs considerados (sin repetir) |
| `cars_with_data` | int | CARs con detalle obtenido (fresco o en caché) |
| `cars_unavailable` | int | `cars_count − cars_with_data` |
| `cars_embargoes_unknown` | int | CARs con datos pero `embargoes_status != "ok"` |
| `alerts_count` | int \| null | Alertas únicas por `alert_code`; null si ningún CAR tiene datos |
| `embargoes_count` | int \| null | Embargos únicos por (órgano, proceso) entre los CARs con `embargoes_status="ok"`; null si no hay ninguno |
| `stale` | bool | Algún CAR servido desde una caché vencida |
| `oldest_fetched_at` | datetime \| null | Fecha de obtención más antigua de los CARs con datos |

### Status

| Campo | Tipo | Valores |
|---|---|---|
| `level` | enum | `gold`, `silver`, `bronze`, `sem_dados` |
| `reason` | enum \| null | Solo con `sem_dados`: `not_registered`, `no_properties`, `data_unavailable` |
| `partial` | bool | `cars_unavailable > 0` o `cars_embargoes_unknown > 0` |
| `basis` | enum | `provisional` (regla FR-111a) o `score` (FR-111b, futuro) |

**Regla provisional** (`compute_status`), evaluada en orden. Gana la primera que se cumple:

| # | Condición | Resultado |
|---|---|---|
| 1 | Ningún `Producer` con el CNPJ | `sem_dados` / `not_registered` |
| 2 | `cars_count == 0` | `sem_dados` / `no_properties` |
| 3 | `cars_with_data == 0` | `sem_dados` / `data_unavailable` |
| 4 | `embargoes_count ≥ 1` | `bronze` |
| 5 | `alerts_count ≥ 1` o `partial` | `silver` |
| 6 | En otro caso | `gold` |

Consecuencia: un CAR `not_in_mapbiomas` tiene los embargos no determinables, así que activa `partial` y su CNPJ no llega a Gold (research R5).

### Score

| Campo | Tipo | Hoy |
|---|---|---|
| `state` | enum `em_calculo` \| `nao_calculavel` \| `disponivel` | `nao_calculavel` si el status es `sem_dados`; si no, `em_calculo` |
| `value` | number \| null | null |
| `computed_at` | datetime \| null | null |
| `method_version` | string \| null | null |

**Transiciones**: `nao_calculavel ↔ em_calculo`, según haya o no CARs con datos. `em_calculo → disponivel` ocurrirá cuando exista el método (otra feature). Con `disponivel`, `Status.basis = score`.

### PublicCnpjReport (respuesta pública)

`cnpj` (14 dígitos) · `cnpj_formatted` · `registered` · `status` · `score` · `cars_count` · `cars_with_data` · `stale` · `data_as_of` (= `oldest_fetched_at`).

**Nunca contiene**: códigos de CAR, geometrías, email, ids de cuenta, ni listas de alertas o embargos (FR-105).

### DashboardSummary (cambio)

Se le añaden `cnpj_status: Status` y `cnpj_score: Score`, calculados a nivel CNPJ (R4). Así coinciden con la ficha pública (FR-114, SC-106).
