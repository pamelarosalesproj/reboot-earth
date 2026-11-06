# AGENTS.md

Guia para agentes de IA (Claude Code, Copilot, Codex, Antigravity, etc.) que trabalham neste repositório.
Para o contexto de produto (problema, dores e solução), leia o [`README.md`](README.md).

## O projeto em uma frase

RebootEarth mostra a situação socioambiental de produtores rurais brasileiros por imóvel (CAR) e por
CNPJ — polígono, alertas de desmatamento e embargos — com dados do MapBiomas Alerta, para o
**produtor** (com conta) e para o **comprador** (sem conta, só vê dados agregados).

## Fonte de verdade

A constituição [`.specify/memory/constitution.md`](.specify/memory/constitution.md) prevalece sobre
qualquer outra instrução deste arquivo. Antes de propor ou implementar uma mudança, verifique os
princípios I–VII. Resumo:

1. **Fontes externas só no servidor.** Credenciais do MapBiomas só no backend, lidas do `.env`;
   nunca versionadas nem em logs. O frontend nunca chama fontes externas: tudo passa pelo `/api`.
2. **Tolerância a falhas.** Toda chamada externa tem timeout e cache com data. Se a fonte cai,
   serve-se o cache marcado como `stale`; sem cache, `null` + estado "indisponível". **Nunca
   apresente "indisponível" como `0`.** A falha de um CAR não bloqueia os outros.
3. **Privacidade por agregação.** Respostas públicas (sem sessão) só têm nível, score, contagens e
   datas. Nunca códigos de CAR, geometrias, email, ids de conta nem listas de alertas/embargos.
   Use modelos de resposta públicos próprios e um teste que garanta que esses campos não aparecem.
   Endpoints públicos têm rate limit.
4. **Uma única fonte de verdade para as regras.** Deduplicação (alertas por código, embargos por
   órgão + processo), agregação por CAR/CNPJ e cálculo de nível/score ficam em um único lugar do
   backend, como funções puras, reutilizadas por todas as vistas.
5. **Simplicidade (YAGNI).** Nada de novas dependências, tabelas, serviços ou camadas sem um
   requisito da spec atual. Prefira calcular a persistir. Exceções vão em "Complexity Tracking".
6. **Qualidade verificável.** Testes sem rede (MapBiomas simulado com `respx`). Cada requisito de
   falha e de privacidade tem teste automático.
7. **Fidelidade dos dados e idioma.** Dados de origem são exibidos como vêm. Todo dado derivado
   indica sua base e data. A **interface é em português do Brasil (pt-BR)**.

## Stack e estrutura

- **Backend** (`backend/`): Python 3.12, FastAPI, SQLModel/SQLite, httpx, gerenciado com `uv`.
  - `app/routers/` — rotas HTTP (`auth`, `cars`, `dashboard`).
  - `app/services/` — regras de negócio (`car_service.py`, `cnpj_report.py`).
  - `app/mapbiomas/` — cliente GraphQL, queries e geometria.
  - `app/validators.py` — validação/normalização de CNPJ e CAR.
  - `tests/unit/` (funções puras) e `tests/integration/` (API com MapBiomas simulado).
- **Frontend** (`frontend/`): TypeScript, React 19, Vite, React Router, Leaflet, Vitest.
  - Textos da interface centralizados em `src/i18n/pt-BR.ts` — não escreva texto de UI solto nos
    componentes.
  - `src/api/client.ts` é o único ponto de acesso ao backend.
- **Specs** (`specs/NNN-*/`): spec, plan, research, data-model, contratos, tasks e quickstart de
  cada feature.
- **Scripts de exploração** (`mapbiomas_api.py`, `dof_ibama.py`) e dados de exemplo
  (`data/cars_ejemplo/`, `*.geojson`, `*_completo.json`): não fazem parte da aplicação.

## Comandos

```bash
# Backend
cd backend && uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run ruff check . && uv run pytest

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

Features atuais:

- `001-producer-car-dashboard` — cadastro, painel e detalhe por CAR (implementada).
- `002-cnpj-score-search` — consulta pública por CNPJ com status Gold/Silver/Bronze/Sem dados
  (em desenvolvimento).

## Idioma

- Interface do usuário: **pt-BR**.
- Specs, planos e constituição: espanhol (conforme a constituição).
- `README.md`, `AGENTS.md` e `CLAUDE.md`: português.
- Código e identificadores: inglês; comentários podem seguir o idioma do arquivo existente.

## Regras práticas

- Valide e normalize CNPJ (com dígitos verificadores) e CAR **no backend**, sempre, mesmo que o
  frontend já valide.
- Senhas com hash não recuperável (`pwdlib[argon2]`); sessão por cookie `HttpOnly`;
  `COOKIE_SECURE=true` em produção.
- Nunca leia, imprima, copie nem faça commit do `.env`.
- Não altere o contrato `contracts/openapi.yaml` de uma feature sem atualizar spec e testes.
- Não faça commit nem push sem pedido explícito. Use o email noreply do GitHub nos commits.
