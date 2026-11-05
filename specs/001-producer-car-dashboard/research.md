# Research: Panel del productor por CAR

**Fecha**: 2026-11-05 · **Fuentes**: `SCHEMA.md` / `schema.json` (introspección de MapBiomas Alerta), `mapbiomas_api.py`, `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0_completo.json`

## R1. Stack del backend

- **Decision**: Python 3.12 + FastAPI + SQLModel/SQLite, gestionado con `uv`.
- **Rationale**: el usuario pidió un backend Python básico. FastAPI genera OpenAPI automáticamente (sirve para el contrato con el frontend) y su soporte async permite consultar MapBiomas en paralelo. SQLite no requiere servidor. El Python del sistema es 3.9 (ya sin soporte), pero `uv` y 3.12 ya están instalados.
- **Alternatives considered**: Flask (más simple, pero sin validación ni OpenAPI integrados); Django (demasiado para un MVP); PostgreSQL (innecesario a esta escala, aunque migrar es directo con SQLModel).

## R2. Stack del frontend y mapa

- **Decision**: React 19 + Vite (react-leaflet 5 requiere React 19) + TypeScript; mapa con Leaflet + react-leaflet y teselas OpenStreetMap.
- **Rationale**: es la opción TS básica más común. Leaflet dibuja GeoJSON (incluidos MultiPolygon) y `fitBounds` cubre el encuadre automático (FR-008) sin API keys.
- **Alternatives considered**: MapLibre GL (vectorial, más pesado); Mapbox (requiere token); servir las imágenes PNG que ya da MapBiomas (`imageContext`), descartado porque no son interactivas y dependen de la disponibilidad de MapBiomas.

## R3. Autenticación del productor

- **Decision**: email + contraseña con hash Argon2 (`pwdlib`). Sesión mediante cookie `HttpOnly`, `SameSite=Lax`, con un token aleatorio guardado en la tabla `Session` (caduca a los 7 días).
- **Rationale**: es lo más simple y seguro para una SPA servida en el mismo origen (proxy de Vite en desarrollo). La sesión se puede revocar al cerrar sesión, y el token no queda accesible a JavaScript.
- **Alternatives considered**: JWT en `localStorage` (expuesto a XSS y sin revocación simple); OAuth/SSO (fuera del alcance del MVP).

## R4. Acceso a MapBiomas Alerta

- **Decision**: cliente async con `httpx` en el servidor, autenticado con la cuenta de servicio de `.env` (`MAPBIOMAS_EMAIL`/`PASSWORD`/`API_URL`). El token se guarda en memoria y, ante un error de autenticación, se vuelve a iniciar sesión una vez. Timeout de 20 s por consulta.
- **Rationale**: cumple FR-017 (credenciales nunca en el navegador) y reutiliza la mutation `signIn` que ya usa `mapbiomas_api.py`.
- **Queries por CAR** (portadas de `mapbiomas_api.py`):
  - Polígono y metadatos: `ruralProperty(propertyCode)` → `geomRuralProperty` (EWKT, SRID 4674), `areaHa`, `stateAcronym`, `carType`. Se convierte a GeoJSON en el servidor.
  - Alertas: `ruralProperty.alerts { alertCode detectedAt areaHa crossedRuralProperties(carCode) { alertAreaInCar } crossedEmbargoesTotal crossedEmbargoesIds crossedEmbargoesList }`.
  - Embargos del CAR: `alerts(propertyCodes:[car], limit:1) { collection { ruralProperties(carCode) { embargoedAreas {...} } } }`. Si el CAR no tiene alertas, se usa `pointInformation(boundingBox)` alrededor de un punto interior como respaldo; si eso también falla, el resultado es "no determinable".

## R5. Relación embargo ↔ alerta

- **Decision**: el número de embargos por alerta (FR-013) usa `crossedEmbargoesTotal` / `crossedEmbargoesIds`: embargos cuyo polígono se superpone a la alerta (equivale al filtro `isInEmbargoedAlerta`). Los campos `crossedEmbargoesRuralProperties*` (embargos de los CARs que la alerta cruza) no se usan por alerta, porque duplican el total del CAR.
- **Rationale**: es el único vínculo que conecta un embargo con un desmatamento concreto.
- **Riesgo abierto**: no está validado con datos reales (el CAR de prueba tiene 0 embargos y la API no respondía). Tampoco se sabe si `crossedEmbargoesIds` repite el mismo proceso con distintos IDs, como ocurre en `embargoedAreas`. Mitigación: si `crossedEmbargoesList` trae órgano + proceso, deduplicar por esa clave; si no, contar los IDs distintos. Se revalida en implementación con un CAR obtenido vía `alerts(isInEmbargoedAlerta: true)`.

## R6. Validación de existencia del CAR (FR-004) ⚠️

- **Hallazgo**: según el schema, `ruralProperty(propertyCode)` *"requires a Rural Property crossed with alerts in our database"*. Un CAR real **sin alertas** podría devolver `null` y ser rechazado en el registro, aunque sea precisamente el productor sin desmatamento.
- **Decision (confirmada por el usuario el 2026-11-05)**: (1) se valida el formato `UF-NNNNNNN-HASH32` localmente; (2) se consulta `ruralProperty`; si devuelve datos, el CAR existe. (3) Si devuelve `null`, se acepta igualmente con el estado "sin registro en MapBiomas (sin alertas)" y su tarjeta muestra 0 alertas y embargos "no determinable"; (4) si MapBiomas no responde, el registro se rechaza con un mensaje de "inténtalo más tarde".
- FR-004 de spec.md ya está actualizado con esta regla.

## R7. Caché y frescura (FR-018)

- **Decision**: tabla `CarSnapshot` con el JSON del resumen y del detalle por código de CAR, compartida entre productores. TTL de 24 h; `?refresh=true` la ignora. Si MapBiomas falla y existe una snapshot antigua, se devuelve con `stale: true`.
- **Rationale**: reduce la dependencia de una API inestable y cumple SC-002.
- **Alternatives considered**: Redis (un servicio más para un MVP); no cachear (el panel sería inutilizable cada vez que MapBiomas cae).

## R8. Validación de CNPJ

- **Decision**: se normaliza a 14 dígitos (se quita la máscara); se rechazan secuencias repetidas (`00000000000000`…) y se verifican los dos dígitos verificadores (módulo 11, pesos 5-4-3-2-9-8-7-6-5-4-3-2 y 6-5-4-3-2-9-8-7-6-5-4-3-2).
- **Nota**: el CNPJ alfanumérico (Receita Federal, a partir de julio de 2026) no está cubierto en el MVP. Se deja documentado como mejora futura.

## R9. Idioma

- **Decision**: interfaz en portugués de Brasil, con textos centralizados en `frontend/src/i18n/pt-BR.ts` para poder traducirlos después.
