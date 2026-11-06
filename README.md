# RebootEarth

Plataforma que mostra, de forma simples e rastreável, a situação socioambiental de produtores
rurais brasileiros: **polígono de cada imóvel (CAR), alertas de desmatamento, embargos e indicadores
socioambientais**, com dados do **MapBiomas Alerta**, do **INPE** (PRODES, DETER, Queimadas) e do
**IBAMA** (SINAFLOR). Atende dois públicos:

- **Produtor rural** (com conta): cadastra seu CNPJ e seus CARs e acompanha cada imóvel em um painel.
- **Comprador** (sem conta): frigorífico, trading, cooperativa ou varejista que consulta o CNPJ de um
  fornecedor e vê um status resumido (**Gold**, **Silver**, **Bronze** ou **Sem dados**).

---

## O problema

O mercado de commodities agropecuárias (soja, carne, café, cacau, madeira...) exige cada vez mais
comprovação de que a produção **não vem de áreas desmatadas ou embargadas**. Compromissos como a
Moratória da Soja, os TACs da Carne, as regras de crédito rural e regulações de importação como a
EUDR (União Europeia) transformaram a origem socioambiental em condição para vender.

As informações necessárias para essa verificação **existem e são públicas**, mas estão espalhadas,
são técnicas e difíceis de cruzar:

- alertas de desmatamento validados (MapBiomas Alerta, API GraphQL com autenticação);
- embargos do IBAMA, do ICMBio e de órgãos estaduais, cada um com seu formato;
- o CAR (Cadastro Ambiental Rural), que liga um polígono a um imóvel, mas não diretamente a um CNPJ;
- bases abertas enormes (p. ex. o DOF do IBAMA, um ZIP de ~4,6 GB com um CSV por ano e UF).

## As dores

### Do produtor

- **Não sabe como é visto pelo mercado.** Descobre um alerta ou embargo só quando a venda ou o
  crédito é bloqueado.
- **Não tem os dados reunidos.** Precisaria consultar várias plataformas, uma por imóvel, e
  interpretar mapas e processos técnicos.
- **Não consegue agir a tempo.** Sem saber quais alertas cruzam seu imóvel, quando foram detectados
  e qual área afetam, não consegue contestar, regularizar ou explicar.
- **Não tem como provar uma situação limpa.** Mesmo sem problemas, não tem um jeito simples de
  mostrar isso ao comprador.

### Do comprador

- **Due diligence cara e manual.** Verificar cada fornecedor exige analistas, ferramentas GIS e
  acesso a várias bases.
- **Risco jurídico e de reputação.** Comprar de uma área embargada ou desmatada pode gerar multas,
  perda de mercado e danos à marca.
- **Informação pouco confiável.** Fontes externas caem ou ficam incompletas, e um "zero" pode
  significar "sem problemas" ou "não consegui consultar".
- **Precisa de uma resposta rápida.** Antes de fechar uma compra, quer saber em segundos se o
  fornecedor apresenta risco, sem precisar criar conta nem pedir dados ao produtor.

## A solução que propomos

Uma plataforma que **organiza por imóvel e por CNPJ** os dados ambientais que já são públicos e os
apresenta de forma clara para cada público:

