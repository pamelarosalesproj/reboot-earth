# Feature Specification: Relatório do CNPJ explicado pela IA a partir dos dados de cada CAR

**Feature Branch**: `006-regras-nivel` (se desarrolla en la misma rama, a pedido de la responsable)

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Pero ya tienes los datos de cada car!!! yo quiero usar la IA solo para consolidar datos y explicarle al productor qué significa. Quiero que transforme ese tanto de info en algo digerible."

## Contexto y decisiones (2026-11-08)

- El **Início** ya muestra un "Relatório do CNPJ" con título, riesgos, contexto, un resumen por imóvel y
  ressalvas. El formato y la interfaz se mantienen.
- Hoy ese relatório sale de tres caminos: un ejemplo escrito a mano (si existe para el CNPJ), un modelo de
  lenguaje (si hay clave configurada) o un texto armado por reglas. Problemas verificados:
  - al modelo se le envía la lista bruta de alertas y **no** el nivel y los motivos de cada imóvel, la
    vegetación nativa, el DETER, el SINAFLOR, las unidades de conservación ni la fuente de los embargos,
    así que no puede explicarlos y puede inventarlos;
  - se envían los códigos de CAR junto con el CNPJ a un tercero;
  - se genera de nuevo en cada visita al Início (lento, costoso y con texto distinto cada vez);
  - si el modelo devuelve un riesgo de más, se descarta todo el relatório;
  - el texto armado por reglas se presenta como "Gerado por IA";
  - el texto pide recomendaciones de regularización (consejo jurídico) y usa el nombre antiguo de la
    plataforma.
- **Nada de esto involucra notas fiscales** (la auditoría de NFs es otro módulo, oculto desde el
  2026-11-08).
- Decisiones confirmadas con la responsable:
  1. La IA **solo consolida y explica** datos que ya existen por imóvel (nivel y motivos, indicadores ya
     agregados, embargos con su fuente) y del CNPJ (nivel, motivos, imóveis por nivel). **No calcula nada
     ni decide el nivel.**
  2. **Seudónimos**: la IA recibe "Imóvel A", "Imóvel B"… y no recibe el CNPJ; el productor ve los códigos
     reales.
  3. **Se genera una vez** y se reutiliza mientras los datos no cambien.
  4. **Todo número del texto debe existir en los datos**; si no, no se muestra ese texto.
  5. Mismo formato, nivel impuesto por las reglas, vocabulario permitido, sin consejo jurídico ni de
     compra, en pt-BR.
  6. (Clarificación) La IA tiene prioridad sobre el ejemplo escrito a mano, que queda solo para modo
     demostración; el relatório escrito por IA lleva arriba el aviso "Gerado por IA".

## Cambios de alcance

- **2026-11-08 (pedido de la responsable)**: se quita del Início el cartón "Status do CNPJ" porque repetía
  lo que explica el relatório. El encabezado del relatório pasa a mostrar el nivel del CNPJ, el sinal
  "Atenção EUDR" (con su ayuda) y los imóveis por nivel, tomados del panel (reglas), de modo que siguen
  visibles aunque el relatório falle o esté cargando. La lista de motivos de las reglas se quita (los
  riesgos del relatório los explican). Debajo del relatório va el enlace "Entenda os níveis Gold, Silver e
  Bronze" a la página "Entenda o nível". El estado del score ("Score em cálculo") deja de mostrarse en el
  Início. La IA menciona el sinal EUDR cuando aplica.
- **2026-11-08**: el modelo por defecto pasa a `gemini-3.5-flash` con 30 s de límite (`gemini-2.5-flash` ya
  no está disponible para cuentas nuevas).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entender la situación del CNPJ en un vistazo (Priority: P1)

El productor abre el Início y lee un relatório corto y claro: un título que resume la situación, hasta 3
riesgos, hasta 3 datos de contexto, una frase por imóvel y las ressalvas que correspondan. Entiende qué
pesa en su nivel, qué es solo contexto y qué significa cada término, sin tener que abrir cada CAR.

**Why this priority**: es el objetivo de la feature: convertir muchos datos técnicos en algo digerible.

**Independent Test**: con los datos de varios imóveis simulados y el modelo de lenguaje simulado, el
relatório muestra el formato completo, usa solo números presentes en los datos y explica los motivos del
nivel.

**Acceptance Scenarios**:

1. **Given** un CNPJ con imóveis en distintos niveles, **When** el productor abre el Início, **Then** ve
   arriba el aviso "Gerado por IA" y luego un título, hasta 3 riesgos, hasta 3 datos de contexto, una frase
   por cada imóvel y ressalvas, en pt-BR.
2. **Given** un imóvel Bronze por embargo vigente, **Then** su frase y los riesgos lo explican con los
   números de los datos (cantidad, hectáreas, fuente del embargo).
