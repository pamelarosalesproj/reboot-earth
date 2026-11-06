# ELO Rural Constitution

## Core Principles

### I. Fuentes externas solo desde el servidor

- Las credenciales de MapBiomas Alerta, y de cualquier otra fuente externa, MUST residir solo en
  el backend, leerse de la configuración (`.env` / entorno) y nunca versionarse ni registrarse en
  logs.
- El navegador MUST NOT llamar directamente a fuentes externas: toda consulta pasa por el API
  propio, que actúa de intermediario.

**Rationale**: protege las credenciales y permite controlar caché, límites y errores en un único
punto.

### II. Tolerancia a fallos de fuentes externas

- Toda consulta a una fuente externa MUST tener timeout y MUST guardar el resultado en caché junto
  con la fecha en que se obtuvo.
- Si la fuente no responde, el sistema MUST servir la última caché marcada como desactualizada
  (`stale`). Si no hay caché, MUST mostrar "no disponible" con la opción de reintentar.
- El fallo de un elemento (un CAR, una tarjeta) MUST NOT bloquear la vista completa ni el resto de
  los elementos.
- La UI y el API MUST distinguir entre `0` (dato confirmado) y "no disponible / no determinable"
  (`null` + estado). Ningún "no disponible" puede presentarse como cero.
- Las rutas públicas MUST NOT devolver error por la caída de una fuente externa cuando pueden
  responder con datos en caché o con un estado "sin datos".

**Rationale**: MapBiomas Alerta tiene caídas reales (p. ej. 502 el 2026-11-05). Para el usuario,
un cero falso es peor que un "no disponible" honesto.

### III. Privacidad por agregación

- La información accesible sin sesión MUST limitarse a datos agregados por CNPJ: nivel, score,
  conteos y fechas.
- Las respuestas públicas MUST NOT incluir códigos de CAR, polígonos/geometrías, email, ids de
  cuenta ni listas de alertas o embargos.
- Las respuestas públicas MUST usar modelos de respuesta propios, que no reutilicen los modelos
  internos o autenticados. Un test MUST comprobar que esos campos no aparecen en ningún nivel de
  la respuesta.
- Cada productor MUST ver solo los CARs de su propia cuenta.
- Los endpoints públicos MUST tener un límite de consultas para impedir la extracción masiva de
  datos.

**Rationale**: la plataforma sirve a productores y a compradores. Los compradores necesitan el
status, pero no el detalle de las propiedades de un tercero.

### IV. Una sola fuente de verdad para las reglas de negocio

- Cada regla de negocio (deduplicación de alertas por código y de embargos por órgano + proceso,
  agregación por CAR o CNPJ, cálculo de nivel y score) MUST implementarse en un único lugar del
  backend y reutilizarse en todas las vistas que la muestran.
- Dos vistas que muestran el mismo dato (p. ej. el panel del productor y la ficha pública) MUST
  obtenerlo del mismo código, y MUST existir un test que verifique que coinciden.
- Las reglas MUST implementarse como funciones puras siempre que sea posible, para testearlas sin
  red ni base de datos.

**Rationale**: las discrepancias entre vistas destruyen la confianza en un indicador de riesgo.

### V. Simplicidad (YAGNI)

- No se añade una dependencia, tabla, servicio ni capa de abstracción sin una necesidad
  demostrada por un requisito de la spec actual.
- Los valores que se pueden calcular de forma barata a partir de datos existentes MUST calcularse
  en el momento en lugar de persistirse.
- Toda excepción MUST justificarse en la sección "Complexity Tracking" del plan.
- Las limitaciones conocidas de una solución simple (p. ej. un rate limit en memoria con un solo
  proceso) MUST documentarse en el plan.

**Rationale**: es un proyecto pequeño, en etapa temprana y con requisitos aún cambiantes. Cada
pieza extra se paga en mantenimiento.

### VI. Calidad verificable

- Los tests MUST NOT depender de la red ni de la disponibilidad de MapBiomas: las fuentes
  externas MUST simularse.
- Antes de integrar un cambio MUST pasar:
  - backend: `uv run ruff check .` y `uv run pytest`;
  - frontend: `npm run build` y `npm test`.
- Cada requisito de comportamiento ante fallos (principio II) y de privacidad (principio III)
  MUST tener al menos un test automático.
- Cada feature MUST incluir un `quickstart.md` con su validación manual de extremo a extremo.

**Rationale**: la fuente de datos es inestable, así que los tests tienen que ser deterministas y
cubrir los caminos de fallo, no solo el camino feliz.

### VII. Fidelidad de los datos e idioma

- Los datos de origen (polígonos, alertas, embargos) MUST mostrarse tal como los entrega la
  fuente. El sistema no los edita, corrige ni genera.
- Todo dato derivado (conteos, nivel, score) MUST indicar en qué se basa y la fecha de los datos
  usados.
- Un indicador provisional MUST identificarse como tal.
- La interfaz de usuario MUST estar en portugués de Brasil (pt-BR).
- Las specs, planes y documentación del proyecto se escriben en español.

**Rationale**: la plataforma informa decisiones comerciales sobre terceros, así que cada número
tiene que ser trazable a su fuente. El mercado objetivo es brasileño y el equipo trabaja en
español.

## Restricciones adicionales

- **Stack**: backend en Python 3.12 (FastAPI + SQLModel/SQLite, gestionado con `uv`) y frontend en
  TypeScript (React + Vite). Cambiar de stack requiere una enmienda.
- **Seguridad**: contraseñas almacenadas de forma no recuperable; sesión por cookie `HttpOnly`;
  `COOKIE_SECURE=true` obligatorio en producción con HTTPS.
- **Identificadores**: CNPJ y CAR MUST validarse (formato y dígitos verificadores en el caso del
  CNPJ) y almacenarse normalizados en el backend. El frontend MAY validar antes de enviar para dar
  feedback inmediato, pero el backend siempre vuelve a validar.

## Flujo de desarrollo y gates de calidad

- Cada feature sigue el flujo Spec Kit:
  `/speckit-specify` → (`/speckit-clarify`) → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`.
- El "Constitution Check" de cada `plan.md` MUST evaluar los principios I–VII. Una violación
  bloquea el paso a tareas, salvo que esté justificada en "Complexity Tracking".
- Las decisiones tomadas como supuestos durante la especificación MUST quedar en la sección
  "Assumptions" de la spec y confirmarse con el usuario antes de implementarse cuando afecten a la
  privacidad o al alcance.
- Los cambios de alcance solicitados por el usuario se registran en la spec con su fecha.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica del proyecto. Toda spec, plan, tarea y
  revisión de código MUST verificar su cumplimiento.
- **Enmiendas**: se proponen con `/speckit-constitution`, incluyen el Sync Impact Report y la
  aprueba la persona responsable del proyecto. Si la enmienda invalida algo ya implementado, MUST
  acompañarse de las tareas de migración necesarias.
- **Versionado** (SemVer):
  - MAJOR: eliminar o redefinir un principio de forma incompatible.
  - MINOR: añadir un principio o sección, o ampliar materialmente una guía.
  - PATCH: aclaraciones y redacción.
- **Revisión de cumplimiento**: al cerrar cada feature se revisa que los tests exigidos por el
  principio VI existan y pasen.

**Version**: 1.0.1 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-06

*1.0.1 (2026-11-06): el proyecto pasa a llamarse ELO Rural (antes RebootEarth). Sin cambios en los principios.*
