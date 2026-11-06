# Feature Specification: Consulta pública de score por CNPJ

**Feature Branch**: `002-cnpj-score-search`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "una búsqueda basica por cnpj donde indique el score de ese cpnj, ese score lo calcularemos despues. porque esta plataforma debe ser tanto para el productor y para el comprador ( que no necesita registrarse) pero sí saber el status, como propones ?"

> **Cambio (2026-11-06, solicitado por el usuario):** la explicación del nivel era confusa ("Há embargos registrados." + "Indicador preliminar… não é o score definitivo." + "Score em cálculo"). Ahora: (1) el motivo usa los números de la regla, por ejemplo "Porque há 7 embargos registrados nos imóveis do CNPJ." (`Status` añade los agregados `alerts_count` y `embargoes_count`); (2) el aviso pasa a "Nível provisório: considera apenas alertas e embargos do MapBiomas Alerta."; (3) **el score solo se muestra cuando existe** (`disponivel`). Mientras tanto no aparece "Score em cálculo". Afecta a FR-103 y FR-112 y vale para el panel y la ficha pública.

## Propuesta

La plataforma pasa a tener dos públicos:

- **Productor** (con cuenta, ya existe en `001-producer-car-dashboard`): registra su CNPJ y sus CARs y ve el detalle completo.
- **Comprador** (sin cuenta, nuevo): es quien compra a un productor (frigorífico, trading, cooperativa, minorista) y quiere saber, antes de comprar, si ese proveedor presenta riesgo socioambiental. Escribe un CNPJ y ve un **resultado resumido**: el score, el status (**Gold**, **Silver**, **Bronze** o **Sem dados**) y la fecha de los datos.

El score es un **elemento independiente con su propio estado**. Esta feature define dónde se muestra y qué se muestra mientras no exista. El cálculo se especificará en otra feature. Así se puede publicar la búsqueda ya, mostrando "Score em cálculo", y conectar el cálculo después sin cambiar la experiencia del comprador.

El comprador ve solo información agregada por CNPJ. Nunca ve los códigos de CAR, los polígonos ni los datos de la cuenta del productor; ese detalle sigue siendo privado del productor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El comprador consulta un CNPJ sin registrarse (Priority: P1)

Un comprador entra a la plataforma y, sin crear una cuenta, llega a la página "Consultar CNPJ" desde el botón "É comprador? Consulte o status do seu produtor" de la página inicial o desde la pestaña "Consultar CNPJ" de la barra superior. Allí escribe el CNPJ de un proveedor y ve una ficha de resultado con: CNPJ formateado, score (o su estado si aún no existe), status (Gold / Silver / Bronze / Sem dados) y fecha/hora de los datos.

**Why this priority**: es la razón de que exista el lado comprador. Por sí sola aporta valor (saber si el proveedor está en la plataforma y en qué estado) aunque el score no esté calculado.

**Independent Test**: sin sesión, buscar `04.654.691/0001-06` (registrado en la plataforma) y un CNPJ válido no registrado; el primero muestra la ficha con su estado de score y su status, y el segundo muestra el status "Sem dados" con el motivo "CNPJ não cadastrado na plataforma".

**Acceptance Scenarios**:

1. **Given** un visitante sin sesión, **When** escribe un CNPJ válido de un productor registrado y busca, **Then** ve la ficha del CNPJ con su score o estado de score, su status y la fecha de los datos.
2. **Given** un visitante sin sesión, **When** escribe un CNPJ válido que ningún productor registró, **Then** ve el status "Sem dados" con el motivo "CNPJ não cadastrado na plataforma" y una explicación breve de que eso no indica ni riesgo ni ausencia de riesgo.
3. **Given** un visitante sin sesión, **When** escribe un CNPJ con formato o dígitos verificadores incorrectos, **Then** el sistema no busca e indica que el CNPJ no es válido.
4. **Given** un visitante sin sesión, **When** escribe el CNPJ con o sin máscara (`00.000.000/0000-00` o 14 dígitos), **Then** el resultado es el mismo.
5. **Given** un productor registrado sin ningún CAR, **When** un comprador busca su CNPJ, **Then** ve el status "Sem dados" con el motivo "nenhuma propriedade informada" y el score en estado "Não calculável".

