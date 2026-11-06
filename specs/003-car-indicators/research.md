# Research: Indicadores socioambientales en la tarjeta del CAR

**Feature**: `003-car-indicators` | **Date**: 2026-11-06

Las decisiones se validaron con un prototipo contra las fuentes reales y 3 CARs (PE-2607505, MT-5102504, TO-1712504) el 2026-11-06. Stack fijado por la constitución; no quedan NEEDS CLARIFICATION.

## R1. Situación de cada alerta: campos adicionales de MapBiomas

- **Decision**: una consulta nueva, `alerts(propertyCodes: [ID!], limit: 200)`, con:
  - `crossedRuralProperties { code alertAreaInCar }`;
  - `crossedDeforestationAuthorizationsArea` y `crossedForestManagementsArea`;
  - `crossedLegalReservesArea` y `crossedPermanentProtectedAreaTotal`;
  - `crossedIndigenousLandsArea`;
  - los seis campos `crossed{Federal,State,Municipality}ProtectedArea{IntegralProtections,SustainableUses}Area`;
  - `crossedConservationUnitsList`, `crossedEmbargoesArea` y `actionsList`.

  Además, `findSuspendedJudicialAlert(carCode: String!)`. La situación la asigna una función pura `classify_alert`, según FR-302.
- **Rationale**: es la misma API y la misma cuenta. Verificado: responde para los 3 CARs. El tipo correcto de `propertyCodes` es `[ID!]` y el de `carCode` es `String!` (los tipos equivocados dan error).
- **Limitations**:
  - `autorizada`, `com_fiscalizacao` y `suspensa_judicial` no aparecieron en datos reales; se prueban con datos simulados.
  - El área de reserva legal, APP y unidades de conservación es la de la alerta completa, no solo la parte dentro del CAR. Por ejemplo, la alerta 747059 tiene 6,55 ha dentro del CAR y 7,69 ha en reserva legal. Se muestra con una nota.

## R2. Fuentes del INPE: WFS de TerraBrasilis, sin credenciales

- **Decision**: cliente HTTP propio (`app/sources/inpe.py`) con timeout de 30 s.
  - Servicio principal: `https://terrabrasilis.dpi.inpe.br/geoserver/ows`.
  - Servicio de focos de calor: `https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs`.
  - Siempre WFS 1.1.0, filtrando por rectángulo con el **orden longitud, latitud**. Si hay filtro CQL, el rectángulo va **dentro** del CQL como `BBOX(geom,...)`, porque combinar el parámetro `bbox` con `CQL_FILTER` provoca un error.
- **Capas**:
  - Biomas: `prodes-brasil-nb:biomas_brasil`.
  - Desmatamento: por bioma, la capa `yearly_deforestation` más la `accumulated_deforestation_*`.
  - DETER: `deter-amz:deter_amz` (geometría `geom`, filtrada por `view_date`).
  - Focos de calor: `bdqueimadas2:focos` (geometría `geometria`, filtrada por `data_hora_gmt` y `eh_satelite_referencia = true`).
- **Optimización**: primero se identifica qué biomas cruza el CAR, y solo se consultan las capas PRODES de esos biomas (de 1 a 3 biomas en lugar de 6, es decir, 2 a 6 consultas en lugar de 12). El DETER solo se consulta si el CAR cruza el bioma Amazonía.
- **Alternatives considered**: los CSV masivos de focos de calor, anuales o mensuales (más datos de los necesarios por CAR), y la API de Brazil Data Cube (raster, no hace falta).

## R3. Intersecciones geométricas: dependencia `shapely`

