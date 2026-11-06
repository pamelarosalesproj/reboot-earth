# Data Model: Indicadores socioambientales en la tarjeta del CAR

## Tablas nuevas

| Tabla | Campos | Uso |
|---|---|---|
| `car_indicators_snapshot` | `car_code` (PK), `payload` (JSON = `CarIndicators`), `fetched_at` | Caché de 24 h por CAR (R5) |
| `sinaflor_car` | `car_code` (PK), `autorizacoes` (int), `vigentes` (int), `volume_m3` (float), `ultima_emissao` (date \| null) | Resumen por CAR del POA Amazônia Legal (R4) |
| `sinaflor_sync` | `id` (PK = 1), `synced_at`, `source_last_modified` (str \| null), `rows` (int) | Si existe la fila, SINAFLOR está disponible |

Las tablas existentes no cambian.

## `CarIndicators` (respuesta y payload de la caché)

```text
car_code, fetched_at, stale (bool)
sources: {mapbiomas|prodes|deter|focos|sinaflor: {status, fetched_at, stale}}
    status ∈ "ok" | "indisponivel" | "nao_se_aplica"
alerts_by_status: {<Situacao>: {n, ha}}        # siempre las 6 claves (0 si no hay)
open: {
  post_2020: {n, ha}
  legal_reserve_ha        # solo alertas abiertas (embargo_vigente, com_fiscalizacao, pendente)
  app_alerts              # n.º de alertas abiertas que tocan APP
  embargoes_active        # null si los embargos no son determinables
  indigenous_land_ha
  integral_protection_ha
}
context: {
  embargoes_lifted                    # null si no son determinables
  sustainable_use_ha, sustainable_use_names: [str]
  native_vegetation: {remaining_pct, deforested_ha, by_year: {año: ha}} | null
  deter: {by_class: {<classe>: {n, ha, last}}} | null
  hotspots_12m: {count, by_month: {"YYYY-MM": n}} | null
  forest_management: {authorizations, active, volume_m3, last_issued} | null
}
alerts: [AlertIndicator]
```

`null` en un bloque de contexto significa que su fuente no tiene `status="ok"`; el motivo está en `sources`.

### `AlertIndicator`

| Campo | Tipo | Regla |
|---|---|---|
| `alert_code` | int | |
| `detected_at` | date | |
| `area_in_car_ha` | float | `alertAreaInCar` de este CAR (si no viene, el área de la alerta) |
| `status` | Situacao | FR-302 (abajo) |
| `post_2020` | bool | `detected_at > 2020-12-31` |
| `authorized_ha` | float | autorizaciones + planes de manejo |
| `legal_reserve_ha` | float | `min(crossedLegalReservesArea, area_in_car_ha)`: MapBiomas lo calcula sobre la alerta completa (R1) y se limita al área dentro del CAR |
| `touches_app` | bool | `crossedPermanentProtectedAreaTotal > 0` |
| `indigenous_land_ha`, `integral_protection_ha`, `sustainable_use_ha` | float | suma de los niveles federal, estatal y municipal, limitada a `area_in_car_ha` |
| `conservation_units` | [str] | nombres de `crossedConservationUnitsList` (máximo 3) |

### `Situacao` y prioridad (FR-302)

| # | Valor | Condición | Bloque |
|---|---|---|---|
| 1 | `suspensa_judicial` | `alert_code` ∈ `findSuspendedJudicialAlert(car)` | Contexto (superada) |
| 2 | `embargo_vigente` | `crossedEmbargoesArea > 0` y (algún embargo del CAR sin `expired_at` **o** embargos no determinables) | Riscos abertos |
| 3 | `autorizada` | `authorized_ha > 0` | Contexto (superada) |
| 4 | `embargo_levantado` | `crossedEmbargoesArea > 0` y todos los embargos del CAR con `expired_at` | Contexto (superada) |
| 5 | `com_fiscalizacao` | `actionsList` no vacío | Riscos abertos |
| 6 | `pendente` | en otro caso | Riscos abertos |

Etiqueta para la UI de `pendente`: **"Sem autorização registrada"** (FR-304).

### Clases del DETER (FR-311)

`DESMATAMENTO_CR`, `DESMATAMENTO_VEG`, `DEGRADACAO`, `CS_GEOMETRICO` ("Corte seletivo – padrão de manejo"), `CS_DESORDENADO` ("Corte seletivo – desordenado"), `CICATRIZ_DE_QUEIMADA`, `MINERACAO`. Cualquier otra clase se muestra con su nombre original.