---

### User Story 2 - Status Gold / Silver / Bronze / Sem dados (Priority: P1)

Cada CNPJ consultado muestra un status de cuatro niveles: **Gold**, **Silver**, **Bronze** o **Sem dados**. Mientras el cálculo del score no exista, el nivel se asigna con una regla provisional basada en las alertas y embargos que la plataforma ya tiene, para que la búsqueda sea útil desde el primer día. *(Niveles definidos por el usuario el 2026-11-05.)*

**Why this priority**: el usuario pidió explícitamente que el comprador "sí sepa el status". Sin esto, la búsqueda solo devolvería "Score em cálculo".

**Independent Test**: con el score en estado "Em cálculo", buscar CNPJs de productores cuyos CARs tengan (a) ni alertas ni embargos, (b) alertas sin embargos, (c) algún embargo, (d) datos no disponibles, y un CNPJ no registrado; verificar que cada uno muestra Gold, Silver, Bronze, Sem dados y Sem dados, respectivamente.

**Acceptance Scenarios**:

1. **Given** un productor cuyos CARs no tienen alertas ni embargos según los últimos datos, **When** se busca su CNPJ, **Then** el status es **Gold**.
2. **Given** un productor con al menos una alerta de desmatamento y ningún embargo, **When** se busca su CNPJ, **Then** el status es **Silver**.
3. **Given** un productor con al menos un embargo, tenga o no alertas, **When** se busca su CNPJ, **Then** el status es **Bronze**.
4. **Given** un productor del que no se pudieron obtener los datos de ninguno de sus CARs, **When** se busca su CNPJ, **Then** el status es **Sem dados** con el motivo "dados indisponíveis".
5. **Given** un status, **When** el comprador lo ve, **Then** aparece con una explicación corta de qué significa ese nivel y el aviso de que, mientras no exista el score, se basa solo en alertas y embargos de MapBiomas Alerta.

---

### User Story 3 - El productor ve su propio score y cómo lo ve el comprador (Priority: P2)

El productor autenticado ve en su página "Início" el mismo score y status que vería un comprador al buscar su CNPJ, para saber cómo lo perciben.

**Why this priority**: da transparencia al productor y le permite corregir su situación (p. ej. añadir CARs que faltan). No bloquea el lado comprador.

**Independent Test**: iniciar sesión como productor, comparar el score/status de "Início" con el resultado de la búsqueda pública del mismo CNPJ en una ventana sin sesión; deben coincidir.

**Acceptance Scenarios**:

1. **Given** un productor autenticado, **When** entra a "Início", **Then** ve su score (o estado de score) y su status con la misma etiqueta y fecha que el resultado público.
2. **Given** un productor autenticado, **When** añade o quita un CAR, **Then** el score/status público refleja el cambio en la siguiente consulta.

---

### Edge Cases

- **Dos cuentas con el mismo CNPJ**: el resultado público agrega los CARs de todas las cuentas con ese CNPJ, sin duplicar CARs repetidos.
- **CNPJ de filial vs. matriz**: se busca por el CNPJ completo de 14 dígitos; una filial (otro sufijo `/0002-xx`) es un CNPJ distinto y no se agrega con la matriz.
- **MapBiomas caído durante la búsqueda**: se muestran los últimos datos guardados con su fecha. Si nunca se obtuvieron, el status es "Sem dados" con el motivo "dados indisponíveis". La búsqueda nunca falla por completo por culpa de MapBiomas.
- **Datos parciales** (algunos CARs con datos y otros no): el status se calcula con los CARs con datos y la ficha indica "dados parciais: X de Y propriedades". Un CNPJ con datos parciales no puede ser Gold: si los CARs con datos no tienen alertas ni embargos, el status es Silver, porque los CARs sin datos podrían tenerlos.
- **Embargos no determinables** en algún CAR (feature 001): se tratan igual que un CAR sin datos a efectos del nivel.
- **Búsquedas masivas automatizadas**: se limita la cantidad de búsquedas por visitante en un periodo para impedir la extracción masiva de la base.
- **Productor con 0 CARs**: ver User Story 1, escenario 5.

