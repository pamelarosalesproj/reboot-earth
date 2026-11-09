# Arquitetura técnica

**Atualizado em**: 2026-11-08 · **Estado**: features 001, 002, 003, 005, 006 e 007, auditoria mensal com IA
e redesign do frontend

Documento de referência para quem mantém o código. Produto e motivação: [`README.md`](../README.md). Como
rodar, configurar e testar: [`desenvolvimento.md`](desenvolvimento.md). Regras de nível:
[`proposta-regras-nivel.md`](proposta-regras-nivel.md). Regras de governança:
[constituição](../.specify/memory/constitution.md). Detalhe de cada feature: `specs/NNN-*/`.

## 1. Visão geral

```
Navegador (React SPA, pt-BR)
   │  só /api (proxy do Vite em dev)
   ▼
FastAPI (backend/app)
   ├─ routers/        auth · cars · dashboard · public · audit
   ├─ services/       car_service · car_indicators · level_rules · cnpj_report · cnpj_overview
   │                  · ai_auditor_service                     ← regras de negócio
   ├─ reports/        relatório do CNPJ: dados com pseudônimos → IA → controles (ou texto por regras)
   ├─ mapbiomas/      cliente GraphQL + queries (credenciais só aqui)
   ├─ sources/        inpe (WFS) · ibama (áreas embargadas) · sinaflor (CSV diário) · geo (shapely)
   ├─ rate_limit.py   limite das consultas públicas
   └─ SQLite          contas, CARs e caches (NullPool)
          │
          ├──► MapBiomas Alerta (GraphQL, com login)
          ├──► INPE TerraBrasilis (WFS público: PRODES, DETER, biomas, focos de calor)
          ├──► IBAMA Pamgia (ArcGIS público: áreas embargadas, respaldo dos embargos)
          ├──► IBAMA dados abertos (CSV do POA Amazônia Legal, sincronizado 1×/dia)
          └──► LLM compatível com a API da OpenAI (padrão: Gemini), opcional
```

Princípios que guiam o desenho (constituição I–VII):
- fontes externas só no servidor;
- cache com data e falha isolada por fonte;
- dados públicos só agregados;
- uma única implementação de cada regra;
- nada de dependências sem necessidade;
- testes sem rede;
- dados derivados sempre com base e data.

## 2. Backend

### Endpoints

