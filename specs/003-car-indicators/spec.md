# Feature Specification: Indicadores socioambientales en la tarjeta del CAR

**Feature Branch**: `003-car-indicators`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "agrega al card del CAR todas estas informaciones" — los indicadores validados con datos reales de 3 CARs el 2026-11-06 (alertas por situación legal, desmatamento después de 2020, reserva legal y APP, embargos vigentes y levantados, superposición con territorios, vegetación nativa remanescente, degradación DETER, focos de calor y manejo forestal SINAFLOR).

> **Cambio de alcance (2026-11-06, solicitado por el usuario):** los indicadores se muestran **solo en el detalle del CAR** ("Ver detalhes"), no en la tarjeta de "Meus CARs", porque la tarjeta quedaba demasiado cargada. La tarjeta vuelve a mostrar solo el mapa, las alertas y los embargos. Donde esta spec dice "tarjeta" para los bloques Riscos abertos y Contexto, léase "detalle del CAR". El resto de los requisitos no cambia.

## Contexto

Hoy la tarjeta del CAR muestra solo el número de alertas y de embargos. Así, una alerta autorizada o ya sancionada pesa igual que una sin explicación, y el productor no ve el contexto (vegetación, fuego, tala).

Esta feature **muestra** más información. **No cambia** la regla de niveles Gold, Silver y Bronze de la feature 002 ni la ficha pública: esos cambios quedan para otra feature, que necesita confirmación del usuario. La tarjeta separa:

- **Riscos abertos**: lo que hoy representa un riesgo vigente.
- **Contexto**: información útil que no indica, por sí sola, un problema.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver los riesgos abiertos de cada CAR (Priority: P1)

El productor abre "Meus CARs" y, en cada tarjeta, ve un bloque **Riscos abertos** con:
- las alertas por situación legal (n.º y ha);
- el desmatamento después de 2020;
- las alertas abiertas en reserva legal y en APP;
- los embargos vigentes;
- la superposición con tierra indígena o con una unidad de conservación de protección integral.

**Why this priority**: es lo que distingue un problema vigente de uno superado. Sin esto, todas las alertas parecen iguales.

**Independent Test**: con MapBiomas simulado, un CAR con 3 alertas pendientes (2 tocando APP, 27 ha en reserva legal) y otro con 3 alertas bajo embargo vigente muestran esas cifras en sus tarjetas.

**Acceptance Scenarios**:

1. **Given** un CAR con alertas, **When** el productor abre "Meus CARs", **Then** la tarjeta muestra las alertas agrupadas por situación (n.º y ha), cada alerta en una sola situación, según el orden de FR-302.
2. **Given** una alerta sin autorización, embargo, fiscalización ni suspensión registrados, **When** se muestra, **Then** su situación es "Sem autorização registrada" y en ningún lugar se la llama "ilegal".
3. **Given** un CAR con alertas detectadas antes y después del 31/12/2020, **When** se muestra la tarjeta, **Then** el desmatamento después de 2020 suma solo el área de las alertas posteriores.
4. **Given** un CAR sin alertas, **When** se muestra la tarjeta, **Then** los indicadores de alertas muestran "0" (dato confirmado), no "indisponível".

---

### User Story 2 - Ver el contexto ambiental del CAR (Priority: P2)

En la misma tarjeta, un bloque **Contexto** muestra:
- el % de vegetación nativa remanescente;
- los focos de calor de los últimos 12 meses;
- la degradación y la tala selectiva (DETER) desde 2021;
- la superposición con unidades de conservación de uso sostenible;
- el manejo forestal autorizado (SINAFLOR);
- las alertas superadas (autorizadas, con embargo levantado o suspendidas).

**Why this priority**: completa la lectura del CAR, pero no indica por sí solo un problema.

**Independent Test**: con las fuentes del INPE e IBAMA simuladas, un CAR de la Caatinga muestra "não se aplica" en DETER y SINAFLOR, y uno de la Amazonía muestra los valores correspondientes.

**Acceptance Scenarios**:

