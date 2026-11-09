# Feature Specification: Embargos del IBAMA como respaldo cuando MapBiomas no los determina

**Feature Branch**: `006-regras-nivel` (se desarrolla en la misma rama, a pedido de la responsable)

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "implementa 2" — usar los embargos de datos abiertos del IBAMA como alternativa cuando MapBiomas falla (opción 2 de la revisión del CAR AM-1303304-4B3B1D8060024401A46135766447CBA8, que salía Silver solo por "Parte dos dados não pôde ser verificada").

## Contexto y decisiones (2026-11-08)

- **Problema verificado**: para los CARs **sin alertas**, los embargos se obtienen consultando a
  MapBiomas en un punto del interior del imóvel. Desde al menos el 2026-11-08 esa consulta responde
  error de servidor siempre que se piden datos de embargo (la misma consulta pidiendo solo el código
  del imóvel responde bien). Esos CARs quedan con embargos "indisponível" y la regla de nivel de la
  006 los marca "dados parciais" → **Silver**, aunque todo lo demás esté limpio. Casos reales:
  AM-1303304-…, PE-2600500-…, RO-1100205-… (los tres sin alertas; todas las demás fuentes en orden).
- **Fuente de respaldo**: la capa pública de **áreas embargadas del IBAMA** (Pamgia), con el
  polígono de cada área embargada, número del termo, proceso, fecha del embargo y área embargada.
  Se actualiza a diario (última alteración vista: 2026-11-07). Para el CAR de PA, que sí tiene
  embargos en MapBiomas, la capa del IBAMA devuelve **el mismo embargo** (proceso
  02048.000439/2012-63), y uno solo (MapBiomas lo repite 3 veces por diferencias de formato).
- Decisiones confirmadas con la responsable:
  1. **Cobertura**: si el IBAMA responde, los embargos cuentan como **verificados** y el CAR puede
     llegar a Gold. La interfaz indica que la base es **solo IBAMA** (no ICMBio ni órganos
     estatales) y la fecha de la consulta.
  2. **Vigencia**: la capa no indica si un embargo fue levantado o cancelado; **todo embargo que
     cuenta se trata como vigente** (→ Bronze por "embargo vigente").
  3. **Asociación al CAR**: es un **cruce geográfico** (el mismo método que usa MapBiomas), no un
     vínculo legal: la capa no trae el número de CAR. Solo cuenta un embargo si su superposición
     con el polígono del CAR es **≥ 0,1 ha**, para descartar roces de borde con vecinos. Se muestran
     las hectáreas superpuestas.
- **No cambia la regla de nivel** de la 006: solo cambia de dónde salen los embargos cuando
  MapBiomas no los da. Aun así afecta el nivel del panel **y** de la ficha pública (un CAR puede
  pasar de Silver a Gold o a Bronze), por eso se confirmó antes de implementar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nivel correcto de un CAR sin alertas cuando MapBiomas no da los embargos (Priority: P1)

El productor ve el nivel de un CAR sin alertas calculado con los embargos del IBAMA cuando MapBiomas
no puede informarlos, en lugar de quedar en Silver por "dados parciais".

**Why this priority**: es el error que motivó la feature: CARs limpios aparecen Silver sin motivo
real, en el panel y en la ficha pública.

**Independent Test**: con MapBiomas simulado devolviendo error en los embargos y el IBAMA simulado
con o sin áreas embargadas, el nivel y los motivos del CAR son los esperados.

**Acceptance Scenarios**:

