# AGENTS.md

Guia para agentes de IA (Claude Code, Copilot, Codex, Antigravity, etc.) que trabalham neste repositório.
Para o contexto de produto (problema, dores e solução), leia o [`README.md`](README.md). Para os
detalhes técnicos (endpoints, tabelas, regras, fontes externas e as armadilhas delas, testes e
operação), leia [`docs/arquitetura.md`](docs/arquitetura.md).

## O projeto em uma frase

RebootEarth mostra a situação socioambiental de produtores rurais brasileiros por imóvel (CAR) e por
CNPJ — polígono, alertas de desmatamento por situação legal, embargos e indicadores (vegetação
nativa, DETER, focos de calor, manejo florestal) — com dados do MapBiomas Alerta, do INPE e do IBAMA,
para o **produtor** (com conta) e para o **comprador** (sem conta, só vê dados agregados).

## Fonte de verdade

A constituição [`.specify/memory/constitution.md`](.specify/memory/constitution.md) prevalece sobre
qualquer outra instrução deste arquivo. Antes de propor ou implementar uma mudança, verifique os
princípios I–VII. Resumo:

1. **Fontes externas só no servidor.** Credenciais do MapBiomas só no backend, lidas do `.env`;
   nunca versionadas nem em logs. O frontend nunca chama fontes externas (MapBiomas, INPE, IBAMA):
   tudo passa pelo `/api`.
2. **Tolerância a falhas.** Toda chamada externa tem timeout e cache com data. Se a fonte cai,
   serve-se o cache marcado como `stale`; sem cache, `null` + estado "indisponível". **Nunca
   apresente "indisponível" como `0`.** A falha de um CAR — ou de uma fonte nos indicadores — não
   bloqueia o resto. Há três estados distintos: valor, "Indisponível" e "Não se aplica".
3. **Privacidade por agregação.** Respostas públicas (sem sessão) só têm nível, score, contagens e
   datas. Nunca códigos de CAR, geometrias, email, ids de conta nem listas de alertas/embargos.
   Use modelos de resposta públicos próprios e um teste que garanta que esses campos não aparecem.
   Endpoints públicos têm rate limit.
4. **Uma única fonte de verdade para as regras.** Deduplicação (alertas por código, embargos por
   órgão + processo), agregação por CAR/CNPJ e cálculo de nível/score ficam em um único lugar do
   backend, como funções puras, reutilizadas por todas as vistas.
5. **Simplicidade (YAGNI).** Nada de novas dependências, tabelas, serviços ou camadas sem um
   requisito da spec atual. Prefira calcular a persistir. Exceções vão em "Complexity Tracking".
6. **Qualidade verificável.** Testes sem rede (MapBiomas e INPE simulados com `respx`, SINAFLOR com
   CSV de amostra). Cada requisito de falha e de privacidade tem teste automático.
7. **Fidelidade dos dados e idioma.** Dados de origem são exibidos como vêm. Todo dado derivado
   indica sua base e data. A **interface é em português do Brasil (pt-BR)**.

## Stack e estrutura

- **Backend** (`backend/`): Python 3.12, FastAPI, SQLModel/SQLite, httpx, shapely, gerenciado com `uv`.
  - `app/routers/` — rotas HTTP (`auth`, `cars`, `dashboard`, `public`).
  - `app/services/` — regras de negócio: `car_service.py` (dados do CAR e cache), `cnpj_report.py`
    (agregação por CNPJ, nível e score), `car_indicators.py` (situação das alertas e indicadores).
  - `app/mapbiomas/` — cliente GraphQL, queries e geometria.
  - `app/sources/` — fontes públicas: `inpe.py` (WFS do TerraBrasilis), `sinaflor.py` (CSV do IBAMA
    e comando de sincronização), `geo.py` (polígonos com shapely).
  - `app/rate_limit.py` — limite das consultas públicas; `app/validators.py` — CNPJ e CAR.
  - `tests/unit/` (funções puras) e `tests/integration/` (API com fontes simuladas).
- **Frontend** (`frontend/`): TypeScript, React 19, Vite, React Router, Leaflet, Vitest.
  - Textos da interface centralizados em `src/i18n/pt-BR.ts` — não escreva texto de UI solto nos
    componentes.
  - `src/api/client.ts` é o único ponto de acesso ao backend.
  - Layouts em `src/layout/` (`AppLayout` para o painel, `AuthLayout` para login/cadastro); CSS por
    página. `src/preview/` + `/preview/painel` são só de desenvolvimento, com dados fictícios
    (ver `frontend/design-dashboard.md`).
