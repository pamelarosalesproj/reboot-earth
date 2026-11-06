# Feature Specification: Nueva regla de nivel por CAR y por CNPJ, y página "Entenda o nível"

**Feature Branch**: `006-regras-nivel`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "antes de meternos al agente actualiza las reglas con tu propuesta [docs/proposta-regras-nivel-e-agente.md]. Y necesito una opción en el sidebar 'Entiende más' o algo así, en el panel del productor, que explique las reglas con detalle."

## Contexto y decisiones (2026-11-06)

- Reemplaza la **regla provisional FR-111a** de la feature 002 (solo miraba si había alertas o embargos). Afecta al panel del productor (Início, "Meus CARs", detalle del CAR) **y a la ficha pública** del comprador.
- Decisiones de la propuesta, aceptadas por el usuario ("con tu propuesta"):
  1. Una alerta abierta posterior a 2020 en reserva legal o APP es **Bronze solo si su área es ≥ 1 % del área del CAR**; por debajo, Silver.
  2. El nivel del CNPJ es **el peor de sus CARs**.
  3. Sello **"Atenção EUDR"** separado del nivel.
- El **agente de informes** queda fuera de esta feature (irá en otra). Esta feature no cambia el informe del CNPJ salvo el nivel que recibe.
- El score sigue sin método (no se muestra).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nivel de cada CAR según sus riesgos abiertos (Priority: P1)

El productor ve en cada CAR ("Meus CARs" y detalle) un nivel que refleja la gravedad de sus riesgos abiertos, con los motivos y sus números.

**Why this priority**: es la base del nivel del CNPJ y la que el usuario pidió actualizar.

**Independent Test**: con los datos simulados de un CAR, cada combinación de riesgos produce el nivel y los motivos esperados.

**Acceptance Scenarios**:

1. **Given** un CAR con un embargo vigente, **When** se calcula el nivel, **Then** es Bronze con el motivo "embargo vigente" y el número de embargos.
2. **Given** un CAR con una alerta abierta en tierra indígena o UC de protección integral, **Then** es Bronze.
3. **Given** un CAR con alertas abiertas posteriores a 2020 en reserva legal o APP que suman ≥ 1 % de su área, **Then** es Bronze; si suman < 1 %, **Then** es Silver.
4. **Given** un CAR en la Amazonía con corte selectivo desordenado o minería del DETER en los últimos 24 meses, **Then** es Bronze; con degradación del DETER en ese plazo, **Then** al menos Silver.
5. **Given** un CAR con alguna alerta abierta de cualquier fecha y nada de lo anterior, **Then** es Silver.
6. **Given** un CAR cuyas alertas están todas superadas (autorizadas, embargo levantado o suspendidas judicialmente), sin embargos vigentes ni DETER grave, **Then** es Gold.
7. **Given** un CAR con embargos no determinables o sin los indicadores de MapBiomas, y nada más, **Then** es Silver con el motivo "dados parciais".
8. **Given** que MapBiomas no responde y no hay caché, **Then** es Sem dados.
9. **Given** que fallan PRODES, DETER, focos de calor o SINAFLOR, **Then** el nivel no baja por esa falla.

### User Story 2 - Nivel del CNPJ = el peor CAR (Priority: P1)

El productor (Início) y el comprador (ficha pública) ven el nivel del CNPJ como el peor nivel entre sus CARs, con la distribución ("2 de 3 imóveis em Bronze") y los motivos.

**Why this priority**: el comprador no sabe de qué imóvel viene el producto: el riesgo de un CAR alcanza al CNPJ.

**Independent Test**: con CARs simulados en distintos niveles, el CNPJ toma el peor y la ficha pública solo muestra datos agregados.

**Acceptance Scenarios**:

1. **Given** CARs en Gold, Silver y Bronze, **Then** el CNPJ es Bronze y se informa cuántos CARs hay en cada nivel.
2. **Given** CARs en Gold y uno en Sem dados, **Then** el CNPJ es Silver (datos parciales).
3. **Given** ningún CAR con datos, **Then** el CNPJ es Sem dados.
4. **Given** la ficha pública, **When** se muestra el nivel, **Then** coincide con el del panel y no incluye códigos de CAR ni listas de alertas o embargos.

### User Story 3 - Sello "Atenção EUDR" (Priority: P2)

Si algún CAR tiene desmatamento posterior al 31/12/2020, aunque esté autorizado, se muestra el sello "Atenção EUDR", separado del nivel.

**Why this priority**: el reglamento europeo exige ausencia de desmatamento posterior a 2020 aunque sea legal; un CAR puede ser Gold y no cumplirlo.

**Independent Test**: un CAR con una alerta autorizada de 2022 es Gold y tiene el sello.

**Acceptance Scenarios**:

1. **Given** una alerta posterior a 2020 de cualquier situación, **Then** el CAR y su CNPJ muestran "Atenção EUDR" y el nivel no cambia por ello.
2. **Given** sin datos de alertas, **Then** el sello no se muestra como "sin riesgo": queda como indeterminado.

### User Story 4 - Página "Entenda o nível" (Priority: P2)

En el menú lateral del panel del productor hay una opción "Entenda o nível" que explica con detalle: los niveles, cada criterio y su orden, lo que nunca baja el nivel, cómo se calcula el CNPJ, el sello EUDR, las fuentes y un glosario (APP, reserva legal, UC, TI, DETER, PRODES, alerta abierta/superada, EUDR).

**Why this priority**: el productor necesita entender por qué tiene su nivel y qué puede hacer.

**Independent Test**: la opción aparece en el menú, abre la página y sus textos coinciden con la regla implementada (mismo umbral de 1 %, mismos 24 meses).