1. **Given** un CAR fuera del bioma Amazonía, **When** se muestra el contexto, **Then** la degradación DETER aparece como "Não se aplica a este bioma", nunca como "0".
2. **Given** un CAR fuera de la Amazônia Legal, **When** se muestra el contexto, **Then** el manejo forestal SINAFLOR aparece como "Não se aplica".
3. **Given** alertas DETER de corte selectivo, **When** se muestran, **Then** se distingue "corte seletivo com padrão de manejo" (geométrico) de "corte seletivo desordenado".
4. **Given** el % de vegetación nativa, **When** se muestra, **Then** va acompañado del aviso de que incluye desmatamento legal o histórico y de que no registra regeneración.

---

### User Story 3 - Ver la situación de cada alerta en el detalle del CAR (Priority: P2)

En el detalle del CAR, la tabla de alertas añade, para cada alerta:
- su situación legal;
- si es posterior a 2020;
- el área en reserva legal;
- si toca APP;
- la unidad de conservación que cruza, si cruza alguna.

**Why this priority**: permite verificar de dónde salen los números de la tarjeta.

**Independent Test**: el detalle de un CAR con alertas en un APA muestra el nombre del APA en esas alertas, con la situación de cada una.

**Acceptance Scenarios**:

1. **Given** el detalle de un CAR, **When** se abre, **Then** cada alerta muestra su situación y los campos anteriores, y la suma por situación coincide con la tarjeta.

---

### Edge Cases

- **Una fuente no responde** (MapBiomas, INPE o IBAMA): los indicadores de esa fuente muestran "indisponível" o la última consulta con fecha; el resto se muestra normalmente.
- **Una alerta cruza varios CARs**: se cuenta el área de la alerta dentro de este CAR. La reserva legal, la APP y las unidades de conservación vienen calculadas sobre la alerta completa, lo que se indica con una nota.
- **Un CAR que MapBiomas no tiene registrado**: los indicadores de alertas muestran "0" y los de embargos "não determinável", como hoy.
- **Un CAR que cruza varios biomas**: el % de vegetación se calcula sin contar dos veces las zonas donde los mapas de los biomas se superponen.
- **Datos de SINAFLOR aún no cargados** (primera ejecución): "indisponível", nunca "0".

## Requirements *(mandatory)*

### Alertas por situación

- **FR-301**: Cada alerta del CAR MUST tener exactamente una situación: `suspensa_judicial`, `embargo_vigente`, `autorizada`, `embargo_levantado`, `com_fiscalizacao` o `pendente`.
- **FR-302**: La situación MUST asignarse en este orden, y gana la primera que se cumpla:
  1. Suspendida judicialmente según MapBiomas.
  2. Cruza un área embargada y el CAR tiene algún embargo sin fecha de fin.
  3. Tiene área cubierta por un permiso de supresión o un plan de manejo.
  4. Cruza un área embargada y todos los embargos del CAR tienen fecha de fin.
  5. Tiene alguna acción de fiscalización registrada.
  6. En otro caso, `pendente`.
- **FR-303**: La tarjeta MUST mostrar, por situación, el n.º de alertas y la suma del área de esas alertas dentro del CAR (ha). En Riscos abertos van `embargo_vigente`, `com_fiscalizacao` y `pendente`; en Contexto, como "superadas", van `autorizada`, `embargo_levantado` y `suspensa_judicial`.
- **FR-304**: `pendente` MUST mostrarse como "Sem autorização registrada". La interfaz MUST NOT usar la palabra "ilegal" para una alerta.

### Otros riesgos abiertos

- **FR-305**: El desmatamento después de 2020 MUST ser la suma del área dentro del CAR de las alertas detectadas después del 31/12/2020, con el n.º de alertas.
- **FR-306**: MUST mostrarse el área en reserva legal (ha) y el n.º de alertas que tocan APP, contando **solo las alertas abiertas** (situaciones de Riscos abertos).
- **FR-307**: MUST mostrarse el n.º de embargos vigentes en Riscos abertos y el de levantados en Contexto.
- **FR-308**: La superposición de alertas con tierra indígena o con una unidad de conservación de protección integral (ha) MUST ir en Riscos abertos; la superposición con unidades de uso sostenible, en Contexto, con el nombre de la unidad cuando exista.

### Contexto

