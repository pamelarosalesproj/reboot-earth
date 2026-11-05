# Feature Specification: Panel del productor por CAR

**Feature Branch**: `001-producer-car-dashboard`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "El productor se registra con su email, CNPJ y uno o más CARs. Cuando el productor entra, puede ver por cada CAR: la forma del polígono, el número de alertas de desmatamento y la cantidad de embargos (posiblemente por alerta). Esa información la debe traer de MapBiomas Alerta. Generar un frontend básico con TypeScript y un backend básico con Python." (fuente: `intent.md`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registro del productor (Priority: P1)

Un productor rural crea su cuenta indicando solo su email, su CNPJ y una contraseña. No necesita tener a mano los códigos de CAR para registrarse: tras crear la cuenta entra directamente a su panel, donde añade sus CARs (ver User Story 4). *(Cambio solicitado por el usuario el 2026-11-05: antes los CARs se pedían en el registro.)*

**Why this priority**: es la puerta de entrada a todo el producto; un registro corto reduce el abandono.

**Independent Test**: registrar un productor con email, CNPJ `04.654.691/0001-06` y contraseña, cerrar sesión y volver a entrar; la cuenta existe y el panel muestra la invitación a añadir el primer CAR.

**Acceptance Scenarios**:

1. **Given** un visitante sin cuenta, **When** introduce un email válido, un CNPJ válido y una contraseña de al menos 8 caracteres, **Then** se crea la cuenta y el productor entra a su panel.
2. **Given** un productor recién registrado sin CARs, **When** entra al panel, **Then** ve un mensaje que lo invita a añadir su primer CAR, con el campo para hacerlo.
3. **Given** el formulario de registro, **When** el CNPJ tiene dígitos verificadores incorrectos, **Then** el sistema rechaza el registro e indica qué campo corregir.
4. **Given** el formulario de registro, **When** MapBiomas Alerta no está disponible, **Then** el registro funciona igualmente (no depende de MapBiomas).
5. **Given** un email ya registrado, **When** alguien intenta registrarse con él, **Then** el sistema rechaza el registro e invita a iniciar sesión.

---

### User Story 2 - Ver resumen de cada CAR al entrar (Priority: P1)

Al iniciar sesión, el productor ve un panel con una tarjeta por cada CAR asociado. Cada tarjeta muestra el polígono de la propiedad dibujado sobre un mapa, el número de alertas de desmatamento que cruzan el CAR y el número de embargos registrados en el CAR.

**Why this priority**: Es el valor central del producto: que el productor conozca de un vistazo la situación ambiental de sus propiedades.

**Independent Test**: Con una cuenta que tenga el CAR `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0`, iniciar sesión y verificar que la tarjeta muestra el polígono, el número de alertas y el número de embargos coincidentes con los datos de MapBiomas Alerta para ese CAR.

**Acceptance Scenarios**:

1. **Given** un productor con 2 CARs, **When** inicia sesión, **Then** ve 2 tarjetas, una por CAR, identificadas por su código.
2. **Given** una tarjeta de CAR, **When** se carga, **Then** muestra la forma del polígono de la propiedad sobre un mapa, ajustado para que la propiedad completa sea visible.
3. **Given** una tarjeta de CAR, **When** se carga, **Then** muestra el número total de alertas de desmatamento que cruzan ese CAR.
4. **Given** una tarjeta de CAR, **When** se carga, **Then** muestra el número total de embargos (distintos) registrados en ese CAR.
5. **Given** un CAR sin alertas ni embargos, **When** se carga su tarjeta, **Then** muestra "0 alertas" y "0 embargos" de forma explícita (no vacío).

---

### User Story 3 - Detalle de alertas y embargos por alerta (Priority: P2)

Desde la tarjeta de un CAR, el productor abre el detalle y ve la lista de alertas de desmatamento: código de alerta, fecha de detección, área afectada dentro del CAR y cuántos embargos están asociados a cada alerta. También ve la lista de embargos del CAR con su órgano emisor, número de proceso, área y fecha.

**Why this priority**: Aporta contexto para actuar (p. ej. defenderse de un embargo o entender una alerta), pero el resumen de la US2 ya entrega valor por sí solo.

**Independent Test**: Abrir el detalle de un CAR con alertas y comprobar que la lista y los conteos por alerta coinciden con MapBiomas Alerta.

**Acceptance Scenarios**:

1. **Given** un CAR con alertas, **When** el productor abre el detalle, **Then** ve cada alerta con código, fecha de detección, área dentro del CAR (ha) y número de embargos asociados.
2. **Given** un CAR con embargos, **When** el productor abre el detalle, **Then** ve cada embargo con órgano emisor (IBAMA, ICMBio u órgano estatal), número de proceso, área embargada (ha) y fecha de registro, sin duplicados del mismo proceso.
3. **Given** el detalle de un CAR, **When** el productor vuelve atrás, **Then** regresa al panel con todas sus tarjetas.

---

### User Story 4 - Añadir y gestionar los CARs desde el panel (Priority: P1)

Ya dentro de la plataforma, el productor añade los CARs de sus propiedades uno a uno, y puede quitar los que ya no gestiona. Es la única forma de asociar CARs a la cuenta.

**Why this priority**: sube a P1 porque, sin CARs en el registro, es imprescindible para que el panel (US2) muestre algo.

**Independent Test**: con una cuenta sin CARs, añadir `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` desde el panel y comprobar que aparece su tarjeta; quitarlo y comprobar que se vuelve a la invitación a añadir un CAR.

**Acceptance Scenarios**:

1. **Given** un productor autenticado, **When** añade un CAR con formato válido, **Then** aparece una nueva tarjeta para ese CAR.
2. **Given** un productor, **When** introduce un CAR con formato inválido, **Then** el sistema lo señala y no lo añade.
3. **Given** un CAR con formato válido que MapBiomas Alerta no tiene registrado, **When** el productor lo añade, **Then** el CAR se asocia y su tarjeta indica "sin registro en MapBiomas (sin alertas)".
4. **Given** MapBiomas Alerta no disponible, **When** el productor añade un CAR, **Then** el sistema pide reintentar más tarde y no lo añade.
5. **Given** un productor con varios CARs, **When** quita uno, **Then** su tarjeta desaparece y los demás permanecen.
6. **Given** un productor con un único CAR, **When** lo quita, **Then** el panel vuelve a mostrar la invitación a añadir un CAR.

---

### User Story 5 - Página inicial que explica la plataforma (Priority: P3)

Un visitante que llega a la plataforma sin sesión ve una página inicial pública que explica en lenguaje sencillo qué hace la plataforma: consultar, por cada CAR propio, el polígono de la propiedad, las alertas de desmatamento y los embargos, con datos de MapBiomas Alerta. También explica cómo funciona en pocos pasos (registrarse con email, CNPJ y CARs → entrar → ver el panel) y ofrece accesos directos a registrarse e iniciar sesión.

**Why this priority**: mejora la comprensión y la conversión de visitantes, pero el producto funciona sin ella (se puede entrar directo por registro o login).

**Independent Test**: abrir la dirección principal de la plataforma sin sesión y comprobar que se muestra la explicación, los pasos y los dos accesos (registrarse e iniciar sesión), y que cada uno lleva a su pantalla.

**Acceptance Scenarios**:

1. **Given** un visitante sin sesión, **When** abre la dirección principal, **Then** ve la página inicial con el propósito de la plataforma, qué información muestra por CAR, de dónde provienen los datos y cómo empezar.
2. **Given** la página inicial, **When** el visitante pulsa "Registrarse", **Then** llega al formulario de registro.
3. **Given** la página inicial, **When** el visitante pulsa "Iniciar sesión", **Then** llega a la pantalla de login.
4. **Given** un productor con sesión activa, **When** abre la página inicial, **Then** ve un acceso "Ir al panel" en lugar de los de registro y login.

---

### User Story 6 - Inicio con barra lateral y números grandes (Priority: P1)

Al entrar, el productor ve un panel con una barra lateral a la izquierda (su avatar, su email y CNPJ, y las opciones "Início" y "Meus CARs"). La página de inicio muestra tres números grandes: CARs registrados, alertas de desmatamento y embargos, sumando todos sus CARs. *(Solicitado por el usuario el 2026-11-05.)*

**Why this priority**: es lo primero que ve el productor; resume su situación de un vistazo.

**Independent Test**: con el CAR de referencia en la cuenta, al entrar se ve "1" CAR, "3" alertas y "0" embargos; "Meus CARs" en la lateral lleva a las tarjetas.

**Acceptance Scenarios**:

1. **Given** un productor autenticado, **When** entra al panel, **Then** ve la barra lateral con su avatar, email, CNPJ y las opciones "Início" y "Meus CARs", y la página de inicio con los tres números.
2. **Given** dos CARs del productor cruzados por la misma alerta o con el mismo embargo, **When** se calculan los totales, **Then** esa alerta o embargo se cuenta una sola vez.
3. **Given** un CAR sin datos disponibles (MapBiomas caído y sin caché), **When** se muestra el inicio, **Then** los totales indican cuántos CARs quedaron fuera en lugar de mostrar un total engañoso.
4. **Given** un productor sin CARs, **When** entra al inicio, **Then** ve la invitación a añadir su primer CAR.
5. **Given** una pantalla de móvil, **When** se abre el panel, **Then** la barra lateral pasa a ser una barra superior compacta.

---

### Edge Cases

- **MapBiomas no disponible o lento**: el panel se muestra igualmente; cada tarjeta afectada indica que los datos no están disponibles temporalmente y ofrece reintentar, sin bloquear las demás tarjetas.
- **CAR sin alertas**: la fuente principal de embargos es a través de las alertas; si el CAR no tiene alertas y no es posible determinar los embargos, la tarjeta muestra "embargos: no determinable" en lugar de "0", para no inducir a error.
- **CAR sin geometría**: la tarjeta muestra los conteos y un aviso de que el polígono no está disponible.
- **Embargos duplicados**: la fuente puede repetir un mismo embargo con distintos códigos o descripciones; se cuenta una sola vez por combinación de órgano emisor + número de proceso.
- **Alerta que cruza varios CARs**: el área mostrada es solo la parte de la alerta dentro del CAR consultado.
- **CAR repetido**: añadir un CAR que ya está en la cuenta se rechaza indicando que ya existe.
- **Cuenta sin CARs**: el panel muestra una invitación a añadir el primer CAR en lugar de una lista vacía.
- **Mismo CAR en varias cuentas**: se permite (p. ej. arrendatario y propietario); cada cuenta lo ve de forma independiente.
- **Polígonos grandes o multipolígonos**: se dibujan todas las partes de la propiedad.
- **Credenciales incorrectas al iniciar sesión**: mensaje genérico que no revela si el email existe.

## Requirements *(mandatory)*

### Functional Requirements

**Registro y acceso**

- **FR-001**: El sistema MUST permitir que un productor se registre solo con email, contraseña y CNPJ. El registro MUST NOT pedir CARs ni depender de MapBiomas Alerta.
- **FR-002**: El sistema MUST validar el formato del email y que sea único entre las cuentas.
- **FR-003**: El sistema MUST validar el CNPJ (14 dígitos, con o sin máscara `00.000.000/0000-00`, y dígitos verificadores correctos) y almacenarlo normalizado.
- **FR-004**: El sistema MUST validar el formato de cada código de CAR (`UF-CCCCCCC-HASH`) y consultarlo en MapBiomas Alerta antes de asociarlo (al añadirlo desde el panel). Si MapBiomas no lo tiene registrado (p. ej. CAR sin alertas), el CAR se acepta y se marca como "sin registro en MapBiomas"; si MapBiomas no responde, no se añade y se pide reintentar más tarde. (Confirmado por el usuario el 2026-11-05.)
- **FR-005**: El sistema MUST permitir iniciar y cerrar sesión con email y contraseña, y almacenar las contraseñas de forma no recuperable.
- **FR-006**: El sistema MUST mostrar a cada productor solo los CARs asociados a su propia cuenta.

**Panel por CAR**

- **FR-007**: Tras iniciar sesión, el sistema MUST mostrar una tarjeta por cada CAR asociado, identificada por el código del CAR (y su área en ha y estado/UF cuando estén disponibles).
- **FR-008**: Cada tarjeta MUST mostrar el polígono de la propiedad sobre un mapa, con encuadre automático a la extensión del polígono.
- **FR-009**: Cada tarjeta MUST mostrar el número total de alertas de desmatamento que cruzan el CAR, según MapBiomas Alerta.
- **FR-010**: Cada tarjeta MUST mostrar el número total de embargos distintos del CAR (deduplicados por órgano emisor + número de proceso).
- **FR-011**: El sistema MUST distinguir visualmente entre "0" (dato confirmado) y "no disponible / no determinable" (dato no obtenido).
- **FR-012**: El fallo al obtener los datos de un CAR MUST NOT impedir la visualización de los demás CARs.

**Detalle**

- **FR-013**: El sistema MUST ofrecer una vista de detalle por CAR con la lista de alertas: código, fecha de detección, área de la alerta dentro del CAR (ha) y número de embargos asociados a esa alerta.
- **FR-014**: La vista de detalle MUST listar los embargos del CAR con órgano emisor, número de proceso, área (ha) y fecha de registro.

**Gestión de CARs**

- **FR-015**: Un productor autenticado MUST poder añadir CARs (con las validaciones de FR-004) y quitar cualquiera de sus CARs, incluido el último. Con 0 CARs, el panel MUST invitar a añadir el primero.

**Datos externos**

- **FR-016**: Toda la información de polígonos, alertas y embargos MUST provenir de MapBiomas Alerta; el sistema no la edita ni la genera.
- **FR-017**: Las credenciales de acceso a MapBiomas Alerta MUST residir solo en el servidor y nunca exponerse al navegador del productor.
- **FR-018**: El sistema MUST indicar en cada tarjeta la fecha/hora en que se obtuvieron los datos y permitir actualizarlos manualmente.

**Inicio del panel**

- **FR-022**: Tras iniciar sesión, el sistema MUST mostrar una barra lateral con el avatar del productor (iniciales del email mientras no haya foto), su email y CNPJ, y las opciones "Início", "Meus CARs" y cerrar sesión.
- **FR-023**: La página "Início" MUST mostrar el total de CARs, de alertas de desmatamento únicas y de embargos únicos (órgano + proceso) de todos los CARs del productor, indicando cuántos CARs no tienen datos o tienen embargos no determinables.

**Página inicial**

- **FR-019**: El sistema MUST mostrar en la dirección principal una página pública, accesible sin sesión, que explique: el propósito de la plataforma, la información disponible por CAR (polígono, alertas de desmatamento, embargos), la fuente de datos (MapBiomas Alerta) y los pasos para empezar.
- **FR-020**: La página inicial MUST ofrecer accesos visibles a "Registrarse" e "Iniciar sesión"; con sesión activa, MUST mostrar en su lugar "Ir al panel".
- **FR-021**: La página inicial MUST ser legible en pantallas de móvil y de escritorio, y no depender de la disponibilidad de MapBiomas Alerta.

### Key Entities

- **Productor**: persona o empresa usuaria. Atributos: email (único), CNPJ (normalizado), credencial de acceso, fecha de registro. Tiene cero o más CARs (se añaden desde el panel).
- **CAR asociado**: vínculo entre un productor y un código de CAR. Atributos: código CAR, fecha en que se añadió. Un mismo código puede estar asociado a varios productores.
- **Resumen de CAR** (derivado de MapBiomas): código, UF, área (ha), polígono, total de alertas, total de embargos, momento de obtención.
- **Alerta de desmatamento** (derivado): código, fecha de detección, área total, área dentro del CAR, número de embargos asociados.
- **Embargo** (derivado): órgano emisor, número de proceso, área (ha), fecha de registro, descripciones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un productor completa el registro en menos de 1 minuto y añade su primer CAR en menos de 2 minutos más.
- **SC-002**: Tras iniciar sesión, el panel de un productor con hasta 5 CARs muestra todas las tarjetas con sus datos en menos de 10 segundos en condiciones normales de la fuente externa.
- **SC-003**: Para los CARs de prueba del proyecto, el número de alertas y de embargos mostrado coincide al 100% con lo que reporta MapBiomas Alerta para el mismo CAR.
- **SC-004**: El 100% de los registros con CNPJ inválido y de los CARs con formato inválido son rechazados con un mensaje que identifica el campo erróneo.
- **SC-005**: Si la fuente externa falla para un CAR, el resto del panel sigue siendo usable en el 100% de los casos.
- **SC-006**: El 90% de los productores de prueba identifican sin ayuda cuántas alertas y embargos tiene cada uno de sus CARs en la primera visita.
- **SC-007**: El 80% de los visitantes de prueba sabe explicar qué ofrece la plataforma tras leer la página inicial durante menos de 1 minuto, y llega al registro con un solo clic.

## Assumptions

- **Alcance "básico"**: es una primera versión mínima (MVP) para validar el concepto; no incluye recuperación de contraseña por email, verificación de email, roles de administrador ni notificaciones.
- **Autenticación**: email + contraseña, ya que la intención solo menciona el email; se define una contraseña como método razonable por defecto.
- **Titularidad del CAR**: en esta versión no se verifica que el CNPJ sea titular del CAR; la asociación es autodeclarada. El CNPJ se valida solo en formato y dígitos verificadores.
- **Embargos "por alerta"**: la intención no es concluyente; se muestra el total de embargos por CAR en la tarjeta y el desglose por alerta en el detalle, cubriendo ambas interpretaciones. Revisión de la fuente (2026-11-05): MapBiomas Alerta sí relaciona embargos con cada alerta, de dos formas distintas: (a) embargos cuya área **se superpone a la propia alerta** y (b) embargos registrados en **los CARs que la alerta cruza**, aunque no toquen la alerta. El "número de embargos asociados a la alerta" (FR-013) usa la relación (a), que es la que vincula el embargo con ese desmatamento concreto; la relación (b) equivale al embargo del CAR y ya se muestra en la tarjeta. Pendiente de validar con un CAR de prueba que tenga embargos (los CARs de ejemplo actuales tienen 0).
- **Fuente de datos**: se usa la API de MapBiomas Alerta (entorno configurado actualmente en el proyecto, `staging`), con una cuenta de servicio del proyecto. Los scripts existentes (`mapbiomas_api.py`) ya demuestran cómo obtener polígono, alertas y embargos por CAR y sirven de referencia.
- **Frescura de datos**: los datos pueden guardarse temporalmente para no repetir consultas en cada visita; una antigüedad de hasta 24 horas es aceptable, con actualización manual disponible.
- **CAR de prueba de referencia**: `PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0` (UF PE, SICAR_IRU, 264,23 ha). Según los datos descargados el 2026-11-05 (`PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0_completo.json`), tiene 3 alertas (1571779, 1581449, 1580505) y 0 embargos, tanto superpuestos a las alertas como en el CAR. Sirve para validar el caso "CAR con alertas y sin embargos" (tarjeta con "3 alertas" y "0 embargos"). Falta encontrar un CAR con embargos para cubrir ese caso.
- **Idioma de la interfaz**: portugués de Brasil por ser el mercado objetivo (productores con CAR/CNPJ); los textos se pueden adaptar.
- **Página inicial**: contenido estático y básico (sin gestor de contenidos, blog, precios ni formulario de contacto). Textos en el mismo idioma que el resto de la interfaz.
- **Restricción técnica solicitada**: el usuario pidió explícitamente un frontend básico en TypeScript y un backend básico en Python; se respetará en la fase de planificación.
- **Fuera de alcance**: datos DOF/IBAMA de transporte forestal (`dof_ibama.py`), productores con CPF en lugar de CNPJ, y app móvil nativa.
