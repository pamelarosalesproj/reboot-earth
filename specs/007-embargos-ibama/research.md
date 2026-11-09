# Research: Embargos del IBAMA como respaldo (feature 007)

Todas las verificaciones se hicieron contra los servicios reales el 2026-11-08, con scripts de
exploración fuera del repo. Los tests no usan red (principio VI).

## R1. Por qué fallan los embargos de los CARs sin alertas

- **Hallazgo**: `pointInformation(boundingBox)` de MapBiomas responde **HTTP 500 con cuerpo vacío**
  en cuanto se pide `embargoedAreasCount` o cualquier campo de `embargoedAreas`. Pidiendo solo
  `carCode` responde 200. Pasa también con un CAR (PA-1505031) cuyos embargos sí salen por la vía de
  las alertas. `ruralProperty(propertyCode)` no tiene campos de embargo. No hay otra vía en la API.
- **Consecuencia**: los CARs sin alertas (AM-1303304, PE-2600500, RO-1100205 en la cuenta de prueba)
  quedan con `embargoes_status="unavailable"` → `DADOS_PARCIAIS` → Silver.

## R2. Fuente de respaldo: capa de áreas embargadas del IBAMA

- **Decision**: ArcGIS FeatureServer público del Pamgia (IBAMA):
  `https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query`.
- **Rationale**: polígonos de las áreas embargadas (91 935 registros), actualizada a diario (máx.
  `dat_ult_alteracao` = 2026-11-07), sin credenciales, consulta espacial en ~0,2–0,3 s. Para PA-1505031
  devuelve el mismo embargo que MapBiomas (proceso 02048.000439/2012-63), una sola vez.
- **Alternatives considered**:
  - GeoServer `siscom.ibama.gov.br/geoserver` (`publica:vw_brasil_adm_embargo_a`): responde 404.
  - MapServer `embargos_siscom_brasil`: "Service not found".
  - CSV de termos de embargo (dados abertos): tiene `SIT_CANCELADO` pero no polígonos; exigiría sync
    diario y tabla nueva (como SINAFLOR). Descartado por la responsable (decisión "todos vigentes").
  - Capa del ICMBio `adm_embargo_icmbio_a`: es "Embargos (2022)", foto desactualizada. Descartada.

## R3. Forma de la consulta

- **Decision**: `POST` (form) con `f=geojson`, `geometryType=esriGeometryPolygon`,
  `geometry` = anillos de la **envolvente convexa simplificada** del CAR (buffer 0,001° → convex hull →
  simplify 0,0005°, igual que `inpe._filter_geom`), `inSR=4326`, `outSR=4326`,
  `spatialRel=esriSpatialRelIntersects`, `returnGeometry=true`, `resultRecordCount=2000` y
  `outFields=num_tad,serie_tad,num_processo,dat_embargo,qtd_area_embargada,des_tad`.
- **Rationale**: la envolvente es un superconjunto (no pierde embargos) y mantiene el cuerpo pequeño
  aunque el CAR tenga miles de vértices; la superposición exacta se calcula en local (R4).
  `outFields` explícito garantiza que **nunca** se piden `cpf_cnpj_embargado` ni `nome_embargado`
  (principio III). El polígono del CAR viene de MapBiomas en SIRGAS 2000 (EPSG:4674); la diferencia con
  WGS 84 es submétrica y se ignora (como en INPE).
- **Fechas**: en GeoJSON, `dat_embargo` llega como epoch en milisegundos → `date` UTC.
- **Respuesta truncada**: si `exceededTransferLimit` es verdadero, la lista no es completa → se trata
  como fuente no disponible (nunca se presenta una lista parcial como completa).
- **Errores**: HTTP ≠ 200, JSON inválido, `{"error": …}` o timeout → `SourceUnavailable`.

## R4. Asociación al CAR (umbral 0,1 ha)

- **Decision**: superposición = `car_polygon(geom) ∩ shape(feature).buffer(0)`, área con
  `sources.geo.area_ha` (equirectangular, error < 1 %). Cuenta si ≥ `IBAMA_MIN_OVERLAP_HA = 0.1`.
  Si la geometría del embargo no se puede interpretar, cuenta (criterio conservador) con
  `overlap_ha=None` y se registra en el log.
- **Medición real**: PA-1505031 ∩ embargo 02048000439201263 = 5,4 % del CAR (11 % del polígono
  embargado). Muy por encima del umbral.
- **Alternatives considered**: cualquier cruce (Bronze por roces de borde con vecinos); ≥ 1 ha (puede
  ignorar embargos chicos reales). Elegido 0,1 ha por la responsable.

## R5. Deduplicación (principio IV)

- **Decision**: una sola función de agrupamiento, `merge_embargo_items`, usada por MapBiomas y por el
  IBAMA: clave `(órgano, proceso)` o `(órgano, "code:<id>")` si no hay proceso; para el IBAMA el id es
  `<num_tad>-<serie_tad>`. Suma `overlap_ha` y junta descripciones.
- **Fuera de alcance**: normalizar el formato del proceso entre fuentes (MapBiomas repite
  `02048.000439/2012-63` y `02048000439201263` como dos embargos). Cambiaría conteos de CARs que hoy
  funcionan; queda como mejora posterior.

## R6. Caché y "stale" (principio II)

- **Decision**: el resultado del IBAMA vive en la caché del detalle (`CarSnapshot.detail_json`, 24 h),
  con `embargoes_source="ibama"` y `embargoes_checked_at`. Si en una recarga ninguna fuente determina
  los embargos pero la caché anterior sí los tenía (`status="ok"`), se conservan esos embargos con
  `embargoes_stale=true` y su fecha original. Aplica a ambas fuentes.
- **Rationale**: sin esto, un "Atualizar" con el IBAMA caído borraría un dato válido y volvería a
  "dados parciais".

## R7. Tests sin red

- **Decision**: `FakeIbama` en `conftest.py` montado con `respx` sobre `https://pamgia.ibama.gov.br/`,
  **caído por defecto** (`down=True`) para que los tests existentes conserven su comportamiento; los
  tests nuevos lo encienden y cargan `features`. Registra los parámetros recibidos para verificar
  `outFields`.