- **FR-309**: El % de vegetación nativa remanescente MUST calcularse como 1 − (área desmatada según el mapeo oficial anual del INPE ÷ área del CAR), sin contar dos veces las zonas donde se superponen los mapas de distintos biomas. MUST incluir el aviso de que el valor abarca desmatamento legal o histórico y no registra regeneración.
- **FR-310**: Los focos de calor MUST contar los focos del satélite de referencia dentro del polígono del CAR en los últimos 12 meses.
- **FR-311**: La degradación DETER MUST mostrar n.º, ha y fecha más reciente por clase, desde el 01/01/2021, solo si el CAR cruza el bioma Amazonía. Si no, "Não se aplica a este bioma". El corte selectivo geométrico MUST etiquetarse como "padrão de manejo" y el desordenado como "desordenado".
- **FR-312**: El manejo forestal MUST mostrar el n.º de autorizaciones y el volumen autorizado (m³) del CAR en el registro oficial de planes de manejo de la Amazônia Legal, solo para CARs de la Amazônia Legal. Si no, "Não se aplica".

### Transversales

- **FR-313**: Cada indicador MUST distinguir entre un valor (incluido 0), "indisponível" (la fuente no respondió y no hay caché) y "não se aplica".
- **FR-314**: Los indicadores MUST guardarse en caché por CAR con su fecha de obtención, y MUST servirse marcados como desactualizados cuando una fuente no responda (constitución II). Cada fuente se resuelve de forma independiente.
- **FR-315**: La tarjeta MUST mostrar las fuentes y la fecha de los datos de cada bloque (constitución VII).
- **FR-316**: Esta feature MUST NOT cambiar la regla de niveles (FR-111a de la feature 002), la ficha pública ni su contrato.
- **FR-317**: Los nuevos indicadores MUST mostrarse solo al productor dueño del CAR (constitución III).

### Key Entities

- **Indicadores del CAR**: conjunto de valores calculados para un CAR, con fecha de obtención y estado por fuente (ok, indisponível, não se aplica).
- **Situación de la alerta**: clasificación única de cada alerta según FR-302, con área dentro del CAR, área en reserva legal, si toca APP y unidades de conservación cruzadas.
- **Resumen de manejo SINAFLOR**: por CAR, n.º de autorizaciones y volumen autorizado, actualizado a partir del registro oficial diario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-301**: Para los 3 CARs de referencia (PE-2607505, MT-5102504 y TO-1712504), la tarjeta muestra los valores calculados en la investigación del 2026-11-06, con una tolerancia de ±1 % en áreas y porcentajes.
- **SC-302**: El 100 % de las alertas tiene exactamente una situación, y la suma por situación coincide con el total de alertas del CAR.
- **SC-303**: En el 100 % de los indicadores, "0", "indisponível" y "não se aplica" se muestran de forma distinta.
- **SC-304**: Con una de las fuentes caída, el resto de los indicadores de la tarjeta sigue visible en el 100 % de los casos.
- **SC-305**: Ningún texto de la interfaz califica una alerta como "ilegal".
- **SC-306**: Con los datos ya guardados, la tarjeta muestra los indicadores en menos de 3 segundos.

## Assumptions

- **Regla de niveles sin cambios**: el cambio propuesto (que no penalicen las alertas superadas) queda para una feature posterior, con confirmación del usuario.
- **Fuentes verificadas el 2026-11-06**: los campos adicionales de MapBiomas Alerta (autorizaciones, plan de manejo, reserva legal, APP, tierra indígena, unidades de conservación, embargos, acciones y suspensión judicial) responden con la cuenta actual. Los servicios públicos del INPE (mapeo anual, alertas DETER y focos de calor) responden sin credenciales. El registro de planes de manejo del IBAMA se publica a diario e incluye el código del CAR.
- **Situaciones no observadas**: `autorizada`, `com_fiscalizacao` y `suspensa_judicial` no aparecieron en los 3 CARs de referencia. Se implementan según la documentación de la fuente y se prueban con datos simulados.
- **Embargo vigente o levantado**: la relación entre una alerta y un embargo concreto es aproximada (FR-302, puntos 2 y 4), porque no siempre se puede enlazar con el código del embargo.
- **Vigencia de la caché**: 24 h por CAR, igual que la caché existente.
- **Fuera de alcance**: cambios en la regla de niveles, nuevos datos en la ficha pública, volumen potencial de madera y polígonos de reserva legal o APP del registro oficial de CAR.