3. **Given** alertas superadas, unidades de uso sustentable o focos de calor, **Then** aparecen como
   contexto, nunca como riesgo.
4. **Given** un dato "Indisponível" o "não determinável" (por ejemplo, embargos sin fuente que responda),
   **Then** el relatório lo dice así y nunca lo presenta como 0.
5. **Given** cualquier relatório, **Then** el nivel mostrado es el calculado por las reglas, el texto no lo
   contradice y no contiene "ilegal", "crime" ni consejos jurídicos o de compra.

---

### User Story 2 - Un texto confiable aunque la IA falle (Priority: P1)

Si la IA no está configurada, no responde, inventa un número, menciona un imóvel que no existe o usa
vocabulario no permitido, el productor ve igual un relatório correcto armado por reglas, con un aviso que
dice que **no** fue escrito por IA.

**Why this priority**: el Início nunca puede quedar roto ni mostrar cifras inventadas (principio II).

**Independent Test**: con el modelo simulado devolviendo error, timeout, un número que no está en los datos
o un seudónimo desconocido, se muestra el relatório por reglas con su aviso propio.

**Acceptance Scenarios**:

1. **Given** que no hay clave del modelo, **Then** se muestra el relatório por reglas con el aviso "gerado
   automaticamente por regras" (no "Gerado por IA").
2. **Given** que el modelo tarda más que el límite configurado o responde error, **Then** se muestra el
   relatório por reglas.
3. **Given** que el texto del modelo cita un número que no está en los datos, **Then** no se muestra ese
   texto; se reintenta una vez y, si vuelve a fallar, se muestra el relatório por reglas.
4. **Given** que el texto menciona "Imóvel Z" (que no existe), **Then** se trata como el caso anterior.
5. **Given** que el modelo devuelve 4 riesgos válidos, **Then** se muestran los 3 primeros (no se descarta
   todo el relatório).

---

### User Story 3 - Privacidad y estabilidad (Priority: P2)

Los códigos de CAR y el CNPJ no salen del servidor hacia el proveedor de IA, y el texto no cambia cada vez
que el productor vuelve al Início.

**Why this priority**: principio III (minimizar lo que recibe un tercero) y experiencia: un texto que
cambia en cada visita genera desconfianza y costo.

**Independent Test**: se inspecciona lo enviado al modelo simulado (sin códigos de CAR ni CNPJ) y se
comprueba que dos visitas seguidas con los mismos datos llaman al modelo una sola vez.

**Acceptance Scenarios**:

1. **Given** cualquier relatório, **Then** lo enviado al proveedor de IA no contiene ningún código de CAR
   ni el CNPJ; el relatório mostrado sí muestra los códigos reales.
2. **Given** dos visitas al Início con los mismos datos, **Then** el modelo se llama una sola vez y ambas
   muestran el mismo texto.
3. **Given** que cambian los datos de algún imóvel (por ejemplo, tras "Atualizar"), **Then** el relatório
   se genera de nuevo.

---

### Edge Cases

- **CNPJ sin imóveis o no cadastrado**: no hay relatório ("Relatório ainda não disponível"), como hoy.
- **Un imóvel sin datos de MapBiomas** (Sem dados): su frase lo dice; los demás se explican normalmente.
- **Muchos imóveis**: una frase por imóvel; si son demasiados para un solo pedido, se explican los datos
  agregados y los imóveis en orden de gravedad. [Límite práctico a definir en el plan.]
- **Números con formato distinto** ("376,1" vs "376.1", "2.968,4 ha"): el control acepta el formato pt-BR.
- **Fechas y años en el texto** ("agosto de 2026", "31/12/2020"): solo se aceptan si están en los datos o
  son la fecha de corte de la EUDR.
- **El modelo escribe el seudónimo con otra capitalización** ("imóvel a"): se trata como desconocido.
- **Ejemplo escrito a mano para el CNPJ**: se ignora salvo en modo demostración (FR-811).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-801**: El relatório MUST construirse solo con datos que el sistema ya calcula: por imóvel, nivel y
  motivos, alertas por situación (cantidad y hectáreas), riesgos abiertos, vegetación nativa, DETER, focos
  de calor, manejo florestal, unidades de conservación y embargos con su fuente y estado; del CNPJ, nivel,
  motivos e imóveis por nivel. MUST NOT incluir geometrías ni listas individuales de alertas.
- **FR-802**: Los estados "Indisponível", "não determinável" y "Não se aplica" MUST llegar a la IA como
  tales y MUST NOT mostrarse como 0.
- **FR-803**: La IA MUST recibir seudónimos ("Imóvel A", "Imóvel B"…, con estado y área) en lugar de los
  códigos de CAR, y MUST NOT recibir el CNPJ. El sistema MUST reemplazar los seudónimos por los códigos
  reales antes de mostrar el texto.