- **Specs** (`specs/NNN-*/`): spec, plan, research, data-model, contratos, tasks e quickstart de
  cada feature.
- **Docs** (`docs/`): `arquitetura.md` (técnica) e propostas ainda não implementadas.
- **Scripts de exploração** (`mapbiomas_api.py`, `dof_ibama.py`) e dados de exemplo
  (`data/cars_ejemplo/`, `*.geojson`, `*_completo.json`): não fazem parte da aplicação.
  `data/` contém dados reais de CARs, **não é versionado e nunca deve entrar em commits**.

## Comandos

```bash
# Backend
cd backend && uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run ruff check . && uv run pytest
uv run python -m app.sources.sinaflor     # sincroniza o SINAFLOR (1×/dia; ~90 MB em streaming)

# Frontend
cd frontend && npm install
npm run dev
npm run build && npm test
```

**Antes de considerar uma tarefa concluída**, rode os quatro gates: `uv run ruff check .`,
`uv run pytest`, `npm run build` e `npm test`. Se algum falhar, reporte a saída; não esconda.

## Fluxo de trabalho (Spec Kit)

Cada feature segue: `/speckit-specify` → (`/speckit-clarify`) → `/speckit-plan` → `/speckit-tasks`
→ `/speckit-implement`.

- O "Constitution Check" do `plan.md` avalia os princípios I–VII; uma violação bloqueia as tarefas
  salvo justificativa em "Complexity Tracking".
- Suposições que afetam privacidade ou escopo vão em "Assumptions" e são confirmadas com a pessoa
  responsável antes de implementar.
- Mudanças de escopo pedidas pelo usuário são registradas na spec com data.
- Cada feature tem um `quickstart.md` com validação manual de ponta a ponta.

Features (todas em `main`):

- `001-producer-car-dashboard` — cadastro, painel e detalhe por CAR (implementada).
- `002-cnpj-score-search` — consulta pública por CNPJ com nível Gold/Silver/Bronze/Sem dados e
  regra **provisória** FR-111a (implementada).
- `003-car-indicators` — indicadores do CAR: alertas por situação legal, riscos abertos e contexto,
  com MapBiomas, INPE e SINAFLOR (implementada; **não altera o nível**). Aparecem só no detalhe do
  CAR; o cartão de "Meus CARs" fica enxuto.
- Redesign do frontend (sem spec própria; notas em `frontend/design-dashboard.md`). Os blocos de
  indicadores da 003 ainda usam o estilo anterior.

Pendente de decisão: a nova regra de nível e o agente de resumos em
[`docs/proposta-regras-nivel-e-agente.md`](docs/proposta-regras-nivel-e-agente.md). Mudar a regra de
nível afeta o painel **e** a ficha pública e exige confirmação antes de implementar.

## Idioma

- Interface do usuário: **pt-BR**.
- Specs, planos e constituição: espanhol (conforme a constituição).
- `README.md`, `AGENTS.md`, `CLAUDE.md` e `docs/`: português.
- Código e identificadores: inglês; comentários podem seguir o idioma do arquivo existente.

## Regras práticas

- Valide e normalize CNPJ (com dígitos verificadores) e CAR **no backend**, sempre, mesmo que o
  frontend já valide.
- Senhas com hash não recuperável (`pwdlib[argon2]`); sessão por cookie `HttpOnly`;
  `COOKIE_SECURE=true` em produção.
- Nunca leia, imprima, copie nem faça commit do `.env`.
- Não altere o contrato `contracts/openapi.yaml` de uma feature sem atualizar spec e testes.
- Uma alerta sem autorização, fiscalização nem embargo é **"Sem autorização registrada"**: nunca
  escreva "ilegal" nem "crime" na interface, nos textos gerados ou nos documentos para o usuário.
- Termos técnicos na interface (APP, reserva legal, UCs, EUDR…) levam uma ajuda explicativa
  (componente `Help` em `CarIndicators.tsx`).
- Ao consultar o WFS do INPE, filtre com `INTERSECTS(geom, SRID=4326;<WKT>)` — sem o prefixo `SRID`
  o servidor lê lat/lon, e `bbox` compara caixas. Detalhes em `docs/arquitetura.md`.
- Mudanças de esquema: `create_all` não altera tabelas existentes; crie tabela nova ou escreva uma
  migração.
- Não faça commit nem push sem pedido explícito. Use o email noreply do GitHub nos commits.
  Verifique em qual branch você está antes de commitar: o time cria branches de feature
  (ex.: `004-update-card-info`).