| Método e rota | Sessão | Feature | Descrição |
|---|---|---|---|
| `POST /api/auth/register` · `/login` · `/logout` · `GET /api/auth/me` | — / ✓ | 001 | Conta do produtor (email, CNPJ e senha), sessão por cookie `HttpOnly` |
| `GET/POST /api/cars` · `DELETE /api/cars/{car}` | ✓ | 001 | CARs do produtor; ao adicionar, verifica no MapBiomas |
| `GET /api/cars/{car}/summary` · `/detail` | ✓ | 001/006/007 | Polígono, alertas, embargos (com fonte) e nível do CAR (cache de 24 h, `?refresh=true`) |
| `GET /api/cars/{car}/indicators` | ✓ | 003 | Indicadores socioambientais (riscos abertos e contexto) |
| `GET /api/dashboard` | ✓ | 001/006 | Totais da conta + `cnpj_status` / `cnpj_score` do CNPJ |
| `GET /api/dashboard/overview` | ✓ | 005 | Números do CNPJ: CARs, alertas abertas/superadas (n.º, ha), embargos vigentes |
| `GET /api/dashboard/report` | ✓ | 005/008 | Relatório do CNPJ explicado pela IA, ou por regras (ver [Relatório do CNPJ](#relatório-do-cnpj-features-005-e-008)). `nivel` sempre imposto pelas regras |
| `POST /api/audit/generate-report` | ✓ | Auditoria | Auditoria mensal de notas fiscais × CARs. **Desligada por padrão** (404 sem `AUDIT_ENABLED=true`; ver [Auditoria mensal](#auditoria-mensal-com-ia)) |
| `GET /api/public/cnpj/{cnpj}` | — | 002/006 | Ficha pública agregada; rate limit de 30/h por IP |
| `GET /api/health` | — | — | Saúde |

Um CAR de outro produtor responde **404**; sem sessão, **401**. As rotas de dados nunca respondem 503
por falha de uma fonte externa quando há cache ou um estado "indisponível" para mostrar. Contratos:
`specs/00N-*/contracts/openapi.yaml`.

### Banco de dados

SQLite (`backend/data/app.db` por padrão), tabelas criadas por `create_all` no startup:

| Tabela | Feature | Conteúdo |
|---|---|---|
| `producer`, `producercar`, `session` | 001 | Contas, CARs da conta e sessões |
| `carsnapshot` | 001/007 | Cache do MapBiomas por CAR (`summary_json`, `detail_json`, `fetched_at`); inclui os embargos do IBAMA quando usados |
| `car_indicators_snapshot` | 003 | Cache dos indicadores por CAR (`payload` JSON, `fetched_at`) |
| `sinaflor_car`, `sinaflor_sync` | 003 | Resumo do POA por CAR e metadados da última sincronização |

- `create_all` **não altera tabelas existentes**. Campos novos vão em tabelas novas ou como campos
  opcionais dentro dos JSON de cache; uma mudança de esquema numa tabela existente exige migração.
- O engine usa **`NullPool`**: cada `Session` abre e fecha a própria conexão. Com o pool padrão (5 + 10),
  as vistas que carregam vários CARs em paralelo (uma `Session` por CAR com `asyncio.gather`) esgotavam
  as conexões, o checkout bloqueava o event loop e o servidor inteiro parava de responder.

### Regras de negócio (onde ficam)

| Regra | Arquivo | Resumo |
|---|---|---|
| Validação de CNPJ e CAR | `app/validators.py` | CNPJ com dígitos verificadores; CAR `UF-NNNNNNN-<32 hex>` |
| Deduplicação de embargos | `services/car_service.py` (`merge_embargo_items`) | Embargos únicos por (órgão, processo) ou (órgão, código); a mesma função para MapBiomas e IBAMA |
| Embargos de respaldo (007) | `sources/ibama.py` · `car_service.build_detail` | Se o MapBiomas não determina os embargos e o CAR tem polígono, usa as áreas embargadas do IBAMA que se sobrepõem ≥ 0,1 ha (`IBAMA_MIN_OVERLAP_HA`), todas vigentes |
| Situação de cada alerta | `services/car_indicators.py` (`classify_alert`) | Suspensa judicial > embargo vigente > autorizada > embargo levantado > com fiscalização > pendente |
| Indicadores do CAR | `services/car_indicators.py` (`build_indicators`, `get_indicators`) | Uma fonte por bloco; cache de 24 h; o SINAFLOR é relido da tabela local a cada resposta |
| Nível do CAR (006) | `services/level_rules.py` (`car_level`) | Entradas: `get_detail` + `get_indicators`. Lista todos os motivos com números e o sinal `eudr_attention`. Regras completas em [`proposta-regras-nivel.md`](proposta-regras-nivel.md) |
| Nível do CNPJ (006) | `services/level_rules.py` (`cnpj_level`), via `cnpj_report.cnpj_status` | O pior CAR com dados; `cars_by_level`; motivos contam CARs. Usado no painel, na ficha pública e no relatório |
| Agregação por CNPJ | `services/cnpj_report.py` (`cnpj_codes`, `aggregate_cars`) | CARs sem repetição de todas as contas com o mesmo CNPJ; alertas únicas por código |
| Score | `services/cnpj_report.py` (`get_score`) | Hoje só o estado (`em_calculo` / `nao_calculavel`); ponto de substituição do método |
| Números do CNPJ | `services/cnpj_overview.py` (`cnpj_overview`) | Reaproveita `get_indicators` (situação das alertas) e `get_detail` (embargos); embargo vigente único por (órgão, processo) |
| Relatório do CNPJ | `reports/` (`get_report`, `facts.py`, `prompt.py`) | Dados já calculados com pseudônimos → IA → controles (números, pseudônimos, vocabulário); reserva por regras; impõe `nivel` = regras |
| Auditoria mensal | `services/ai_auditor_service.py` (`audit_monthly_report`) | Cobertura de CARs nas NFs, estouro de volume por CAR, "CAR coringa", embargos e parecer |

O painel e a ficha pública usam **o mesmo código** para o nível (há teste de paridade). Se uma regra de
nível mudar, atualize também [`proposta-regras-nivel.md`](proposta-regras-nivel.md) e os textos de
"Entenda o nível" (`t.rules` em `pt-BR.ts`).

### Relatório do CNPJ (features 005 e 008)

A IA **só consolida e explica** dados que o sistema já calculou; não calcula nem decide o nível.

1. **Modo demonstração** (`REPORT_DEMO_MODE=true`): se existe `MOCK_REPORTS_DIR/<cnpj>.json` (padrão
   `backend/data/mock_reports/`, **fora do git**), usa-o com `origem="exemplo"` (inválido →
   `indisponivel`). Sem o modo, o arquivo é ignorado.
2. **Dados**: `car_inputs` carrega detalhe e indicadores de cada CAR (uma vez), `car_level`/`cnpj_level`
   dão nível e motivos, e `reports/facts.py` (`build_report_facts`, puro) monta o JSON enviado à IA:
   totais do CNPJ já somados e, por imóvel, UF, área, nível, motivos, alertas por situação, embargos com
   fonte e estado, contexto (vegetação nativa, DETER 24 meses, focos, SINAFLOR, UCs de uso sustentável) e
   fontes indisponíveis. Valores desconhecidos vão como texto (`indisponivel`, `nao_determinavel`), nunca 0.
   Hectares e % com 1 decimal; no máximo 40 imóveis (do mais grave ao menos grave).
3. **Pseudônimos**: a IA recebe "Imóvel A", "Imóvel B"… e **nunca** os códigos de CAR nem o CNPJ. Na
   volta, o texto corrido recebe o prefixo `UF-MUNICÍPIO` do CAR (ou o código completo se o prefixo se
   repete) e `imoveis[].car_code` recebe o código completo.
4. **IA** (`call_llm`): `reports/prompt.py` (`SYSTEM_PROMPT`, `PROMPT_VERSION`), JSON de dados como mensagem
   do usuário, `temperature` 0,2, timeout `LLM_TIMEOUT_S`.
5. **Controles** (`_validate_llm`): corta riscos/contexto em 3; título obrigatório; sem "ilegal"/"crime";
   cada número do texto tem de existir nos dados (`allowed_numbers`: valores com 1 decimal ou inteiro
   arredondado, datas dos dados e os números das regras 2020, 31, 12, 24, 1 e 0,1; lê formatos pt-BR); só
   pseudônimos existentes. Imóvel que a IA esqueceu recebe a frase por regras. Falhou → **um** retry; erro
   de rede ou timeout → sem retry.
6. **Reserva**: sem chave, ou se a IA falha, `_build_deterministic_report` com `origem="regras"`.
7. **Cache em memória** (`_cache`): chave = SHA-256 dos dados + `PROMPT_VERSION` + modelo. Texto da IA vale
   até os dados mudarem; texto por regras, 15 min (para tentar a IA de novo). Máximo 256 entradas; some ao
   reiniciar.

Sempre: `nivel` = regras da 006; CNPJ não cadastrado ou sem CARs → `status=indisponivel`. Na interface,
`origem="agente"` mostra o aviso **"Gerado por IA"** no topo do relatório; `regras` e `exemplo` têm notas
próprias.

A proposta original do agente (regras do prompt, controles) está em [`proposta-agente.md`](proposta-agente.md).

### Auditoria mensal com IA

- **Oculta por enquanto**: `POST /api/audit/generate-report` (`routers/audit.py`) responde 404 a menos que
  `AUDIT_ENABLED=true` (a autenticação é verificada antes: sem sessão, 401). No frontend, o
  `AuditReportModal` continua montado no `AppLayout`, mas nenhum botão o abre. O código e os testes foram
  mantidos para quando houver uma fonte real de notas fiscais.
- **As notas fiscais são simuladas**: `_generate_mock_monthly_invoices` gera NFs fictícias. Há dois CNPJs
  de demonstração com casos próprios (`04654691000106` excelente, `11222333000181` atenção); **qualquer
  outro CNPJ recebe o caso crítico** (estouro de volume e concentração num CAR). Ainda não há fonte real de
  NFs, então o parecer da auditoria não reflete a situação real do produtor.
- `audit_monthly_report` aplica quatro verificações (cobertura de CARs nas NFs, estouro de volume por CAR
  frente ao volume autorizado no SINAFLOR, concentração > 80 % num único CAR, NFs em imóveis com embargo) e
  pede o parecer ao mesmo LLM do relatório, com parecer determinístico se o LLM não responder.
- Scripts de dados de demonstração: `backend/seed_3_use_cases.py` e `backend/seed_mock_producer.py`
  (criam contas fictícias `@rebootearth.com`).

### Tolerância a falhas e cache

- **MapBiomas**: timeout de 20 s, cache de 24 h por CAR. Se a fonte cai, serve o cache com `stale=true`;
  sem cache, "indisponível".
- **Embargos (007)**: o resumo traz `embargoes_source` (`mapbiomas`/`ibama`), `embargoes_checked_at` e
  `embargoes_stale`. Se numa recarga nenhuma fonte determina os embargos mas o cache anterior sim,
  mantêm-se os embargos anteriores com `embargoes_stale=true` e a data original
  (`keep_previous_embargoes`). IBAMA: timeout de 5 s.
- **Indicadores**: cada fonte (`mapbiomas`, `prodes`, `deter`, `focos`, `sinaflor`) tem seu próprio
  `SourceStatus` (`ok` / `indisponivel` / `nao_se_aplica`, `fetched_at`, `stale`). Se uma falha,
  reaproveita-se o bloco dela do cache anterior com `stale=true`. INPE: timeout de 3 s por consulta.
- **LLM**: timeout `LLM_TIMEOUT_S` (30 s); qualquer falha cai no texto por regras; o relatório fica em cache em memória.
- **Três estados sempre distintos**: valor (inclusive 0), "Indisponível" e "Não se aplica". `null` nunca
  é mostrado como 0.

## 3. Fontes externas

### MapBiomas Alerta (GraphQL, `app/mapbiomas/`)

- Login com `MAPBIOMAS_EMAIL` / `MAPBIOMAS_PASSWORD`; o token fica em memória e é renovado em caso de erro de autenticação.
- Queries em `queries.py`:
  - `ruralProperty` (polígono e alertas);
  - `alerts(propertyCodes: [ID!])` (embargos e, na 003, os campos `crossed*` de autorização, reserva legal, APP, TI e UCs, além de `actionsList`);
  - `pointInformation(boundingBox)` (embargos de CARs sem alertas: ver abaixo);
  - `findSuspendedJudicialAlert(carCode: String!)`.
- **`pointInformation` não serve para embargos (verificado em 2026-11-08)**: responde HTTP 500 com corpo vazio sempre que se pedem `embargoedAreasCount` ou `embargoedAreas` (só `carCode` funciona). Como é a única via para CARs sem alertas, esses CARs usam o respaldo do IBAMA (feature 007). `ruralProperty` não tem campos de embargo.
- **Tipos importam**: `propertyCodes` é `[ID!]` e `carCode` é `String!`; com outro tipo, a API devolve erro.
- Reserva legal, APP e UCs vêm calculadas **sobre a alerta inteira**. O backend limita cada valor à área da alerta dentro do CAR.
- O mesmo embargo pode vir com o processo em formatos diferentes (`02048.000439/2012-63` e `02048000439201263`) e é contado duas vezes; normalizar o formato ainda não foi feito.
- Schema completo: [`SCHEMA.md`](../SCHEMA.md) e `schema.json`.

### INPE TerraBrasilis (WFS público, `app/sources/inpe.py`)

- Endpoints:
  - `https://terrabrasilis.dpi.inpe.br/geoserver/ows` (biomas, PRODES, DETER);
  - `https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs` (focos de calor).
- Camadas:

| Uso | Camada | Geometria / filtros |
|---|---|---|
| Biomas cruzados | `prodes-brasil-nb:biomas_brasil` | `geom`; atributo `bioma` |
| Desmatamento anual e acumulado | `prodes-{amazon,cerrado,caatinga,mata-atlantica,pampa,pantanal}-nb:yearly_deforestation*` e `accumulated_deforestation_*` | `geom`; atributo `year` |
| DETER | `deter-amz:deter_amz` | `geom`; `view_date >= '2021-01-01'`; atributo `classname` |
| Focos de calor | `bdqueimadas2:focos` | `geometria`; `data_hora_gmt`, `eh_satelite_referencia = true` |

- **Regras verificadas contra o servidor real**:
  - Use WFS 1.1.0 com `CQL_FILTER=INTERSECTS(geom, SRID=4326;<WKT lon lat>)`. **Sem o prefixo `SRID`, o servidor lê o WKT como lat/lon e não devolve nada.**
  - **Não use o parâmetro `bbox` para filtrar camadas grandes**: ele compara caixas (o bioma Amazônia "cruza" um CAR do Cerrado). E `bbox` + `CQL_FILTER` juntos geram erro.
  - O filtro manda a envoltória convexa simplificada do CAR (um superconjunto). A interseção exata e a união das camadas que se sobrepõem entre biomas são feitas localmente com `shapely`. As áreas são calculadas por aproximação equirretangular, com erro < 1 %.
- O DETER só se aplica se o CAR cruzar o bioma Amazônia. Classes: `CS_GEOMETRICO` (padrão de manejo), `CS_DESORDENADO`, `DEGRADACAO`, `CICATRIZ_DE_QUEIMADA`, `MINERACAO`, `DESMATAMENTO_CR`/`_VEG`.
- O PRODES **não registra regeneração**: uma área desmatada e regenerada continua contando como desmatada.
- O cálculo dos indicadores (interseções com `shapely`) roda no event loop: a primeira carga de vários CARs grandes sem cache deixa o servidor lento por alguns minutos.

### IBAMA – áreas embargadas (ArcGIS público, `app/sources/ibama.py`, feature 007)

- Endpoint: `https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/adm_embargos_ibama_a/FeatureServer/0/query` (`settings.ibama_embargoes_url`). Sem credenciais; ~92 mil polígonos, atualizada diariamente.
- Consulta: `POST` (form) com `f=geojson`, `geometryType=esriGeometryPolygon`, `geometry` = envoltória convexa simplificada do CAR em anéis ESRI, `inSR=outSR=4326`, `spatialRel=esriSpatialRelIntersects`, `returnGeometry=true`, `resultRecordCount=2000`. A sobreposição exata com o CAR é calculada localmente com `shapely`.
- `outFields=num_tad,serie_tad,num_processo,dat_embargo,qtd_area_embargada,des_tad`. **Nunca peça `cpf_cnpj_embargado` nem `nome_embargado`** (dados pessoais; princípio III).
- `dat_embargo` chega em epoch ms. A camada **não tem campo de levantado/cancelado**: todo embargo que conta é vigente.
- Resposta com `exceededTransferLimit` (na raiz ou em `properties`) = indisponível: nunca uma lista parcial como completa.
- Só embargos do IBAMA: a camada do ICMBio (`adm_embargo_icmbio_a`) é uma foto de 2022 e não é usada. Os endpoints `siscom.ibama.gov.br/geoserver` e `embargos_siscom_brasil` respondem 404.

### IBAMA SINAFLOR (CSV diário, `app/sources/sinaflor.py`)

- Fonte: `…/SINAFLOR/poaAmazoniaLegal/sinaflor-poa-amazonia-legal.csv`, com cerca de 90 MB, separador `;` e UTF-8 com BOM. Atualizado diariamente.
- `uv run python -m app.sources.sinaflor` baixa o arquivo em streaming, agrega por `NRO_CAR_IMOVEL_RURAL` e substitui `sinaflor_car`. Leva uns 5 s e carregou 3.434 CARs em 2026-11-06.
  - Autorizações são contadas por número distinto; "vigentes" são as com situação Emitida ou Retificada.
  - O volume soma os produtos em m³, ficando com o máximo de cada (autorização, espécie, produto), porque o IBAMA reportou duplicados.
- Só vale para CARs da Amazônia Legal. Sem nenhuma sincronização, o indicador aparece como "indisponível".
- Uma autorização pode abranger vários CARs, e o mesmo volume aparece em cada um.

### LLM (opcional, `app/reports/__init__.py` e `app/services/ai_auditor_service.py`)

- API compatível com a da OpenAI (`/chat/completions`); padrão: Gemini `gemini-3.5-flash` via
  `generativelanguage.googleapis.com`. Configuração em `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL` e
  `LLM_TIMEOUT_S`.
- Sem `LLM_API_KEY` (ou com o valor de exemplo do `.env.example`), o LLM não é chamado e tudo usa o
  texto determinístico.

## 4. Frontend

- **Stack**: React 19, Vite, React Router, Leaflet e Vitest. `src/api/client.ts` é o único acesso ao backend. **Todos os textos** ficam em `src/i18n/pt-BR.ts` (nome da marca: `appName = 'Elo Rural'`).
- **Rotas**:
  - públicas: `/`, `/login`, `/registro`, `/consulta` e `/consulta/:cnpj`;
  - autenticadas: `/painel` (início), `/painel/cars`, `/painel/cars/:code`, `/painel/nivel` ("Entenda o nível") e `/painel/consulta[/:cnpj]`.
- **Layouts**:
  - `layout/AppLayout` (barra lateral do painel) e `layout/AuthLayout` (login e cadastro);
  - a portada e a página `/consulta` têm cabeçalho próprio; o `Header` público do `App.tsx` não aparece nessas páginas.
- **Páginas e componentes principais**:

| Página / componente | Uso |
|---|---|
| `CarsPage`, `CarCard`, `CarMap` | "Meus CARs": cartão do CAR (mapa, nível, alertas, embargos, sinal EUDR) |
| `CarDetailPage` | Detalhe do CAR: nível e motivos, alertas, embargos com fonte (MapBiomas/IBAMA) e indicadores |
| `CarIndicators` (`IndicatorsView`, `Help`), `IndicatorValue` | Blocos "Riscos abertos" e "Contexto"; os três estados; ajuda de termos (ex.: APP) |
| `LevelRulesPage` | "Entenda o nível": regras, glossário, fontes e links (textos em `t.rules`) |
| `StatusBadge`, `CnpjReportCard`, `CnpjSearch`, `PublicCnpjPage` | Nível Gold/Silver/Bronze/Sem dados, ficha pública, busca com validação de CNPJ |
| `HomePage`, `CnpjReportView` | Início: status do CNPJ, 3 números e relatório, com aviso de origem (exemplo/agente) |
| `AuditReportModal` | Auditoria mensal de NFs × CARs (dados de NF simulados). Montado no `AppLayout`, mas sem botão que o abra |
| `LotOverview` | Módulo de lotes do redesign. **Fora do Início** (não há fonte de lotes); só na prévia `/preview/lotes` |
| `BrandMark` | Logotipo |

- **Início** (`/painel`, features 005 e 008): 3 números (CARs, alertas abertas, embargos vigentes) e o relatório do CNPJ. O cabeçalho do relatório mostra o nível do CNPJ, o sinal "Atenção EUDR" e os imóveis por nível, vindos de `/api/dashboard` (regras), e não do texto: aparecem mesmo se o relatório falhar. Embaixo, o link "Entenda os níveis". Números e relatório carregam à parte. (O antigo cartão "Status do CNPJ" saiu em 2026-11-08.)
- **Preview de design** (só em desenvolvimento, sem backend, fora do build de produção): `/preview/painel` mostra o Início com dados fictícios; `/preview/lotes` mostra o módulo de lotes. Notas e limites: [`frontend/design-dashboard.md`](../frontend/design-dashboard.md).
- **Estilo**: `index.css` (tokens e componentes base) e CSS por página/layout (`LandingPage.css`, `HomePage.css`, `PublicCnpjPage.css`, `LevelRulesPage.css`, `AppLayout.css`, `AuthLayout.css`). Os blocos de indicadores (003), no detalhe do CAR, ainda usam o estilo anterior ao redesign.

## 5. Testes

| Onde | O quê |
|---|---|
| `backend/tests/unit/` | Funções puras: validadores, agregação, `car_level`/`cnpj_level` (`test_level_rules.py`), `classify_alert`, deduplicação de embargos, embargos do IBAMA (`test_ibama.py`), geometria, agregação do SINAFLOR, rate limit, auditoria (regras puras), dados e controles do relatório (`test_report_facts.py`) e o `NullPool` do engine |
| `backend/tests/integration/` | API com fontes simuladas: autenticação, CARs, resumo e detalhe, nível por CAR e público, dashboard, overview, relatório, ficha pública (privacidade, falhas, 429), indicadores (falha por fonte, 401/404, cache), respaldo do IBAMA (`test_embargoes_ibama.py`), relatório com IA simulada (`test_dashboard_report.py`) e auditoria |
| `backend/tests/conftest.py` | Via `respx`: `FakeMapBiomas` (`properties`, `embargoes`, `alert_extra`, `judicial`, `down`, `point_down` = o 500 real do `pointInformation`), `FakeInpe` (fixture `inpe`: `layers`, `down`) `FakeIbama` (fixture `ibama`: `features`, `down` — **caído por padrão**, `truncated`, `calls`) e `FakeLlm` (fixture `llm`: `response`, `status`, `timeout`, `bodies`). Fixtures autouse: sem chave de LLM real e cache do relatório limpo |
| `backend/tests/fixtures/` | Resposta real do MapBiomas para o CAR PE-2607505 e amostra do CSV do SINAFLOR |
| `frontend/tests/` | Componentes e páginas com `fetch` simulado |

Gates obrigatórios: `uv run ruff check .`, `uv run pytest`, `npm run build` e `npm test`. Nenhum teste usa a
rede. Os testes usam um engine próprio em memória (`StaticPool`), então não exercitam o pool do engine real.

## 6. Operação

- **Configuração**: `.env` na raiz (lista completa em [`desenvolvimento.md`](desenvolvimento.md#configuração)). Valores relevantes:
  - `CACHE_TTL_HOURS` (24);
  - `PUBLIC_SEARCH_LIMIT_PER_HOUR` (30);
  - `TRUST_PROXY_HEADERS` (só atrás de um proxy confiável);
  - `INPE_TIMEOUT_S` (3), `IBAMA_TIMEOUT_S` (5), `LLM_TIMEOUT_S` (30);
  - `LLM_API_KEY` (opcional: sem ela, relatório e auditoria usam texto determinístico);
  - `REPORT_DEMO_MODE` (padrão `false`: o relatório de exemplo escrito à mão só aparece com `true`);
  - `AUDIT_ENABLED` (padrão `false`: auditoria mensal oculta enquanto as NFs forem simuladas);
  - `COOKIE_SECURE=true` em produção.
- **Tarefa diária**: `cd backend && uv run python -m app.sources.sinaflor` (por exemplo, via cron).
- **Limitações conhecidas**:
  - O rate limit fica na memória de um único processo; com vários workers, precisa de um armazenamento compartilhado.
  - A primeira consulta dos indicadores de vários CARs sem cache pode levar alguns minutos e deixa o servidor lento (cálculo geométrico no event loop); as seguintes vêm do cache.
  - A relação entre alerta e embargo vigente é aproximada.
  - As notas fiscais da auditoria mensal são simuladas; por isso ela fica desligada (`AUDIT_ENABLED=false`).
- **Dados locais**: `data/` (respostas reais de CARs de exemplo) está no `.gitignore` e não deve ir para commits.