- **FR-804**: Las instrucciones a la IA MUST pedir: explicar en lenguaje simple qué pesa en el nivel, qué
  es contexto y qué significan los términos; usar solo los números recibidos; no alterar ni discutir el
  nivel; vocabulario "sem autorização registrada" (nunca "ilegal" ni "crime"); sin consejos jurídicos ni
  de compra; incluir las ressalvas aplicables (PRODES no registra regeneración; reserva legal y APP sobre
  el área de la alerta; volumen del SINAFLOR por autorización; "Indisponível" no es 0); pt-BR; el nombre
  de la plataforma es Elo Rural.
- **FR-805**: Antes de mostrar un texto de la IA, el sistema MUST verificar: formato válido; como máximo 3
  riesgos y 3 datos de contexto (recortando los que sobren); ausencia de vocabulario prohibido; que cada
  número citado exista en los datos enviados (aceptando el formato pt-BR, además del año 2020 y la fecha
  31/12/2020 de la EUDR); y que solo se mencionen seudónimos existentes.
- **FR-806**: Si la verificación falla, el sistema MUST reintentar una vez; si vuelve a fallar, o si no hay
  clave, o si la IA no responde dentro del tiempo configurado, MUST mostrar el relatório armado por reglas.
- **FR-807**: El nivel mostrado MUST ser siempre el calculado por las reglas de nivel, nunca el del texto.
- **FR-808**: El relatório MUST indicar su origen con un aviso visible y veraz: escrito por IA, armado por
  reglas o ejemplo escrito a mano, además de la fecha de los datos.
- **FR-808a**: Cuando el texto fue escrito por la IA, MUST mostrarse **arriba del relatório**, antes del
  título, un aviso destacado **"Gerado por IA"**, acompañado de una nota breve de que el nivel lo calculan
  las reglas y de que los datos vienen de MapBiomas, INPE e IBAMA. Los textos por reglas o de ejemplo MUST
  NOT llevar ese aviso. (Pedido de la responsable, 2026-11-08.)
- **FR-809**: El relatório MUST generarse una vez y reutilizarse mientras los datos de entrada no cambien;
  un cambio en los datos de cualquier imóvel MUST provocar una nueva generación.
- **FR-810**: El tiempo máximo de espera de la IA MUST ser el configurado por el operador.
- **FR-811**: La IA MUST tener prioridad sobre el ejemplo escrito a mano. El ejemplo MUST usarse solo si
  el operador lo activa explícitamente (modo demostración); sin esa activación se ignora aunque exista el
  archivo del CNPJ. (Decidido el 2026-11-08: opción A.)
- **FR-812**: El relatório MUST NOT usar datos de notas fiscales.

### Key Entities

- **Datos del relatório**: resumen estructurado, sin códigos reales, con lo que la IA puede citar: por
  imóvel (seudónimo, estado, área, nivel, motivos, alertas, embargos y fuente, contexto, estados de las
  fuentes) y del CNPJ (nivel, motivos, imóveis por nivel, fecha de los datos).
- **Correspondencia de seudónimos**: "Imóvel A" ↔ código de CAR, solo en el servidor y solo para esa
  generación.
- **Relatório del CNPJ (existente)**: título, riesgos, contexto, resumen por imóvel, ressalvas, nivel,
  origen y fechas. El origen gana un valor nuevo: armado por reglas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-801**: En la cuenta de prueba (7 imóveis), el relatório explica el nivel de cada imóvel con sus
  motivos reales y cita solo números presentes en los datos (0 números inventados en las pruebas).
- **SC-802**: Ningún contenido enviado al proveedor de IA contiene códigos de CAR ni el CNPJ (verificado por
  test automático).
- **SC-803**: Volver al Início con los mismos datos muestra el relatório sin esperar a la IA y con el mismo
  texto; la IA se llama como máximo una vez por cambio de datos.
- **SC-804**: Con la IA no configurada, caída o respondiendo algo inválido, el Início siempre muestra un
  relatório correcto con el aviso de que fue armado por reglas.
- **SC-805**: Ningún relatório (de IA o por reglas) muestra "Gerado por IA" si no lo escribió la IA.

## Assumptions

- La clave y el proveedor de IA son los ya configurados en el entorno (API compatible con OpenAI; por
  defecto Gemini). Esta feature no agrega proveedores.
- La reutilización del relatório vive en la memoria del servidor (se pierde al reiniciar, lo que solo causa
  una nueva generación); no hace falta tabla nueva.
- El texto armado por reglas existente se mantiene como respaldo, corrigiendo su origen y su vocabulario.
- El relatório es solo para el productor autenticado; la ficha pública no lo muestra.
- El test `test_missing_report_is_unavailable` se actualiza al comportamiento vigente.
