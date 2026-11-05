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
- Os testes nunca devem depender da rede nem do MapBiomas real; se um teste precisar de dados,
  use as fixtures em `backend/tests/fixtures/`.