1. **Painel do produtor** — cadastro curto (email, CNPJ e senha); depois o produtor adiciona seus
   CARs. Cada CAR aparece em um cartão com:
   - o polígono do imóvel no mapa;
   - o número de alertas de desmatamento que cruzam o imóvel;
   - o número de embargos (IBAMA, ICMBio, órgãos estaduais), sem duplicados;
   - um **"Ver detalhes"** com os **indicadores do CAR** separados em *Riscos abertos* e *Contexto*
     (ver [Indicadores do CAR](#indicadores-do-car)), cada alerta (código, data, área dentro do CAR,
     situação legal, embargos associados) e cada embargo (órgão, processo, área, data).
2. **Consulta pública por CNPJ** (`specs/002-cnpj-score-search/`) — o comprador digita um CNPJ, sem
   cadastro, e vê uma ficha resumida:
   - **Bronze**: algum imóvel com risco grave em aberto — embargo vigente, alerta em terra indígena
     ou UC de proteção integral, desmatamento após 2020 em reserva legal/APP (≥ 1 % do imóvel) ou
     corte seletivo desordenado/mineração no DETER nos últimos 24 meses;
   - **Silver**: alertas em aberto sem gravidade alta, degradação recente ou dados parciais;
   - **Gold**: nenhum risco em aberto (alertas já autorizadas, com embargo levantado ou suspensas
     não penalizam);
   - **Sem dados**: CNPJ não cadastrado, sem imóveis informados ou dados indisponíveis.

   O nível do CNPJ é o do **imóvel em pior situação**, com os motivos e o sinal **"Atenção EUDR"**
   (desmatamento após 2020, mesmo autorizado). As regras estão em `specs/006-nivel-regras/` e são
   explicadas ao produtor na página **"Entenda o nível"** do painel.
3. **Transparência para os dois lados** — o produtor vê no seu painel exatamente o mesmo status
   que o comprador vê, para saber como é percebido e corrigir o que falta.
4. **Início como resumo do CNPJ** (`specs/005-dashboard-init/`) — status do CNPJ, três números
   (CARs, alertas abertas, embargos vigentes) e um relatório do CNPJ. Por enquanto o relatório é
   um **exemplo escrito à mão**; a geração automática por um agente está em desenvolvimento.

### Princípios da solução

- **Privacidade por agregação:** o comprador vê só dados agregados por CNPJ (nível, score,
  contagens, datas). Códigos de CAR, polígonos e dados da conta continuam privados.
- **Honestidade nos dados:** "0" significa dado confirmado; quando a fonte não responde, a
  plataforma mostra "dados indisponíveis" ou os últimos dados salvos, marcados como desatualizados.
  Nunca um zero falso.
- **Fidelidade à fonte:** polígonos, alertas e embargos aparecem como a fonte os entrega. Todo dado
  derivado indica em que se baseia e a data dos dados usados.
- **Credenciais só no servidor:** o navegador nunca chama o MapBiomas diretamente.

As regras completas estão na constituição do projeto: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

---

## Estrutura do repositório

| Caminho | Conteúdo |
| --- | --- |
| `backend/` | API em Python 3.12 (FastAPI + SQLModel/SQLite), intermediária para MapBiomas, INPE e IBAMA |
| `frontend/` | SPA em TypeScript (React + Vite + Leaflet): landing em `/`, consulta em `/consulta`, painel em `/painel` |
| `frontend/design-dashboard.md` | Notas e limites do redesign do início do painel (preview em `/preview/painel`, só em dev) |
| `docs/arquitetura.md` | **Documentação técnica**: endpoints, tabelas, regras, fontes externas, testes e operação |
| `docs/proposta-regras-nivel-e-agente.md` | Regra de nível (implementada na 006) e proposta do agente de resumos |
| `specs/001-producer-car-dashboard/` | Spec, plano, contrato (`contracts/openapi.yaml`) e tarefas do painel do produtor |
| `specs/002-cnpj-score-search/` | Spec, plano e tarefas da consulta pública por CNPJ |
| `specs/003-car-indicators/` | Spec, plano e tarefas dos indicadores socioambientais do CAR |
| `specs/005-dashboard-init/` | Spec, plano, contrato e tarefas do Início como resumo do CNPJ |
| `data/cars_ejemplo/` | Respostas reais do MapBiomas para CARs de vários estados (**local, não versionado**) |
| `mapbiomas_api.py`, `dof_ibama.py` | Scripts de exploração das fontes (não são usados pela aplicação) |
| `SCHEMA.md`, `schema.json` | Documentação do schema GraphQL do MapBiomas Alerta |

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
# MOCK_REPORTS_DIR=backend/data/mock_reports         (relatórios de exemplo por CNPJ, fora do git)
```

INPE e IBAMA são fontes públicas: não precisam de credenciais.

As credenciais do MapBiomas são usadas só no backend; nunca chegam ao navegador.

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

Testes sem rede: MapBiomas e INPE simulados com `respx`, SINAFLOR com um CSV de amostra.

Validação manual de ponta a ponta: [`001`](specs/001-producer-car-dashboard/quickstart.md),
[`002`](specs/002-cnpj-score-search/quickstart.md) e [`003`](specs/003-car-indicators/quickstart.md).
Detalhes técnicos (endpoints, tabelas, fontes, testes): [`docs/arquitetura.md`](docs/arquitetura.md).

## Consulta pública por CNPJ

- **Telas**: `/consulta` e `/consulta/:cnpj` (link compartilhável), sem login. Acesso pela aba
  "Consultar CNPJ" da barra superior, pelo botão "É comprador? Consulte o status do seu produtor" da
  página inicial e, para produtores logados, pela barra lateral do painel (`/painel/consulta`).
- **API**: `GET /api/public/cnpj/{cnpj}` (com ou sem máscara). Responde 200 também para CNPJ não
  cadastrado (`Sem dados`), 422 para CNPJ inválido e 429 com `Retry-After` ao passar do limite.
  Contrato: [`specs/002-cnpj-score-search/contracts/openapi.yaml`](specs/002-cnpj-score-search/contracts/openapi.yaml).
- **O que mostra**: nível (Gold / Silver / Bronze / Sem dados), estado do score ("Score em cálculo"
  enquanto o método não existe), número de propriedades e data dos dados. **Nunca** códigos de CAR,
  mapas ou dados da conta.
- **Regra provisória do nível**: Sem dados (não cadastrado, sem CARs ou sem dados) → Bronze (≥1
  embargo) → Silver (alertas, ou dados parciais) → Gold. Um CAR sem registro no MapBiomas conta como
  dado parcial e impede o Gold. Detalhes: [`data-model.md`](specs/002-cnpj-score-search/data-model.md#status).
- **Limitação conhecida**: o limite de consultas fica na memória do processo; vale para um único
  processo do backend. Com vários workers ou réplicas, mover o contador para um armazenamento compartilhado.

## Indicadores do CAR

O cartão de cada CAR em "Meus CARs" fica enxuto (mapa, alertas e embargos). Os indicadores aparecem
no **"Ver detalhes"** do CAR, em dois blocos (spec:
[`specs/003-car-indicators`](specs/003-car-indicators/spec.md)):

- **Riscos abertos**: alertas por situação legal (embargo vigente, com fiscalização, sem autorização
  registrada), desmatamento pós-2020 (corte EUDR), alertas abertas em reserva legal e APP, embargos
  vigentes, sobreposição com terra indígena ou UC de proteção integral.
- **Contexto**: alertas superadas (autorizadas, embargo levantado, suspensas judicialmente), embargos
  levantados, UC de uso sustentável, % de vegetação nativa remanescente (INPE PRODES), degradação e
  corte seletivo (INPE DETER, só bioma Amazônia), focos de calor em 12 meses (INPE Queimadas) e manejo
  florestal autorizado (IBAMA SINAFLOR, só Amazônia Legal).

Cada indicador distingue **valor** (inclusive 0), **Indisponível** (a fonte não respondeu e não há
cache) e **Não se aplica**. Uma alerta sem autorização, fiscalização ou embargo aparece como
"Sem autorização registrada", nunca como "ilegal". Os indicadores ficam em cache por 24 h e cada
fonte falha de forma independente. **Ainda não alteram o nível Gold/Silver/Bronze.**

O SINAFLOR é um CSV diário de ~90 MB do IBAMA, resumido por CAR numa tabela local. Rodar uma vez por
dia (ex.: cron); até a primeira execução o indicador aparece como "Indisponível":

```bash
cd backend && uv run python -m app.sources.sinaflor
```

Limitações: reserva legal, APP e UCs vêm calculadas pelo MapBiomas sobre a área da alerta (limitadas à
área dentro do CAR); o PRODES não registra regeneração; o volume do SINAFLOR é o da autorização, que
pode abranger vários CARs.

## Comportamento quando o MapBiomas falha

- Timeout de 20 s por consulta. Os dados ficam em cache por 24 h por CAR (botão "Atualizar" para forçar).
- Se o MapBiomas não responde: aparece a última consulta marcada como "desatualizado", ou
  "dados indisponíveis" + "Tentar novamente" se nunca foi consultado. Cada cartão é independente.
- O cadastro (email, CNPJ e senha) não depende do MapBiomas. Os CARs são adicionados depois no
  painel; para isso o MapBiomas é consultado e, se não responder, pede-se para tentar mais tarde.
- Um CAR que o MapBiomas não tem registrado (sem alertas) é aceito e marcado como tal.