## Requirements *(mandatory)*

### Búsqueda pública

- **FR-101**: El sistema MUST ofrecer la búsqueda por CNPJ en una página propia, "Consultar CNPJ", accesible sin sesión y con una dirección que se pueda compartir (p. ej. un enlace a la ficha de un CNPJ). Se llega a ella desde:
  - una pestaña "Consultar CNPJ" en la barra superior pública;
  - una opción "Consultar CNPJ" en la barra lateral del panel del productor, que muestra la misma ficha pública, sin datos adicionales;
  - un botón en la página inicial (FR-115).

  La página inicial MUST NOT contener el buscador en sí. *(Decidido por el usuario el 2026-11-05.)*
- **FR-102**: La búsqueda MUST aceptar el CNPJ con o sin máscara y validar los dígitos verificadores antes de buscar, con las mismas reglas del registro (FR-003).
- **FR-103**: Para un CNPJ registrado, la ficha MUST mostrar: CNPJ formateado, score o estado de score, status (Gold / Silver / Bronze / Sem dados), número de propiedades (CARs) consideradas y fecha/hora de los datos más antiguos usados.
- **FR-104**: Para un CNPJ válido no registrado, el sistema MUST mostrar el status "Sem dados" con el motivo "CNPJ não cadastrado na plataforma", indicando que la ausencia no equivale a riesgo ni a ausencia de riesgo.
- **FR-105**: El resultado público MUST NOT mostrar códigos de CAR, polígonos, el email del productor ni ningún otro dato de la cuenta. Solo muestra la información agregada definida en FR-103.
- **FR-106**: El sistema MUST limitar las búsquedas públicas por visitante (por defecto: 30 por hora) y, al superar el límite, indicar cuándo puede volver a buscar.
- **FR-107**: La búsqueda MUST seguir funcionando cuando MapBiomas Alerta no responda, usando los últimos datos guardados (FR-018 de la feature 001), e indicar su fecha.

### Score

- **FR-108**: Cada CNPJ registrado MUST tener un score con uno de estos estados: "Em cálculo" (aún no existe método de cálculo), "Não calculável" (sin CARs o sin datos) o "Disponível" (valor calculado, con fecha y versión del método).
- **FR-109**: Hasta que exista el método de cálculo, todos los CNPJs con CARs MUST mostrar el score en estado "Em cálculo". La forma de mostrar el valor del score cuando esté "Disponível" se define en la feature que especifique el cálculo.
- **FR-110**: El cambio de "Em cálculo" a "Disponível" MUST NOT requerir cambios en la búsqueda ni en la ficha más allá de mostrar el valor.

### Status

- **FR-111**: Cada ficha MUST mostrar exactamente uno de cuatro niveles: **Gold**, **Silver**, **Bronze** o **Sem dados**.
- **FR-111a**: Mientras el score esté "Em cálculo", el nivel MUST asignarse con esta regla provisional, evaluada en orden:
  1. **Sem dados**: CNPJ no registrado, sin CARs, o ningún CAR con datos (cada caso con su motivo visible).
  2. **Bronze**: ≥1 embargo único en cualquiera de sus CARs.
  3. **Silver**: ≥1 alerta de desmatamento, o datos parciales (ver Edge Cases).
  4. **Gold**: todos sus CARs con datos completos, sin alertas ni embargos.
- **FR-111b**: Cuando el score esté "Disponível", el nivel MUST derivarse del score según los umbrales que defina la feature del cálculo, y la regla provisional deja de aplicarse.
- **FR-112**: El status MUST ir acompañado de una explicación corta del nivel y, mientras se use la regla provisional, del aviso de que se basa solo en alertas y embargos de MapBiomas Alerta.
- **FR-113**: Los embargos y alertas MUST contarse con las mismas reglas de deduplicación de la feature 001 (embargos por órgano + proceso, alertas por código).

