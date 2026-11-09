# Quickstart: validar los embargos del IBAMA (feature 007)

## Automático (sin red)

```bash
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm run build && npm test
```

Los tests cubren: nivel Gold/Bronze con el IBAMA, umbral de 0,1 ha, deduplicación, IBAMA caído (sigue
"dados parciais"), caché stale, MapBiomas ok (sin consultar el IBAMA), respuesta truncada y que nunca se
piden ni aparecen datos personales del embargado.

## Manual, con datos reales

1. Levantar backend y frontend (ver "Comandos" en `AGENTS.md`) y entrar con la cuenta de prueba.
2. En "Meus CARs", pulsar **Atualizar** en AM-1303304-4B3B1D8060024401A46135766447CBA8 (o usar
   `GET /api/cars/<car>/detail?refresh=true`).
3. Esperado (mientras MapBiomas siga con el error de `pointInformation`):
   - El nivel deja de mostrar "Parte dos dados não pôde ser verificada"; sin otros motivos → **Gold**.
   - En el detalle, "Embargos do imóvel" dice "Nenhum embargo" con la fuente **IBAMA – áreas
     embargadas**, la fecha de consulta y la ayuda (cruce geográfico, solo IBAMA, sin embargos
     levantados).
4. Repetir con PE-2600500-… y RO-1100205-… (mismo resultado esperado).
5. PA-1505031-… sigue usando MapBiomas (tiene alertas): fuente "MapBiomas Alerta", nivel sin cambios.
6. Abrir la ficha pública del CNPJ (`/consulta/<cnpj>`): el nivel coincide con el del Início y no hay
   listas de embargos.
7. Página "Entenda o nível": menciona el respaldo del IBAMA y el umbral de 0,1 ha.
