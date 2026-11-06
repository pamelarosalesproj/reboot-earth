# Quickstart: Nueva regla de nivel

1. Backend y frontend levantados (ver AGENTS.md). Cuenta QA: `qa-003@example.com` / `qa-teste-003`.
2. "Meus CARs": cada CAR muestra su nivel; el detalle lista los motivos con números y, si corresponde, "Atenção EUDR".
3. Início: el nivel del CNPJ es el peor de sus CARs y muestra "Imóveis: N Bronze · N Silver · …".
4. Ficha pública (`/consulta`, sin sesión) con el mismo CNPJ: el mismo nivel, sin códigos de CAR.
5. Menú lateral → "Entenda o nível": criterios (umbral de 1 %, 24 meses del DETER), lo que no penaliza, CNPJ, EUDR, fuentes y glosario.
6. Gates: `uv run ruff check . && uv run pytest`, `npm run build && npm test`.

## Valores de referencia (2026-11-06)

CNPJ 11.444.777/0001-61 (cuenta QA), validado en vivo:

| CAR | Nivel | Motivos |
|---|---|---|
| PE-2607505 | Bronze | RL/APP pós-2020: 3 alertas · 74,46 ha · 28,18 % (≥ 1 %); 3 alertas abiertas |
| MT-5102504 | Bronze | 5 embargos vigentes; RL/APP pós-2020 0,82 % (< 1 %, Silver); 5 alertas abiertas |
| TO-1712504 | Silver | RL/APP pós-2020 0,44 % (< 1 %); 23 alertas abiertas · 99,11 ha |
| **CNPJ** | **Bronze** | 2 Bronze · 1 Silver; Atenção EUDR |