### Lado productor

- **FR-114**: La página "Início" del productor MUST mostrar su score/estado y su status con la misma información y fecha que la ficha pública de su CNPJ.
- **FR-115**: La página inicial pública MUST explicar los dos usos de la plataforma: el productor se registra para gestionar sus CARs, y el comprador consulta un CNPJ sin registrarse. Para el comprador, MUST mostrar un botón destacado "É comprador? Consulte o status do seu produtor" que lleva a la página "Consultar CNPJ".

### Key Entities

- **Consulta pública (Ficha de CNPJ)**: vista agregada de un CNPJ para cualquier visitante. Atributos: CNPJ, registrado sí/no, número de CARs considerados, CARs con datos, status, score, fecha de los datos. No contiene datos identificativos de CARs ni de la cuenta.
- **Score**: valoración de riesgo de un CNPJ. Atributos: estado (Em cálculo / Não calculável / Disponível), valor (solo si Disponível), fecha de cálculo, versión del método. Se asocia a un CNPJ, no a una cuenta.
- **Status**: nivel del CNPJ: Gold, Silver, Bronze o Sem dados, más el motivo cuando es Sem dados ("não cadastrado", "nenhuma propriedade informada", "dados indisponíveis") y el origen del nivel (regla provisional o score). Se recalcula cuando cambian los datos.
- **Productor** (existente): se relaciona con la ficha a través de su CNPJ; varias cuentas pueden compartir un CNPJ.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: Un comprador sin cuenta obtiene la ficha de un CNPJ en menos de 30 segundos desde que llega a la página inicial, sin registrarse.
- **SC-102**: El 95% de las búsquedas muestran el resultado en menos de 3 segundos cuando los datos ya están guardados.
- **SC-103**: El 100% de las búsquedas con CNPJ inválido se rechazan antes de buscar, con un mensaje claro.
- **SC-104**: El 0% de las fichas públicas exponen códigos de CAR, polígonos o datos de la cuenta del productor (verificado revisando las respuestas públicas).
- **SC-105**: Con MapBiomas Alerta caído, el 100% de las búsquedas de CNPJs ya consultados devuelven ficha con datos fechados, sin error.
- **SC-106**: Para el mismo CNPJ, el score/status del panel del productor y el de la ficha pública coinciden en el 100% de los casos.

## Assumptions

- **Comprador sin cuenta**: no se registra, no tiene historial ni favoritos en esta versión. Las alertas de cambio de status para el comprador quedan fuera de alcance.
- **Visibilidad** *(confirmado por el usuario el 2026-11-05, "por ahora sí"; puede revisarse más adelante, p. ej. para añadir opt-in)*: todo CNPJ registrado es consultable públicamente de forma agregada, sin opt-in del productor. Se asume que el registro de la feature 001 incluirá un aviso y la aceptación de que el resumen de su CNPJ será público. La justificación es que alertas y embargos ya son datos públicos en MapBiomas e IBAMA, y la ficha solo los agrega.
- **Niveles del status**: el usuario definió los cuatro niveles (Gold, Silver, Bronze, Sem dados) el 2026-11-05. La regla provisional que asigna cada nivel según alertas y embargos (FR-111a) fue **confirmada por el usuario el 2026-11-05**, incluido que un CAR sin registro en MapBiomas (embargos no determinables) impide llegar a Gold. Cuando exista el score, el nivel se derivará de él (FR-111b).
- **Titularidad**: igual que en la feature 001, la asociación CNPJ–CAR es autodeclarada. La ficha pública lo indica ("propriedades informadas pelo produtor").
- **CNPJs no registrados**: no se consultan fuentes externas para ellos en esta versión, solo se informa que no están registrados.
- **Idioma**: interfaz en portugués de Brasil, como en la feature 001.
- **Fuera de alcance**: el método de cálculo del score, búsqueda por nombre o razón social, búsqueda por CPF, consulta masiva o por archivo, y acceso por API para compradores.
