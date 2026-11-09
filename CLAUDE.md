# CLAUDE.md

As instruções para agentes estão em [`AGENTS.md`](AGENTS.md) e valem integralmente para o Claude Code:

@AGENTS.md

## Específico do Claude Code

- As skills do Spec Kit estão em `.claude/skills/` (`/speckit-specify`, `/speckit-plan`,
  `/speckit-tasks`, `/speckit-implement`, `/speckit-analyze` etc.). Use-as para qualquer feature
  nova em vez de criar specs à mão.
- Antes de editar uma feature, leia `spec.md`, `plan.md` e `tasks.md` dela em `specs/NNN-*/`.
- Para verificar uma mudança na interface, suba backend e frontend (ver "Comandos" no AGENTS.md)
  e confira em `http://localhost:5173`.
- Os testes nunca devem depender da rede nem das fontes reais; se um teste precisar de dados,
  use as fixtures em `backend/tests/fixtures/` e os fakes do `conftest.py`: `mapbiomas_mock`
  (`FakeMapBiomas`: `properties`, `embargoes`, `alert_extra`, `judicial`, `down`) e `inpe`
  (`FakeInpe`: `layers`, `down`).
- Para conferir os indicadores do CAR com dados reais, rode antes o sync do SINAFLOR
  (`uv run python -m app.sources.sinaflor`); sem ele, o manejo florestal aparece "Indisponível".
  Os indicadores ficam em cache 24 h por CAR: use `?refresh=true` para recalcular.
- O Início pode ser visto sem backend em `http://localhost:5173/preview/painel` e o módulo de lotes
  em `/preview/lotes` (dados fictícios, só em desenvolvimento).
- O relatório do CNPJ é um exemplo local em `backend/data/mock_reports/<cnpj>.json` (fora do git).
  Se escrever um novo, use só números que existam nos indicadores do CNPJ e nunca "ilegal"/"crime":
  o backend rejeita o arquivo e mostra "Relatório ainda não disponível".
- Documentação técnica: [`docs/arquitetura.md`](docs/arquitetura.md) e
  [`docs/desenvolvimento.md`](docs/desenvolvimento.md). Ao mudar endpoints, tabelas, fontes ou regras,
  atualize esses arquivos junto com a spec da feature.
- **Ao mudar uma regra de nível** (Gold/Silver/Bronze, motivos, limites, situação das alertas ou o
  respaldo do IBAMA), atualize na mesma mudança
  [`docs/proposta-regras-nivel.md`](docs/proposta-regras-nivel.md), os textos de `t.rules` em
  `frontend/src/i18n/pt-BR.ts` e, se preciso, o resumo do nível no `README.md` (ver "Regras práticas"
  no AGENTS.md).
- O `README.md` é de negócio: não coloque nele referências a specs nem detalhes técnicos; use `docs/`.