1. **Given** un CAR sin alertas, MapBiomas sin poder determinar sus embargos y el IBAMA sin áreas
   embargadas que se superpongan ≥ 0,1 ha, **When** se calcula el nivel, **Then** los embargos
   constan como verificados con 0 embargos y, sin otros motivos, el CAR es **Gold** (sin "dados
   parciais").
2. **Given** el mismo CAR y un área embargada del IBAMA que se superpone ≥ 0,1 ha, **Then** el CAR
   es **Bronze** con el motivo "embargo vigente" y el número de embargos.
3. **Given** un área embargada del IBAMA que toca el CAR pero se superpone < 0,1 ha, **Then** no
   cuenta como embargo del CAR.
4. **Given** que MapBiomas no determina los embargos y el IBAMA tampoco responde, **Then** el
   comportamiento es el de hoy: embargos "indisponível" y motivo "dados parciais" (nunca "0
   embargos").
5. **Given** que MapBiomas sí determina los embargos, **Then** no se consulta al IBAMA y el
   resultado es el mismo que hoy.

---

### User Story 2 - Ver de dónde salen los embargos (Priority: P1)

En el detalle del CAR, el productor ve que los embargos vienen del IBAMA (y solo del IBAMA), con la
fecha de la consulta y, por cada embargo, el termo, el proceso, la fecha del embargo y las hectáreas
superpuestas con su imóvel.

**Why this priority**: principio VII (todo dato derivado indica base y fecha) y la decisión 1: un
"sin embargos" basado solo en el IBAMA debe decirlo.

**Independent Test**: con el IBAMA simulado, el detalle del CAR muestra la fuente, la fecha y los
datos de cada embargo, y ningún dato personal del embargado.

**Acceptance Scenarios**:

1. **Given** un CAR cuyos embargos vienen del IBAMA, **When** se abre el detalle, **Then** se ve
   que la base es "IBAMA (áreas embargadas)" con la fecha de la consulta, y una ayuda explica que es
   un cruce geográfico, que no incluye ICMBio ni órganos estatales y que la capa no indica embargos
   levantados.
2. **Given** un embargo del IBAMA asociado al CAR, **Then** se muestran el número del termo, el
   proceso, la fecha del embargo, el área embargada y las hectáreas superpuestas con el CAR.
3. **Given** cualquier vista (panel o ficha pública), **Then** nunca aparecen el nombre ni el
   CPF/CNPJ del embargado.

---

### User Story 3 - La ficha pública refleja el nivel corregido (Priority: P2)

El comprador ve en la ficha pública del CNPJ el mismo nivel que el productor, ya calculado con los
embargos del IBAMA cuando correspondan, sin ver listas de embargos.

**Why this priority**: es consecuencia directa de la US1 (misma regla, misma fuente de verdad); no
requiere trabajo de interfaz nuevo.

**Independent Test**: con MapBiomas sin embargos y el IBAMA simulado, el nivel público coincide con
el del panel y la respuesta pública no contiene datos de embargos individuales.

**Acceptance Scenarios**:

1. **Given** un CNPJ cuyos CARs pasan a Gold gracias al IBAMA, **Then** la ficha pública muestra el
   nivel corregido y solo contagens, nivel y fechas.

---

### Edge Cases

- **CAR sin polígono**: no se puede hacer el cruce; los embargos quedan "não determinável" como hoy.
- **El IBAMA devuelve muchas áreas** (CAR muy grande): se consideran todas las que se superponen;
  si la respuesta viene truncada por el límite de la fuente, el resultado se trata como no
  determinable (nunca como una lista incompleta presentada como completa).
- **El mismo embargo en varios polígonos** (mismo proceso, varias áreas): cuenta **una vez** (órgano +
  proceso), sumando las hectáreas superpuestas.
- **Embargo sin número de proceso**: se identifica por el número y la serie del termo.
- **El IBAMA responde con error o tarda demasiado**: se usa la última caché marcada como
  desactualizada; sin caché, "indisponível".
- **Polígono del IBAMA o del CAR inválido** (autointersecciones): se intenta corregir la geometría
  antes de medir; si no se puede, ese embargo cuenta (criterio conservador) y se registra en el log.
- **"Atualizar" (refresh)**: vuelve a intentar MapBiomas y, si falla, el IBAMA.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-701**: Cuando MapBiomas no pueda determinar los embargos de un CAR (indisponível o no
  determinable) y el CAR tenga polígono, el sistema MUST consultar las áreas embargadas del IBAMA
  que se crucen con el polígono del CAR.
- **FR-702**: Un área embargada del IBAMA MUST contar como embargo del CAR solo si su superposición
  con el polígono del CAR es ≥ 0,1 ha. El umbral MUST estar en un único lugar del backend.
- **FR-703**: Todo embargo del IBAMA que cuente MUST tratarse como vigente (sin fecha de
  levantamiento), y MUST alimentar la regla de nivel existente sin cambiarla: con ≥ 1 embargo, motivo
  "embargo vigente" (Bronze); con 0, los embargos constan como verificados (sin "dados parciais" por
  embargos).
- **FR-704**: Los embargos del IBAMA MUST deduplicarse por órgano + proceso (o termo + serie si no
  hay proceso), sumando las hectáreas superpuestas, con la misma función de deduplicación que el
  resto de los embargos.
- **FR-705**: Si el IBAMA no responde, MUST mantenerse el estado actual ("indisponível" → "dados
  parciais"); nunca MUST presentarse como 0 embargos. La consulta MUST tener timeout y su resultado
  MUST guardarse en la caché del CAR con fecha.
- **FR-706**: Si MapBiomas determina los embargos, el sistema MUST NOT consultar al IBAMA.
- **FR-707**: El detalle del CAR MUST indicar la fuente de los embargos ("MapBiomas Alerta" o
  "IBAMA – áreas embargadas") y la fecha de la consulta; para el IBAMA MUST incluir una ayuda que
  diga que es un cruce geográfico, solo del IBAMA (no ICMBio ni órganos estatales) y que la capa no
  indica embargos levantados.
- **FR-708**: Por cada embargo del IBAMA, el detalle MUST mostrar número y serie del termo, proceso,
  fecha del embargo, área embargada y hectáreas superpuestas con el CAR.
- **FR-709**: El sistema MUST NOT pedir, guardar ni mostrar el nombre ni el CPF/CNPJ del embargado.
- **FR-710**: La ficha pública MUST reflejar el nivel calculado con esta fuente y MUST seguir sin
  incluir listas de embargos ni datos individuales.
- **FR-711**: La página "Entenda o nível" MUST mencionar que, cuando MapBiomas no informa los
  embargos, se usan las áreas embargadas del IBAMA (cruce geográfico ≥ 0,1 ha).
- **FR-712**: Los textos de interfaz MUST estar en pt-BR y MUST NOT usar "ilegal" ni "crime".

### Key Entities

- **Embargo (existente)**: órgano, proceso, área, fecha de registro, fecha de levantamiento,
  descripciones. Se amplía con: **fuente** del dato (MapBiomas o IBAMA), **termo** (número y serie)
  y **hectáreas superpuestas con el CAR** (solo IBAMA).
- **Estado de los embargos del CAR (existente)**: ok / indisponível / não determinável. Se amplía
  con la **fuente** que lo determinó y la fecha de consulta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-701**: Los 3 CARs de la cuenta de prueba que hoy son Silver solo por embargos no verificados
  (AM-1303304, PE-2600500, RO-1100205) dejan de mostrar "Parte dos dados não pôde ser verificada"
  tras pulsar "Atualizar", siempre que el IBAMA responda.
- **SC-702**: Para un CAR con embargos conocidos en MapBiomas (PA-1505031), la consulta al IBAMA
  encuentra el mismo embargo (mismo proceso) y lo cuenta una sola vez.
- **SC-703**: El detalle de un CAR carga en el mismo tiempo percibido que hoy: la consulta extra
  solo ocurre cuando MapBiomas falla y no agrega más de unos segundos en el peor caso.
- **SC-704**: Ninguna respuesta (panel ni pública) contiene nombre ni CPF/CNPJ del embargado
  (verificado por test automático).
- **SC-705**: Con el IBAMA caído, ningún CAR muestra "0 embargos" que no esté confirmado.

## Assumptions

- **Vigencia (confirmada, 2026-11-08)**: la capa del IBAMA es la lista pública de áreas embargadas y
  se trata como lista de embargos vigentes; no se cruza con el CSV de termos de embargo para descartar
  cancelados. Si se comprueba que la capa incluye embargos levantados, habrá que revisar esta decisión.
- **Asociación (confirmada)**: cruce geográfico con umbral de 0,1 ha; puede haber falsos positivos
  (embargo de un vecino que entra > 0,1 ha por imprecisión del dibujo) y falsos negativos (embargos
  sin polígono en la capa). Se acepta, igual que con MapBiomas.
- **Cobertura (confirmada)**: solo IBAMA. La capa del ICMBio publicada es una foto de 2022 y no se usa.
  No hay fuente de embargos estatales.
- La capa del IBAMA es pública, sin credenciales, y se consulta solo desde el backend (principio I).
- La caché del CAR (24 h) guarda también el resultado del IBAMA; no hace falta tabla nueva.
- MapBiomas sigue siendo la fuente principal: cuando vuelva a responder, se usa de nuevo sin cambios.
