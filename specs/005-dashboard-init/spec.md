# Feature Specification: Início del productor como resumen del CNPJ

**Feature Branch**: `005-dashboard-init`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "el dashboard de inicio muestra infos que hoy no existen (lotes, volumen homologado, conformidad EUDR, matriz de riesgo). Aquí debería estar un resumen del CNPJ: su status total, un informe elaborado por el agente (docs/proposta-regras-nivel-e-agente.md) y 3 big numbers: n.º de CAR, n.º de alertas aún abiertas [y embargos vigentes]. Por ahora genera tú el resumen como Claude y colócalo mockeado, porque otro compañero hará la parte de cómo generar el resumen."

## Contexto y decisiones (2026-11-06)

- El rediseño puso en el Início módulos de **lotes** sin ninguna fuente de datos, que se muestran siempre vacíos o "indisponíveis". **Salen del Início**. El componente se conserva en la vista previa de diseño para cuando exista una fuente de lotes.
- **Tercer número grande**: embargos vigentes (recomendación aceptada al pedir "comenzar").
- **El nivel sigue siendo el de la regla provisional (FR-111a de la feature 002)**. La regla nueva de `docs/proposta-regras-nivel-e-agente.md` necesita 3 decisiones del usuario y queda fuera de alcance.
- **Informe**: esta feature define **dónde y cómo se muestra** y el **formato** del informe. El contenido es un **ejemplo escrito a mano** (mock) por Claude a partir de los datos reales del 2026-11-06. La generación automática (agente, prompt, controles) la implementa otro integrante del equipo **sin cambiar el formato**.

