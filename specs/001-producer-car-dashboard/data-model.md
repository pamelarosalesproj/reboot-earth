# Data Model: Panel del productor por CAR

## Entidades persistidas (SQLite)

### Producer

| Campo | Tipo | Reglas |
|---|---|---|
| id | int PK | autoincremental |
| email | str | único, en minúsculas, formato válido (FR-002) |
| password_hash | str | Argon2; nunca se devuelve (FR-005) |
| cnpj | str(14) | solo dígitos, dígitos verificadores válidos (FR-003) |
| created_at | datetime | UTC |

Relación: 1 Producer → N ProducerCar (0 o más; se añaden desde el panel).

### ProducerCar

| Campo | Tipo | Reglas |
|---|---|---|
| id | int PK | |
| producer_id | FK → Producer | cascade delete |
| car_code | str | regex `^[A-Z]{2}-\d{7}-[0-9A-F]{32}$` (se guarda en mayúsculas) |
| mapbiomas_status | enum | `found` · `not_in_mapbiomas` (ver research R6) |
| added_at | datetime | |

Restricciones: único (`producer_id`, `car_code`). El mismo `car_code` puede estar en varios productores.

### Session

| Campo | Tipo | Reglas |
|---|---|---|
| token | str PK | aleatorio, 32 bytes, url-safe |
| producer_id | FK → Producer | |
| expires_at | datetime | creación + 7 días |

### CarSnapshot (caché de MapBiomas, compartida)

| Campo | Tipo | Reglas |
|---|---|---|
| car_code | str PK | |
| summary_json | JSON | `CarSummary` serializado |
| detail_json | JSON / null | `CarDetail` serializado (se rellena al abrir el detalle) |
| fetched_at | datetime | TTL de 24 h (research R7) |

## Entidades derivadas (respuestas de API, no persistidas salvo en la caché)

### CarSummary
`car_code`, `state` (UF), `area_ha`, `car_type`, `geometry` (GeoJSON MultiPolygon, o null si no hay), `alerts_count` (int, o null si no está disponible), `embargoes_count` (int, o null), `embargoes_status` (`ok` · `not_determinable` · `unavailable`), `fetched_at`, `stale` (bool).

Regla FR-011: `0` solo significa dato confirmado. Si no hay dato, el campo va en `null` acompañado de su estado.

### Alert
`alert_code`, `detected_at` (fecha), `area_ha` (total), `area_in_car_ha` (suma de `alertAreaInCar` para este CAR), `embargoes_count` (embargos superpuestos a la alerta, research R5).

### Embargo
`source` (IBAMA / ICMBio / órgano estatal), `process_code`, `area_ha`, `registered_at`, `expired_at` (nullable), `descriptions` (lista). Clave de deduplicación: (`source`, `process_code`).

### CarDetail
`summary` (CarSummary) + `alerts` (Alert[], ordenadas por `detected_at` desc) + `embargoes` (Embargo[], ordenados por `registered_at`).

## Estados de una tarjeta (frontend)

```text
loading → ok
        → ok(stale)        # MapBiomas falló, se muestra la caché antigua con aviso
        → unavailable      # MapBiomas falló y no hay caché → botón "Reintentar"
ok/stale --(Actualizar)--> loading
```