**Acceptance Scenarios**:

1. **Given** un productor autenticado, **When** pulsa "Entenda o nível", **Then** ve la explicación completa en pt-BR.
2. **Given** la explicación del nivel en el Início o en un CAR, **When** se muestra, **Then** incluye un enlace a esa página.

### Edge Cases

- Un CAR sin área conocida: el umbral del 1 % no se puede evaluar → una alerta abierta post-2020 en RL/APP cuenta como Bronze (conservador) y se indica.
- DETER "Não se aplica" (fuera de la Amazonía): no influye.
- Una alerta que cruza dos CARs del mismo CNPJ se evalúa en cada CAR con su área dentro de ese CAR.
- Datos en caché vencida (stale): el nivel se calcula igual y se indica que los datos pueden estar desactualizados.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-601**: El sistema MUST calcular el nivel de cada CAR evaluando en orden (gana la primera condición):
  1. **Sem dados**: no hay datos de MapBiomas (ni caché).
  2. **Bronze** si se cumple alguna:
     - `EMBARGO_VIGENTE`: ≥ 1 embargo sin fecha de fin;
     - `TI_UC_INTEGRAL`: alguna alerta abierta con área en tierra indígena o UC de protección integral;
     - `RL_APP_POS2020`: la suma del área dentro del CAR de las alertas abiertas posteriores a 2020 que están en reserva legal o tocan APP es ≥ 1 % del área del CAR (o el área del CAR es desconocida);
     - `DETER_GRAVE`: DETER con corte selectivo desordenado (`CS_DESORDENADO`) o minería (`MINERACAO`) con fecha en los últimos 24 meses.
  3. **Silver** si se cumple alguna:
     - `ALERTA_ABERTA`: alguna alerta abierta (sin autorización registrada, con fiscalización o embargo vigente) de cualquier fecha;
     - `DETER_DEGRADACAO`: DETER de degradación (`DEGRADACAO`) en los últimos 24 meses;
     - `DADOS_PARCIAIS`: embargos no determinables o indicadores de MapBiomas no disponibles.
  4. **Gold** en otro caso.
- **FR-602**: El nivel MUST incluir todos los códigos de motivo que se cumplen (no solo el primero) y los números que los explican (n.º de embargos, n.º y ha de alertas abiertas, ha y % en RL/APP post-2020).
- **FR-603**: Nunca bajan el nivel: alertas superadas, UC de uso sostenible, % de vegetación nativa, focos de calor, `CS_GEOMETRICO`, manejo forestal (SINAFLOR) y la falla de PRODES, DETER, focos o SINAFLOR.
- **FR-604**: El nivel del CNPJ MUST ser el peor nivel entre sus CARs con datos (Bronze < Silver < Gold). Si hay CARs en Sem dados y el peor del resto es Gold → Silver con `DADOS_PARCIAIS`. Si ningún CAR tiene datos → Sem dados. Se mantienen los motivos `not_registered` y `no_properties`.
- **FR-605**: El nivel del CNPJ MUST informar la cantidad de CARs en cada nivel y los motivos que llevaron a esos CARs a ese nivel, con cuántos CARs cumplen cada uno. Un motivo de menor gravedad (por ejemplo, RL/APP < 1 % en un CAR Bronze por embargo) no se cuenta (cambio del 2026-11-06, pedido por el usuario).
- **FR-606**: El sello "Atenção EUDR" MUST activarse si algún CAR tiene una alerta con detección posterior al 31/12/2020, en cualquier situación; MUST NOT cambiar el nivel; si no hay datos de alertas, queda indeterminado.
- **FR-607**: Panel (Início, "Meus CARs", detalle) y ficha pública MUST usar el mismo cálculo. La ficha pública MUST seguir mostrando solo datos agregados (constitución III).
- **FR-608**: El panel MUST tener la opción de menú "Entenda o nível" con la página descrita en la US4, y la explicación del nivel MUST enlazar a ella desde el panel.
- **FR-609**: Los textos MUST estar en pt-BR y MUST NOT usar "ilegal" ni "crime".
- **FR-610**: La explicación del nivel MUST dejar de decir "Nível provisório: considera apenas alertas e embargos do MapBiomas Alerta" y pasar a nombrar las fuentes que usa la regla.

### Key Entities

- **Nivel de un CAR**: nivel, códigos de motivo con sus números, sello EUDR (sí / no / indeterminado), si los datos son parciales.
- **Nivel del CNPJ**: nivel, motivos, CARs por nivel, sello EUDR, datos parciales.

## Success Criteria *(mandatory)*

- **SC-601**: Para los CARs de referencia, el nivel coincide con el cálculo manual de la regla con los datos del día (se registra en el quickstart).
- **SC-602**: El nivel del CNPJ es idéntico en el panel y en la ficha pública en el 100 % de los casos.
- **SC-603**: Una falla de PRODES, DETER, focos o SINAFLOR nunca empeora el nivel (cubierto por pruebas automáticas).
- **SC-604**: Cada nivel mostrado indica al menos un motivo con números, salvo Gold, y enlaza a "Entenda o nível" en el panel.
- **SC-605**: La ficha pública no expone códigos de CAR, geometrías ni listas de alertas o embargos (prueba de privacidad existente).

## Assumptions

- "Alerta abierta" y "superada" siguen la clasificación de la feature 003; "posterior a 2020" es detección después del 31/12/2020.
- La ficha pública pasa a necesitar los indicadores de cada CAR (con caché de 24 h); la primera consulta de un CNPJ sin caché puede tardar más.
- El sello EUDR también se muestra en la ficha pública (es un dato agregado).
- El agente de informes (otra feature) recibirá este nivel y sus motivos sin cambiarlos.
