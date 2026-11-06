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
- O redesign do início pode ser visto sem backend em `http://localhost:5173/preview/painel`
  (dados fictícios, só em desenvolvimento).
- Documentação técnica: [`docs/arquitetura.md`](docs/arquitetura.md). Ao mudar endpoints, tabelas,
  fontes ou regras, atualize esse arquivo junto com a spec da feature.