- **Explicación del nivel (2026-11-06)**: el motivo con números y sin "Score em cálculo", en el Início y en la ficha pública. Ver el cambio registrado en `specs/002-cnpj-score-search/spec.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estado y números del CNPJ (Priority: P1)

Al entrar, el productor ve el **nivel de su CNPJ** (Gold, Silver, Bronze o Sem dados) con su explicación y un enlace a cómo lo ve el comprador. Debajo ve tres números: **CARs cadastrados**, **Alertas abertas** (n.º y ha, con "de N; X superadas") y **Embargos vigentes**.

**Why this priority**: es la información real que hoy falta en el Início y la que el productor necesita primero.

**Independent Test**: con el CNPJ de referencia (7 CARs), el Início muestra Bronze, 7 CARs, 36 alertas abiertas (376,1 ha) "de 38; 2 superadas" y 7 embargos vigentes.

**Acceptance Scenarios**:

1. **Given** un productor con CARs, **When** abre el Início, **Then** ve el nivel del CNPJ, igual al de la ficha pública, y los 3 números.
2. **Given** alertas autorizadas, con embargo levantado o suspendidas, **When** se cuentan, **Then** no entran en "Alertas abertas": se indican como "superadas".
3. **Given** una alerta que cruza dos CARs del mismo CNPJ, **When** se cuenta, **Then** cuenta una sola vez.
4. **Given** CARs cuyos datos no están disponibles o cuyos embargos no son determinables, **When** se muestran los números, **Then** se indica cuántos CARs faltan, y un dato no disponible nunca se muestra como 0.
5. **Given** un productor sin CARs, **When** abre el Início, **Then** ve la invitación a añadir el primero.

### User Story 2 - Informe del CNPJ (Priority: P1)

Debajo de los números, una sección **"Relatório do CNPJ"** muestra: título, riesgos (máximo 3), contexto, salvedades y una línea por CAR con enlace a su detalle. También muestra la fecha de los datos y un aviso de su origen.

**Why this priority**: es el resumen que el usuario pidió. El formato queda fijado para la integración del agente.

**Independent Test**: para el CNPJ de referencia se muestra el informe de ejemplo con el aviso "Exemplo escrito manualmente"; para un CNPJ sin informe se muestra "Relatório ainda não disponível" y el resto del Início funciona.

**Acceptance Scenarios**:

1. **Given** un CNPJ con informe, **When** se muestra, **Then** aparecen título, riesgos, contexto, salvedades y la línea de cada CAR con su enlace.
2. **Given** el informe, **When** se muestra su nivel, **Then** es el nivel calculado por las reglas, no un texto del informe.
3. **Given** un informe de ejemplo (mock), **When** se muestra, **Then** lleva el aviso de que es un ejemplo escrito manualmente y no se genera automáticamente.
4. **Given** un CNPJ sin informe o un error al obtenerlo, **When** se abre el Início, **Then** se muestra "Relatório ainda não disponível" y el nivel y los números se ven igual.

### Edge Cases

- Un CAR no aparece en el informe de ejemplo (añadido después): el informe lo omite. No se inventa una línea.
- El informe de ejemplo es estático: si los datos cambian, sus cifras pueden quedar desactualizadas. Por eso se indica la fecha de los datos del informe.
- Dos cuentas con el mismo CNPJ: los números y el nivel son del CNPJ completo, como la ficha pública.

## Requirements *(mandatory)*

- **FR-501**: El Início MUST mostrar el nivel del CNPJ, calculado con el mismo código que la ficha pública (FR-114 de la feature 002), con su explicación y un enlace a la ficha pública.
- **FR-502**: El Início MUST mostrar 3 números a nivel CNPJ:
  - CARs cadastrados (sin repetir);
  - Alertas abertas: n.º de alertas distintas en situación `pendente`, `com_fiscalizacao` o `embargo_vigente`, y la suma de su área dentro de cada CAR, con el total de alertas y el n.º de superadas;
  - Embargos vigentes: únicos por (órgão, processo), sin fecha de fin.

  Cada número MUST indicar cuántos CARs no tienen datos o tienen embargos no determinables, y MUST NOT mostrar 0 cuando el dato no está disponible.
- **FR-503**: Las situaciones de las alertas MUST salir de la misma clasificación de la feature 003 (`classify_alert`), sin otra implementación.
- **FR-504**: El Início MUST NOT mostrar los módulos de lotes (lotes rastreados, volumen homologado, conformidad EUDR, matriz de riesgo y tabla de lotes).
- **FR-505**: El sistema MUST ofrecer el informe del CNPJ con el formato: `titulo`, `riscos[]` (≤ 3), `contexto[]` (≤ 3), `ressalvas[]`, `imoveis[{car_code, resumo}]`, `data_dos_dados`, `gerado_em` y `origem` (`exemplo` | `agente`). El campo `nivel` lo pone siempre el backend con el nivel calculado.
- **FR-506**: Mientras no exista el agente, el informe MUST venir de un ejemplo escrito a mano, guardado **fuera del repositorio** (contiene códigos de CAR reales asociados a un CNPJ). Si no hay ejemplo para el CNPJ, MUST responder "indisponível".
- **FR-507**: La interfaz MUST mostrar el origen del informe:
  - `exemplo`: "Exemplo escrito manualmente — a geração automática ainda não está disponível";
  - `agente`: "Gerado por IA a partir dos dados de MapBiomas, INPE e IBAMA; o nível é calculado por regras".
- **FR-508**: El texto del informe MUST NOT contener "ilegal" ni "crime" (constitución y feature 003).
- **FR-509**: El informe y los números MUST ser visibles solo para el productor autenticado de ese CNPJ (constitución III).

### Key Entities

- **Resumen de alertas del CNPJ**: CARs, alertas totales, abiertas (n.º, ha), superadas (n.º, ha), embargos vigentes, CARs sin datos y CARs con embargos no determinables, con fecha.
- **Informe del CNPJ**: el formato de FR-505, con el nivel calculado y su origen.

## Success Criteria *(mandatory)*

- **SC-501**: Para el CNPJ de referencia, el Início muestra los valores calculados el 2026-11-06 (Bronze; 7 CARs; 36 alertas abiertas · 376,1 ha de 38, 2 superadas; 7 embargos vigentes).
- **SC-502**: El nivel del Início y el de la ficha pública coinciden en el 100 % de los casos.
- **SC-503**: El Início no muestra ningún módulo sin fuente de datos.
- **SC-504**: Sin informe disponible, el nivel y los números se siguen mostrando en el 100 % de los casos.

## Assumptions

- El reemplazo del ejemplo por el agente solo cambia el proveedor del informe en el backend. El endpoint, el formato y la interfaz se mantienen.
- La decisión de privacidad sobre enviar datos a un proveedor de IA queda para la feature del agente. El ejemplo no envía datos a nadie.
- Los números de alertas usan la caché de indicadores de la feature 003. La primera carga de un CNPJ sin caché puede tardar, porque calcula los indicadores de cada CAR.
