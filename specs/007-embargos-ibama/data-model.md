# Data Model: Embargos del IBAMA como respaldo (feature 007)

Sin tablas nuevas: todo vive en la caché existente `CarSnapshot.detail_json` (JSON). Los campos
nuevos son opcionales, así que las cachés anteriores siguen siendo válidas.

## Embargo (schema `Embargo`, ampliado)

| Campo | Tipo | Origen MapBiomas | Origen IBAMA |
|---|---|---|---|
| `source` | str \| null | `source` | `"IBAMA"` |
| `process_code` | str \| null | `processCode` | `num_processo` |
| `area_ha` | float \| null | `areaHa` | `qtd_area_embargada` |
| `registered_at` | date \| null | `sourceRegisteredAt` | `dat_embargo` (epoch ms → date) |
| `expired_at` | date \| null | `sourceExpiredAt` | siempre `null` (decisión "todos vigentes") |
| `descriptions` | list[str] | `description` | `des_tad` |
| **`term`** (nuevo) | str \| null | `null` | `"<num_tad>/<serie_tad>"` |
| **`overlap_ha`** (nuevo) | float \| null | `null` | ha de la intersección con el CAR (≥ 0,1) |

Nunca se piden ni se guardan `cpf_cnpj_embargado` ni `nome_embargado`.

## CarSummary (ampliado)

| Campo | Tipo | Regla |
|---|---|---|
| `embargoes_status` | `ok` \| `not_determinable` \| `unavailable` | sin cambios |
| **`embargoes_source`** (nuevo) | `mapbiomas` \| `ibama` \| null | quién determinó los embargos; null si nadie |
| **`embargoes_checked_at`** (nuevo) | datetime \| null | cuándo se obtuvieron; null si `status ≠ ok` |
| **`embargoes_stale`** (nuevo) | bool (default false) | embargos de una caché anterior porque ninguna fuente respondió ahora |
| `embargoes_count` | int \| null | `len(embargoes)` solo si `status = ok` (sin cambios) |

## Transiciones de estado de los embargos (en `build_detail` / `get_detail`)

```
MapBiomas ok                         → status=ok, source=mapbiomas            (IBAMA no se consulta)
MapBiomas falla, CAR con polígono:
    IBAMA ok                         → status=ok, source=ibama, embargos con overlap ≥ 0,1 ha
    IBAMA falla y caché previa ok    → embargos previos, status=ok, stale=true, fecha previa
    IBAMA falla sin caché previa ok  → status de MapBiomas (unavailable / not_determinable), source=null
MapBiomas falla, CAR sin polígono    → status de MapBiomas (sin cambio)
```

## Constantes (único lugar)

- `IBAMA_MIN_OVERLAP_HA = 0.1` en `backend/app/sources/ibama.py`.
- `settings.ibama_embargoes_url`, `settings.ibama_timeout_s = 5.0` en `backend/app/config.py`.
