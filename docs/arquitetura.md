# Arquitetura técnica

**Atualizado em**: 2026-11-06 · **Estado**: `main` em `859179c` (features 001, 002 e 003 + redesign do frontend)

Documento de referência para quem mantém o código. Produto e motivação: [`README.md`](../README.md).
Regras de governança: [constituição](../.specify/memory/constitution.md). Detalhe de cada feature:
`specs/NNN-*/` (spec, plan, research, data-model, contratos, tasks e quickstart).

## 1. Visão geral

```
Navegador (React SPA, pt-BR)
   │  só /api (proxy do Vite em dev)
   ▼
FastAPI (backend/app)
   ├─ routers/        auth · cars · dashboard · public
   ├─ services/       car_service · cnpj_report · car_indicators   ← regras de negócio (funções puras)
   ├─ mapbiomas/      cliente GraphQL + queries (credenciais só aqui)
   ├─ sources/        inpe (WFS) · sinaflor (CSV diário) · geo (shapely)
   ├─ rate_limit.py   limite das consultas públicas
   └─ SQLite          contas, CARs e caches
          │
          ├──► MapBiomas Alerta (GraphQL, com login)
          ├──► INPE TerraBrasilis (WFS público: PRODES, DETER, biomas, focos de calor)
          └──► IBAMA dados abertos (CSV do POA Amazônia Legal, sincronizado 1×/dia)
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
| `GET /api/cars/{car}/summary` · `/detail` | ✓ | 001 | Polígono, alertas e embargos (cache de 24 h, `?refresh=true`) |
| `GET /api/cars/{car}/indicators` | ✓ | 003 | Indicadores socioambientais (riscos abertos e contexto) |
| `POST /api/audit/generate-report` | ✓ | AI-Agent | Auditoria mensal consolidada de NFs x CARs e parecer do Consultor ESG |
| `GET /api/dashboard` | ✓ | 001/002 | Totais da conta + `cnpj_status` / `cnpj_score` do CNPJ |
| `GET /api/public/cnpj/{cnpj}` | — | 002 | Ficha pública agregada; rate limit de 30/h por IP |
| `GET /api/health` | — | — | Saúde |

Um CAR de outro produtor responde **404**; sem sessão, **401**. As rotas de dados nunca respondem 503
por falha de uma fonte externa quando há cache ou um estado "indisponível" para mostrar. Contratos:
`specs/00N-*/contracts/openapi.yaml`.

### Tabelas (SQLite, criadas por `create_all` no startup)

| Tabela | Feature | Conteúdo |
|---|---|---|
| `producer`, `producercar`, `session` | 001 | Contas, CARs da conta e sessões |
| `carsnapshot` | 001 | Cache do MapBiomas por CAR (resumo e detalhe, `fetched_at`) |
| `car_indicators_snapshot` | 003 | Cache dos indicadores por CAR (`payload` JSON, `fetched_at`) |
| `sinaflor_car`, `sinaflor_sync` | 003 | Resumo do POA por CAR e metadados da última sincronização |

`create_all` **não altera tabelas existentes**. Por isso os campos novos vão em tabelas novas; uma
mudança de esquema numa tabela existente exige migração.

### Regras de negócio (onde ficam)

| Regra | Arquivo | Resumo |
|---|---|---|
| Validação de CNPJ e CAR | `app/validators.py` | CNPJ com dígitos verificadores; CAR `UF-NNNNNNN-<32 hex>` |
| Deduplicação | `services/car_service.py` · `services/cnpj_report.py` | Alertas únicas por código; embargos únicos por (órgão, processo) |
| Agregação por CNPJ | `services/cnpj_report.py` (`aggregate_cars`, `cnpj_aggregate`) | CARs sem repetição de todas as contas com o mesmo CNPJ |
| Nível (provisório, FR-111a) | `services/cnpj_report.py` (`compute_status`) | Sem dados → Bronze (embargo) → Silver (alerta ou dados parciais) → Gold |
| Score | `services/cnpj_report.py` (`get_score`) | Hoje só o estado (`em_calculo` / `nao_calculavel`); ponto de substituição do método |
| Situação de cada alerta | `services/car_indicators.py` (`classify_alert`) | Suspensa judicial > embargo vigente > autorizada > embargo levantado > com fiscalização > pendente |
| Indicadores do CAR | `services/car_indicators.py` (`build_indicators`, `get_indicators`) | Uma fonte por bloco; cache de 24 h; SINAFLOR é sempre lido na hora |
| Auditoria Mensal ESG & IA | `services/ai_auditor_service.py` (`audit_monthly_report`) | Cobertura de CARs, estouro volumétrico, CAR coringa, cruzamento com SINAFLOR e parecer |

O painel e a ficha pública usam **o mesmo código** para o nível (há teste de paridade). Uma proposta
para substituir a regra provisória (abertas × superadas, nível do CNPJ pelo pior CAR, agente de
resumos) está em [`proposta-regras-nivel-e-agente.md`](proposta-regras-nivel-e-agente.md) e **ainda
não foi implementada**.

### Tolerância a falhas e cache

- **MapBiomas**: timeout de 20 s, cache de 24 h por CAR. Se a fonte cai, serve o cache com `stale=true`; sem cache, "indisponível".
- **Indicadores**: cada fonte (`mapbiomas`, `prodes`, `deter`, `focos`, `sinaflor`) tem seu próprio `SourceStatus` (`ok` / `indisponivel` / `nao_se_aplica`, `fetched_at`, `stale`). Se uma falha, reaproveita-se o bloco dela do cache anterior com `stale=true`.
- **Três estados sempre distintos**: valor (inclusive 0), "Indisponível" e "Não se aplica". `null` nunca é mostrado como 0.

## 3. Fontes externas

### MapBiomas Alerta (GraphQL, `app/mapbiomas/`)

- Login com `MAPBIOMAS_EMAIL` / `MAPBIOMAS_PASSWORD`; o token fica em memória e é renovado em caso de erro de autenticação.
- Queries em `queries.py`:
  - `ruralProperty` (polígono e alertas);
  - `alerts(propertyCodes: [ID!])` (embargos e, na 003, os campos `crossed*` de autorização, reserva legal, APP, TI e UCs, além de `actionsList`);
  - `findSuspendedJudicialAlert(carCode: String!)`.
- **Tipos importam**: `propertyCodes` é `[ID!]` e `carCode` é `String!`; com outro tipo, a API devolve erro.
- Reserva legal, APP e UCs vêm calculadas **sobre a alerta inteira**. O backend limita cada valor à área da alerta dentro do CAR.
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

### IBAMA SINAFLOR (CSV diário, `app/sources/sinaflor.py`)

- Fonte: `…/SINAFLOR/poaAmazoniaLegal/sinaflor-poa-amazonia-legal.csv`, com cerca de 90 MB, separador `;` e UTF-8 com BOM. Atualizado diariamente.
- `uv run python -m app.sources.sinaflor` baixa o arquivo em streaming, agrega por `NRO_CAR_IMOVEL_RURAL` e substitui `sinaflor_car`. Leva uns 5 s e carregou 3.434 CARs em 2026-11-06.
  - Autorizações são contadas por número distinto; "vigentes" são as com situação Emitida ou Retificada.
  - O volume soma os produtos em m³, ficando com o máximo de cada (autorização, espécie, produto), porque o IBAMA reportou duplicados.
- Só vale para CARs da Amazônia Legal. Sem nenhuma sincronização, o indicador aparece como "indisponível".
- Uma autorização pode abranger vários CARs, e o mesmo volume aparece em cada um.

## 4. Frontend

- **Stack**: React 19, Vite, React Router, Leaflet e Vitest. `src/api/client.ts` é o único acesso ao backend. **Todos os textos** ficam em `src/i18n/pt-BR.ts`.
- **Rotas**:
  - públicas: `/`, `/login`, `/registro`, `/consulta` e `/consulta/:cnpj`;
  - autenticadas: `/painel` (início), `/painel/cars`, `/painel/cars/:code` e `/painel/consulta[/:cnpj]`.
- **Layouts**:
  - `layout/AppLayout` (barra lateral do painel) e `layout/AuthLayout` (login e cadastro);
  - a portada e a página `/consulta` têm cabeçalho próprio; o `Header` público do `App.tsx` não aparece nessas páginas.
- **Componentes principais**:

| Componente | Uso |
|---|---|
| `CarCard`, `CarMap` | Cartão do CAR (mapa, alertas, embargos) |
| `CarIndicators` (`IndicatorsView`), `IndicatorValue` | Blocos "Riscos abertos" e "Contexto" no **detalhe do CAR** (o cartão não os mostra); os três estados; ajuda de termos (ex.: APP) |
| `StatusBadge`, `CnpjReportCard`, `CnpjSearch` | Nível Gold/Silver/Bronze/Sem dados, ficha pública, busca com validação de CNPJ |
| `LotOverview` | Visão de lotes do início (redesign). Sem fonte no backend: os campos aparecem como não disponíveis |

- **Preview de design** (só em desenvolvimento): `/preview/painel` mostra o início com dados fictícios de 3 lotes, sem backend. Fica fora do build de produção. Notas e limites: [`frontend/design-dashboard.md`](../frontend/design-dashboard.md).
- **Estilo**: `index.css` (tokens e componentes base) e CSS por página/layout (`LandingPage.css`, `HomePage.css`, `PublicCnpjPage.css`, `AppLayout.css`, `AuthLayout.css`). Os blocos de indicadores (003), no detalhe do CAR, ainda usam o estilo anterior ao redesign.

## 5. Testes

| Onde | O quê |
|---|---|
| `backend/tests/unit/` | Funções puras: validadores, agregação, `compute_status`, `classify_alert`, geometria do INPE, agregação do SINAFLOR, rate limit |
| `backend/tests/integration/` | API com fontes simuladas: autenticação, CARs, dashboard, ficha pública (privacidade, falhas, 429), indicadores (falha por fonte, 401/404, cache) |
| `backend/tests/conftest.py` | `FakeMapBiomas` (`properties`, `embargoes`, `alert_extra`, `judicial`, `down`) e `FakeInpe` (fixture `inpe`: `layers`, `down`), via `respx` |
| `backend/tests/fixtures/` | Resposta real do MapBiomas para o CAR PE-2607505 e amostra do CSV do SINAFLOR |
| `frontend/tests/` | Componentes e páginas com `fetch` simulado |

Gates obrigatórios: `uv run ruff check .`, `uv run pytest`, `npm run build` e `npm test`. Nenhum teste usa a
rede.

## 6. Operação

- **Configuração**: `.env` na raiz (veja o README). Valores relevantes:
  - `CACHE_TTL_HOURS` (24);
  - `PUBLIC_SEARCH_LIMIT_PER_HOUR` (30);
  - `TRUST_PROXY_HEADERS` (só atrás de um proxy confiável);
  - `INPE_TIMEOUT_S` (30);
  - `COOKIE_SECURE=true` em produção.
- **Tarefa diária**: `cd backend && uv run python -m app.sources.sinaflor` (por exemplo, via cron).
- **Limitações conhecidas**:
  - O rate limit fica na memória de um único processo; com vários workers, precisa de um armazenamento compartilhado.
  - A primeira consulta dos indicadores de um CAR grande pode levar dezenas de segundos (INPE); as seguintes vêm do cache.
  - A relação entre alerta e embargo vigente é aproximada.
- **Dados locais**: `data/` (respostas reais de CARs de exemplo) **não é versionado** e não deve ir para commits.
