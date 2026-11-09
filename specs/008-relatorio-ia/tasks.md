# Tasks: Relatório do CNPJ explicado pela IA a partir dos dados de cada CAR

**Input**: Design documents from `specs/008-relatorio-ia/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: incluidos (principio VI: cada requisito de fallo y de privacidad tiene test).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Añadir `report_demo_mode: bool = False` a `Settings` en backend/app/config.py (comentario: el ejemplo escrito a mano solo se usa en modo demostración)
- [X] T002 En backend/tests/conftest.py: fixture autouse que fija `settings.llm_api_key = ""` y borra `LLM_API_KEY` del entorno; clase `FakeLlm` (respx sobre `settings.llm_api_url`, POST) con `response` (dict o texto JSON que devuelve como `choices[0].message.content`), `status`, `timeout` (lanza `httpx.ReadTimeout`), `bodies` (cuerpos recibidos) y `calls`; fixture `llm` que la enciende y fija una clave falsa

## Phase 2: Foundational

- [X] T003 Ampliar `CnpjReport.origem` a `Literal["exemplo", "agente", "regras"] | None` en backend/app/schemas.py
- [X] T004 Crear backend/app/reports/prompt.py con `PROMPT_VERSION = "008-1"` y `SYSTEM_PROMPT` (rol: assistente do Elo Rural que explica ao produtor; objetivo: consolidar e explicar em linguagem simples o que pesa no nível, o que é contexto e o que significam os termos; glossário dos códigos de motivo; usar só números recebidos e não somar; não alterar nem discutir o nível; "sem autorização registrada", nunca "ilegal"/"crime"; sem conselhos jurídicos nem de compra; tratar "indisponivel"/"nao_determinavel" como tal, nunca 0; usar sempre os ids "Imóvel A"… exatamente como recebidos; ressalvas aplicáveis; formato JSON `{titulo, riscos[≤3], contexto[≤3], ressalvas[], imoveis[{id, resumo}]}`; pt-BR)

## Phase 3: User Story 1 - Entender la situación del CNPJ (P1) 🎯 MVP

**Goal**: la IA recibe los datos ya calculados (con seudónimos) y el relatório se muestra con códigos reales.
**Independent Test**: con `FakeLlm` devolviendo una respuesta válida, el relatório sale con `origem="agente"`, códigos reales, nivel de las reglas.

### Tests

- [X] T005 [P] [US1] Tests unitarios en backend/tests/unit/test_report_facts.py: `build_report_facts` no contiene códigos de CAR ni CNPJ (búsqueda en el JSON serializado); orden por gravedad y seudónimos A, B…; estados `indisponivel`/`nao_determinavel` como texto y `null` (nunca 0); totales del CNPJ correctos; ha redondeadas a 1 decimal; `allowed_numbers` incluye todos los números del JSON y las constantes (2020, 31, 12, 24, 1, 0,1); `numbers_in_text` normaliza "2.968,4", "376,1", "31/12/2020"; `unknown_aliases` detecta "Imóvel Z"; `restore_aliases` pone el prefijo `UF-MUNICÍPIO` en el texto y el código completo en `car_code`, y usa el código completo si dos CARs comparten prefijo
- [X] T006 [P] [US1] Tests de integración en backend/tests/integration/test_dashboard_report.py: (a) con `llm` válido → `status=ok`, `origem=agente`, `nivel` = el de `/api/dashboard`, `imoveis[].car_code` reales; (b) el cuerpo enviado al LLM no contiene códigos de CAR ni el CNPJ; (c) actualizar `test_missing_report_is_unavailable` → sin ejemplo y sin clave: `status=ok`, `origem=regras`; (d) los tests de ejemplo pasan solo con `report_demo_mode=True`, y sin el modo el ejemplo se ignora

### Implementation

- [X] T007 [US1] Crear backend/app/reports/facts.py (funciones puras): `build_report_facts(cars: list[tuple[code, CarDetail|None, CarIndicators|None, Status]], cnpj: Status, today) -> tuple[dict, dict[str, str]]` según data-model.md (máx. 40 imóveis, orden Bronze→Silver→Gold→Sem dados); `allowed_numbers(facts) -> set[float]`; `numbers_in_text(text) -> list[float]`; `unknown_aliases(texts, aliases) -> set[str]`; `restore_aliases(report_dict, aliases) -> report_dict`
- [X] T008 [US1] Reescribir el flujo de `get_report` en backend/app/reports/__init__.py: modo demostración primero (`settings.report_demo_mode` + `_example_report`); CNPJ sin imóveis → `UNAVAILABLE`; cargar con `cnpj_report.car_inputs` una sola vez y calcular `car_level` / `cnpj_level`; `build_report_facts`; llamada al LLM con `SYSTEM_PROMPT`, el JSON de datos como mensaje de usuario y timeout `settings.llm_timeout_s` (clave de `settings.llm_api_key`, ignorando el valor de ejemplo del `.env.example`); `nivel` impuesto; `origem="agente"`; eliminar `_car_data` y el prompt viejo

**Checkpoint**: US1 funcional con la IA simulada.

## Phase 4: User Story 2 - Texto confiable aunque la IA falle (P1)

**Goal**: validación estricta y fallback por reglas con origen veraz.
**Independent Test**: con `FakeLlm` en error, timeout, número inventado, "Imóvel Z", 4 riscos o "ilegal", el resultado es correcto.

- [X] T009 [P] [US2] Tests en backend/tests/integration/test_dashboard_report.py: sin clave → `regras` y 0 llamadas; HTTP 500 → `regras`; timeout → `regras`; número inventado → reintento (2 llamadas) y luego `regras`; "Imóvel Z" → `regras`; "ilegal" → `regras`; 4 riscos válidos → `agente` con 3; imóvel faltante en la respuesta → se completa con su frase por reglas
- [X] T010 [US2] En backend/app/reports/__init__.py: `_validate_llm(raw, facts, aliases)` que recorta `riscos`/`contexto` a 3, valida el esquema, aplica `FORBIDDEN`, exige `numbers_in_text ⊆ allowed_numbers` y ningún alias desconocido; completa imóveis faltantes con la frase por reglas; un reintento; si falla, `_build_deterministic_report` con `origem="regras"`
- [X] T011 [US2] Ajustar `_build_deterministic_report` en backend/app/reports/__init__.py: `origem="regras"`; quitar la ressalva "Recomenda-se … nota ESG" y la línea fija de SINAFLOR; título sin "Conformidade socioambiental positiva" (usar "Nenhum risco em aberto nos N imóveis"); mantener vocabulario permitido

## Phase 5: User Story 3 - Privacidad y estabilidad (P2)

**Goal**: caché por contenido y nada sensible hacia la IA.
**Independent Test**: dos llamadas a `/api/dashboard/report` con los mismos datos → 1 llamada al LLM y mismo texto; datos cambiados → nueva llamada.

- [X] T012 [P] [US3] Tests en backend/tests/integration/test_dashboard_report.py: dos visitas → `llm.calls == 1` y textos iguales; tras cambiar los datos de un CAR (`refresh` con datos distintos en `FakeMapBiomas`) → nueva llamada; el fallback se cachea (sin clave: dos visitas sin llamadas)
- [X] T013 [US3] Caché en memoria en backend/app/reports/__init__.py: clave SHA-256 de `json.dumps(facts, sort_keys=True)` + `PROMPT_VERSION` + modelo; respuestas `agente` sin vencimiento, `regras` 15 min; máximo 256 entradas; función `clear_report_cache()` usada por un fixture autouse de los tests

## Phase 6: Frontend (FR-808, FR-808a)

- [X] T014 [P] Ampliar `origem` a `'exemplo' | 'agente' | 'regras' | null` en frontend/src/types.ts
- [X] T015 [P] Textos en frontend/src/i18n/pt-BR.ts (`home.report`): `aiBadge: 'Gerado por IA'`, `originAgent: 'O texto foi escrito por IA a partir dos dados de MapBiomas, INPE e IBAMA; o nível é calculado por regras fixas.'`, `originRules: 'Gerado automaticamente por regras (sem IA) a partir dos dados de MapBiomas, INPE e IBAMA.'`, `originExample: 'Exemplo de demonstração escrito manualmente.'`
- [X] T016 Mostrar en frontend/src/components/CnpjReportView.tsx, con `origem === 'agente'`, un aviso destacado "Gerado por IA" arriba del relatório (antes del encabezado) + la nota `originAgent`; con `regras` y `exemplo`, su nota (sin el aviso de IA); estilo del aviso en frontend/src/pages/HomePage.css
- [X] T017 Test Vitest en frontend/tests/CnpjReportView.test.tsx: con `agente` aparece "Gerado por IA" antes del título; con `regras` no aparece y se ve "Gerado automaticamente por regras"

## Phase 7: Polish

- [X] T018 [P] Actualizar docs/arquitetura.md (sección "Relatório do CNPJ": flujo nuevo, seudónimos, control de números, caché, `REPORT_DEMO_MODE`, quitar los "pontos de atenção" resueltos) y docs/desenvolvimento.md (`REPORT_DEMO_MODE`)
- [X] T019 [P] Actualizar docs/proposta-agente.md (status: implementado en la 008 con una sola llamada por CNPJ; diferencias con la propuesta), AGENTS.md (feature 008; quitar "Pendente: o agente") y CLAUDE.md (línea del relatório de ejemplo → modo demostración)
- [X] T020 Correr los cuatro gates y reportar la salida
- [ ] T021 Validación manual de quickstart.md con la clave real (la responsable)

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T004) → US1 (T005–T008) → US2 (T009–T011) → US3 (T012–T013) → Frontend (T014–T017) → Polish.
- El frontend (T014–T017) solo depende de T003 y puede hacerse en paralelo a US2/US3.
- T008 depende de T007; T010 y T013 tocan el mismo archivo que T008 (secuenciales).

## Implementation Strategy

- **MVP**: Phases 1–3 + T010/T011 (sin validación y fallback no se puede mostrar texto de IA con seguridad).
- Luego caché (US3) y frontend (aviso "Gerado por IA", exigido por FR-808a antes de entregar).
- No hacer commit sin pedido explícito.
