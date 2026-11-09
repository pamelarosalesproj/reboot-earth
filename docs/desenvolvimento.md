# Guia de desenvolvimento

Como rodar, configurar e testar o Elo Rural, e como cada funcionalidade se comporta tecnicamente. Para
endpoints, tabelas, regras no código e as armadilhas das fontes externas, veja
[`arquitetura.md`](arquitetura.md). As regras de nível estão em
[`proposta-regras-nivel.md`](proposta-regras-nivel.md).

## Estrutura do repositório

| Caminho | Conteúdo |
| --- | --- |
| `backend/` | API em Python 3.12 (FastAPI + SQLModel/SQLite), intermediária para MapBiomas, INPE e IBAMA |
| `frontend/` | SPA em TypeScript (React + Vite + Leaflet): landing em `/`, consulta em `/consulta`, painel em `/painel` |
| `frontend/design-dashboard.md` | Notas e limites do redesign do início do painel (preview em `/preview/painel`, só em dev) |
| `docs/arquitetura.md` | Documentação técnica: endpoints, tabelas, regras, fontes externas, testes e operação |
| `docs/proposta-regras-nivel.md` | Regras de nível Gold/Silver/Bronze em uso |
| `docs/proposta-agente.md` | Proposta do agente de resumos (ainda não implementada) |
| `specs/NNN-*/` | Spec, plano, research, data model, contratos (`contracts/openapi.yaml`), tarefas e quickstart de cada feature (Spec Kit) |
| `.specify/memory/constitution.md` | Constituição do projeto (princípios I–VII) |
| `data/cars_ejemplo/` | Respostas reais do MapBiomas para CARs de vários estados (**local, não versionado**) |
| `mapbiomas_api.py`, `dof_ibama.py` | Scripts de exploração das fontes (não são usados pela aplicação) |
| `SCHEMA.md`, `schema.json` | Documentação do schema GraphQL do MapBiomas Alerta |

Features: `001-producer-car-dashboard` (painel do produtor), `002-cnpj-score-search` (consulta pública),
`003-car-indicators` (indicadores do CAR), `005-dashboard-init` (Início), `006-nivel-regras` (regras de
nível e "Entenda o nível") e `007-embargos-ibama` (embargos do IBAMA como respaldo).

## Requisitos

