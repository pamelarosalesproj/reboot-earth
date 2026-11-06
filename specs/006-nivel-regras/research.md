# Research: Nueva regla de nivel

## R1. Área RL/APP posterior a 2020

- **Decision**: suma de `area_in_car_ha` de las alertas abiertas con `post_2020` y (`legal_reserve_ha > 0` o `touches_app`), dividida por `summary.area_ha` del CAR. Bronze si ≥ 1 %.
- **Rationale**: MapBiomas no da el área en APP, solo si la alerta la toca; usar el área de la alerta en el CAR es conservador y comparable entre RL y APP.
- **Alternatives**: solo `legal_reserve_ha` (ignora APP); conteo de alertas (no escala con el tamaño del CAR).

## R2. DETER "últimos 24 meses"

- **Decision**: usar `context.deter.by_class[clase].last` (fecha de la detección más reciente de la clase) ≥ hoy − 730 días.
- **Rationale**: ya está en los indicadores cacheados; no hace falta otra consulta.

## R3. Motivos en el CNPJ

- **Decision**: para el CNPJ, cada motivo lleva `cars` (cuántos CARs lo cumplen) y no suma embargos ni alertas entre CARs.
- **Rationale**: sumar repetiría embargos y alertas compartidos (principio IV). Los números del CNPJ siguen en los "3 números" del Início (005).

## R4. Indicadores no disponibles

- **Decision**: si el detalle existe pero los indicadores de MapBiomas no, solo se evalúan los embargos (Bronze) y alertas abiertas no se pueden evaluar → `DADOS_PARCIAIS` (Silver como máximo, Bronze si hay embargo vigente). Si existen indicadores pero no el detalle → Sem dados (no hay área ni embargos).