- **Decision**: añadir `shapely` al backend para intersecar polígonos (PRODES y DETER), unir capas que se superponen entre biomas y comprobar si un punto está dentro de un polígono (focos de calor). Las áreas se calculan con una aproximación local equirectangular, con un error menor al 1 % en CARs de hasta decenas de miles de ha.
- **Rationale**: la constitución (V) exige una necesidad demostrada. FR-309 pide no contar dos veces los mapas de biomas que se superponen, y en el prototipo sumar sin unir daba 59 % de vegetación en el CAR de MT en lugar de 66,9 %. Implementar a mano la intersección y la unión de polígonos no es razonable.
- **Alternatives considered**: el filtro `INTERSECTS` de GeoServer (devuelve los polígonos enteros sin recortar, así que el área queda mal); `pyproj` para áreas geodésicas (otra dependencia más, sin una ganancia relevante con este margen de error).

## R4. SINAFLOR: sincronización diaria a una tabla resumida

- **Decision**:
  - El comando `uv run python -m app.sources.sinaflor` descarga en streaming el CSV del POA Amazônia Legal, de unos 90 MB (`.../SINAFLOR/poaAmazoniaLegal/sinaflor-poa-amazonia-legal.csv`, separado por `;`, UTF-8 con BOM).
  - Agrega por `NRO_CAR_IMOVEL_RURAL`: autorizaciones distintas (`NRO_AUTORIZACAO`), autorizaciones con `SITUACAO` vigente ("Autorização Emitida" o "Autorização Retificada"), volumen en m³ (solo productos cuyo nombre contiene "m³", con la `,` decimal normalizada) y la última fecha de emisión.
  - Lo guarda en la tabla `sinaflor_car`, que se reemplaza en cada ejecución.
- **Rationale**: no hay una API por CAR, y descargar 90 MB en cada visita es inaceptable. La tabla resumida es la pieza mínima: a lo sumo unas 5.000 filas.
- **Mitigación de duplicados**: el IBAMA reportó en 2025 autorizaciones duplicadas. Las autorizaciones se cuentan por número distinto y, para cada par (autorización, especie, producto), se toma el máximo, no la suma de filas repetidas.
- **Sin sincronización previa**: la tabla vacía y sin metadatos de sincronización significa "indisponível" (FR-313), nunca 0.
- **Limitation**: la sincronización es manual o la programa quien opere el sistema (cron). Queda documentado en el README.

## R5. Caché y fallos por fuente

- **Decision**: nueva tabla `car_indicators_snapshot` (`car_code` como clave primaria, `payload` en JSON y `fetched_at`). Es una tabla nueva porque `create_all` no añade columnas a tablas que ya existen, así que se evita una migración.
  - TTL de 24 h.
  - Cada fuente (mapbiomas, prodes, deter, focos, sinaflor) se resuelve por separado: si falla, se reutiliza el bloque de esa fuente de la caché anterior con `stale=true`; si no hay caché, `status="indisponivel"`.
- **Rationale**: constitución II y SC-304.

## R6. Endpoint y UI

- **Decision**: `GET /api/cars/{car_code}/indicators?refresh=`, solo para el dueño del CAR (`own_car`). En el frontend:
  - `CarIndicators` carga los indicadores aparte del resumen, así que si fallan no se rompe la tarjeta.
  - `IndicatorValue` muestra los tres estados: valor, indisponível y não se aplica.
  - El detalle usa el mismo endpoint para añadir columnas a la tabla de alertas, cruzando por `alert_code`.
- **Rationale**: aislar los fallos (SC-304) y reutilizar un único endpoint en la tarjeta y el detalle (constitución IV).

## R7. Amazônia Legal y bioma Amazonía

- **Decision**:
  - El **DETER** aplica si el CAR cruza el bioma Amazonía, según la capa de biomas (R2).
  - El **SINAFLOR** aplica si la UF del CAR está en la Amazônia Legal (AC, AM, AP, MA, MT, PA, RO, RR, TO).
- **Limitation**: el MA solo está parcialmente en la Amazônia Legal. Para un CAR del MA fuera de ella se mostrará "sem autorizações" en lugar de "não se aplica", que es un resultado aceptable. Queda anotado.