- [`uv`](https://docs.astral.sh/uv/) (instala o Python 3.12 automaticamente)
- Node 24 e npm

## Configuração

`.env` na raiz do repositório (não é versionado):

```env
MAPBIOMAS_EMAIL=seu@email.com
MAPBIOMAS_PASSWORD=...
MAPBIOMAS_API_URL=https://plataforma.alerta.mapbiomas.org/api/v2/graphql
# Opcionais
# DATABASE_URL=sqlite:////caminho/absoluto/app.db   (padrão: backend/data/app.db)
# COOKIE_SECURE=true                                (obrigatório em produção com HTTPS)
# CORS_ORIGINS=["http://localhost:5173"]
# PUBLIC_SEARCH_LIMIT_PER_HOUR=30                    (consultas públicas por CNPJ, por IP e por hora)
# TRUST_PROXY_HEADERS=false                          (true só atrás de um proxy confiável: usa X-Forwarded-For)
# CACHE_TTL_HOURS=24                                 (cache por CAR do MapBiomas e dos indicadores)
# INPE_TIMEOUT_S=30                                  (timeout por consulta aos WFS do INPE)
# IBAMA_TIMEOUT_S=5                                  (timeout da consulta às áreas embargadas do IBAMA)
# MOCK_REPORTS_DIR=backend/data/mock_reports         (relatórios de exemplo por CNPJ, fora do git)
```

INPE e IBAMA são fontes públicas: não precisam de credenciais. As credenciais do MapBiomas são usadas só
no backend; nunca chegam ao navegador.

## Como rodar

```bash
# Backend → http://localhost:8000 (documentação interativa em /docs)
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000

# Frontend → http://localhost:5173 (proxy /api → :8000)
cd frontend && npm install && npm run dev

# Uma vez por dia (indicador de manejo florestal): resumo do SINAFLOR por CAR
cd backend && uv run python -m app.sources.sinaflor
```

## Testes

```bash
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm run build && npm test
```

Testes sem rede: MapBiomas, INPE e as áreas embargadas do IBAMA simulados com `respx`, SINAFLOR com um
CSV de amostra.

Validação manual de ponta a ponta: [`001`](../specs/001-producer-car-dashboard/quickstart.md),
[`002`](../specs/002-cnpj-score-search/quickstart.md), [`003`](../specs/003-car-indicators/quickstart.md),
[`006`](../specs/006-nivel-regras/quickstart.md) e [`007`](../specs/007-embargos-ibama/quickstart.md).

## Consulta pública por CNPJ

- **Telas**: `/consulta` e `/consulta/:cnpj` (link compartilhável), sem login. Acesso pela aba
  "Consultar CNPJ" da barra superior, pelo botão "É comprador? Consulte o status do seu produtor" da
  página inicial e, para produtores logados, pela barra lateral do painel (`/painel/consulta`).
- **API**: `GET /api/public/cnpj/{cnpj}` (com ou sem máscara). Responde 200 também para CNPJ não
  cadastrado (`Sem dados`), 422 para CNPJ inválido e 429 com `Retry-After` ao passar do limite.
  Contrato: [`specs/002-cnpj-score-search/contracts/openapi.yaml`](../specs/002-cnpj-score-search/contracts/openapi.yaml).
- **O que mostra**: nível (Gold / Silver / Bronze / Sem dados), estado do score ("Score em cálculo"
  enquanto o método não existe), número de propriedades e data dos dados. **Nunca** códigos de CAR,
  mapas ou dados da conta.
- **Regra do nível**: a da feature 006 (`backend/app/services/level_rules.py`), a mesma do painel.
  A regra provisória da 002 foi substituída.
- **Limitação conhecida**: o limite de consultas fica na memória do processo; vale para um único
  processo do backend. Com vários workers ou réplicas, mover o contador para um armazenamento compartilhado.

## Indicadores do CAR

O cartão de cada CAR em "Meus CARs" fica enxuto (mapa, alertas e embargos). Os indicadores aparecem no
**"Ver detalhes"** do CAR, em dois blocos (feature 003):

- **Riscos abertos**: alertas por situação legal (embargo vigente, com fiscalização, sem autorização
  registrada), desmatamento pós-2020 (corte EUDR), alertas abertas em reserva legal e APP, embargos
  vigentes, sobreposição com terra indígena ou UC de proteção integral.
- **Contexto**: alertas superadas (autorizadas, embargo levantado, suspensas judicialmente), embargos
  levantados, UC de uso sustentável, % de vegetação nativa remanescente (INPE PRODES), degradação e
  corte seletivo (INPE DETER, só bioma Amazônia), focos de calor em 12 meses (INPE Queimadas) e manejo
  florestal autorizado (IBAMA SINAFLOR, só Amazônia Legal).

Cada indicador distingue **valor** (inclusive 0), **Indisponível** (a fonte não respondeu e não há
cache) e **Não se aplica**. Os indicadores ficam em cache por 24 h e cada fonte falha de forma
independente. Desde a feature 006, parte dos riscos abertos entra no nível; o contexto nunca rebaixa o
nível, e a falha de PRODES, DETER, Queimadas ou SINAFLOR também não.

O SINAFLOR é um CSV diário de ~90 MB do IBAMA, resumido por CAR numa tabela local. Rodar uma vez por dia
(ex.: cron); até a primeira execução o indicador aparece como "Indisponível".

Limitações: reserva legal, APP e UCs vêm calculadas pelo MapBiomas sobre a área da alerta (limitadas à
área dentro do CAR); o PRODES não registra regeneração; o volume do SINAFLOR é o da autorização, que pode
abranger vários CARs.

## Comportamento quando o MapBiomas falha

- Timeout de 20 s por consulta. Os dados ficam em cache por 24 h por CAR (botão "Atualizar" para forçar).
- Se o MapBiomas não responde: aparece a última consulta marcada como "desatualizado", ou
  "dados indisponíveis" + "Tentar novamente" se nunca foi consultado. Cada cartão é independente.
- O cadastro (email, CNPJ e senha) não depende do MapBiomas. Os CARs são adicionados depois no painel;
  para isso o MapBiomas é consultado e, se não responder, pede-se para tentar mais tarde.
- Um CAR que o MapBiomas não tem registrado (sem alertas) é aceito e marcado como tal.
- **Embargos** (feature 007): se o MapBiomas não consegue informá-los (hoje acontece com os CARs sem
  alertas), o backend consulta as áreas embargadas do IBAMA que se sobrepõem 0,1 ha ou mais ao polígono do
  CAR. O detalhe do CAR indica a fonte e a data. Se o IBAMA também não responde, os embargos aparecem como
  "indisponíveis" e o nível marca "dados parciais", nunca "0 embargos".
