# Data Model: Nueva regla de nivel

Sin tablas nuevas. Solo cambia el modelo de respuesta `Status` (calculado, no persistido).

## Status (CAR o CNPJ)

| Campo | Tipo | Notas |
|---|---|---|
| level | gold · silver · bronze · sem_dados | |
| reason | not_registered · no_properties · data_unavailable · null | Solo con sem_dados |
| partial | bool | Algún dato no disponible (CAR sin datos, embargos no determinables, indicadores de MapBiomas no disponibles) |
| basis | provisional · regras · score | Esta feature usa `regras` |
| reasons | Reason[] | Todos los motivos que se cumplen, del más grave al menos grave |
| cars_by_level | {gold, silver, bronze, sem_dados: int} · null | Solo en el CNPJ |
| eudr_attention | bool · null | `null` = indeterminado (sin datos de alertas) |
| alerts_count | int · null | Alertas abiertas (CAR) o únicas abiertas no se suman en el CNPJ: `null` en el CNPJ |
| embargoes_count | int · null | Embargos vigentes (CAR); `null` en el CNPJ |

## Reason

| Campo | Tipo | Notas |
|---|---|---|
| code | EMBARGO_VIGENTE · TI_UC_INTEGRAL · RL_APP_POS2020 · DETER_GRAVE · ALERTA_ABERTA · DETER_DEGRADACAO · DADOS_PARCIAIS | |
| severity | bronze · silver | Nivel al que lleva |
| n | int · null | CAR: embargos, alertas o detecciones DETER |
| ha | float · null | CAR: área |
| pct | float · null | CAR: % del área del CAR (solo RL_APP_POS2020) |
| cars | int · null | CNPJ: cuántos CARs cumplen el motivo |
