# Research: Consulta pública de score por CNPJ

**Feature**: `002-cnpj-score-search` | **Date**: 2026-11-05

El stack ya está definido por la feature 001 (FastAPI + SQLModel/SQLite, React + Vite) y fijado en la constitución v1.0.0 (*Restricciones adicionales*). No quedan NEEDS CLARIFICATION técnicos. Abajo, las decisiones de diseño propias de esta feature.

## R1. Una sola función de agregación para el panel y la ficha pública

- **Decision**: extraer de `backend/app/routers/dashboard.py` la agregación (alertas únicas, embargos únicos por órgano + proceso, CARs con datos, CARs con embargos no determinables, fecha más antigua) a una función pura `aggregate_cars(details, cars_count)` en un servicio nuevo `app/services/cnpj_report.py`. Tanto `GET /api/dashboard` como `GET /api/public/cnpj/{cnpj}` la usan, y el status se calcula sobre su resultado.
- **Rationale**: SC-106 exige que el panel y la ficha pública coincidan en el 100% de los casos. Compartir el código lo garantiza por construcción y evita una segunda copia de las reglas de deduplicación (FR-113).
- **Alternatives considered**: duplicar la lógica en el router público (se desincroniza); que la ficha pública llame internamente al endpoint del panel (necesita una sesión de productor, así que no aplica).

## R2. Status calculado en el momento, sin tabla

- **Decision**: `compute_status(aggregate, registered)` es una función pura que devuelve `{level, reason, basis}` siguiendo FR-111a en orden: Sem dados → Bronze → Silver → Gold. No se persiste; se calcula en cada consulta a partir de la caché `CarSnapshot` (TTL 24 h).
- **Rationale**: los datos de origen ya están en caché, así que el cálculo cuesta microsegundos. Guardar el status obligaría a invalidarlo cada vez que se añade o quita un CAR o se refresca un snapshot, y es justo ahí donde aparecerían discrepancias (FR-114, US3 escenario 2).
- **Alternatives considered**: una tabla `cnpj_status` actualizada con eventos (más piezas sin ninguna ganancia medible a esta escala).

## R3. Score como "proveedor" sustituible, sin tabla todavía

- **Decision**: `get_score(cnpj, aggregate) -> Score`, en el mismo servicio. Hoy devuelve `state="nao_calculavel"` si no hay CARs con datos y `state="em_calculo"` en el resto de casos, con `value`, `computed_at` y `method_version` en `null`. Cuando exista el método, se sustituye esta función (y, si hace falta, se añade una tabla `cnpj_score`), y `compute_status` pasa a usar `basis="score"` (FR-111b).
- **Rationale**: cumple FR-110 (activar el score no cambia el contrato ni la UI más allá de mostrar `value`) sin crear hoy una tabla vacía.
- **Alternatives considered**: crear ya la tabla `cnpj_score` (YAGNI; su forma depende del método que aún no existe).

## R4. Agregación por CNPJ entre cuentas

- **Decision**: los CARs de un CNPJ son el conjunto **sin repetir** de `ProducerCar.car_code` de todos los `Producer` con ese CNPJ normalizado. No se añade índice a `Producer.cnpj` (principio V: con cientos de filas no aporta, y en la base existente exigiría una migración). "Registrado" significa que existe al menos un `Producer` con ese CNPJ.
- **Rationale**: es el edge case "dos cuentas con el mismo CNPJ" de la spec. Hoy `Producer.cnpj` no es único.
- **Consequence**: en el panel de una cuenta (FR-114), el status se muestra **a nivel CNPJ** (lo mismo que ve el comprador), no solo con los CARs de esa cuenta. Los números grandes de "Início" (FR-023 de 001) siguen siendo los de la cuenta.

## R5. Comportamiento con MapBiomas caído y CARs sin registro

- **Decision**: la ficha pública reutiliza `get_detail` (caché 24 h; si MapBiomas no responde, sirve la caché con `stale=true`; sin caché, el CAR cuenta como "sin datos"). Nunca devuelve 503 por MapBiomas (FR-107, SC-105).
- **Consequence a comunicar**: un CAR con `not_in_mapbiomas` tiene hoy `embargoes_status="not_determinable"` (ver `build_detail`). Según el edge case de la spec, eso equivale a datos parciales, así que **un CNPJ con algún CAR no registrado en MapBiomas no puede ser Gold**: como mucho, Silver. Es coherente con la regla ("no sabemos si hay embargos"), pero conviene confirmarlo con el usuario. Está marcado en el quickstart.
- **Alternatives considered**: búsqueda pública solo con caché, sin consultar nunca MapBiomas. Se descarta porque la ficha de un CNPJ cuyos CARs nadie abrió en 24 h saldría siempre "Sem dados". El límite de búsquedas (R6) acota el coste.

## R6. Límite de búsquedas públicas

- **Decision**: limitador en memoria, ventana deslizante por IP, 30 búsquedas por hora (`public_search_limit_per_hour` en `Settings`). Al superarlo responde 429 con la cabecera `Retry-After` (en segundos) y `retry_after_s` en el cuerpo (FR-106). La IP se toma de `request.client.host`; si `trust_proxy_headers=true`, se usa la primera IP de `X-Forwarded-For`.
- **Rationale**: no añade dependencias y basta para un solo proceso (que es como se despliega hoy).
- **Limitation**: con varios workers o réplicas, cada proceso cuenta por separado. En ese momento habrá que mover el contador a un almacén compartido. Queda anotado en el plan.
- **Alternatives considered**: `slowapi` (dependencia extra para lo mismo), CAPTCHA (fricción para el comprador, que es justo a quien queremos servir).

## R7. Rutas y UI

- **Decision**: la búsqueda vive en su propia página, "Consultar CNPJ": `/consulta` (buscador) y `/consulta/:cnpj` (ficha que se puede compartir; FR-101). Se llega a ella desde:
  - una pestaña en la barra superior pública (`Header` en `App.tsx`);
  - una opción en la barra lateral del panel, que lleva a `/painel/consulta` y `/painel/consulta/:cnpj`. Es la misma página dentro del layout del panel, con la misma ficha pública;
  - un botón en la landing, "É comprador? Consulte o status do seu produtor".

  La landing **no** lleva el buscador (decisión del usuario, 2026-11-05): es una página que explica, y el botón separa claramente el camino del comprador del camino del productor. Componentes nuevos: `CnpjSearch`, `StatusBadge` (Gold, Silver, Bronze, Sem dados, con color y texto, sin depender solo del color) y `CnpjReportCard`. `StatusBadge` también se usa en `HomePage` (FR-114).
- **Validación en el navegador**: `frontend/src/lib/cnpj.ts` replica `normalize_cnpj` (14 dígitos y dígitos verificadores) para rechazar el CNPJ sin hacer la petición (FR-102, SC-103). El servidor vuelve a validar.
- **Aviso en el registro**: `RegisterPage` añade el texto "O resumo do seu CNPJ (nível e score) poderá ser consultado publicamente; códigos de CAR e mapas não." (supuesto de visibilidad de la spec).

## R8. Privacidad del contrato público

- **Decision**: el esquema de respuesta pública (`PublicCnpjReport`) es un modelo **separado** que no reutiliza `CarSummary` ni `Me`, para que los campos `car_code`, `geometry` o `email` no puedan aparecer por accidente (FR-105, SC-104). Un test de contrato comprueba que esas claves no aparecen en ningún nivel del JSON.
