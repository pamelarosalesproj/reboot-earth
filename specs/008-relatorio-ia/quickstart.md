# Quickstart: validar el relatório explicado por la IA (feature 008)

## Automático (sin red)

```bash
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm run build && npm test
```

Cubre: datos del relatório (sin códigos ni CNPJ, estados no-valor), seudónimos de ida y vuelta, control de
números, recorte a 3 riesgos/contexto, vocabulario, reintento y fallback (sin clave, error, timeout, número
inventado, "Imóvel Z"), caché (una llamada para dos visitas), modo demostración y el aviso "Gerado por IA".

## Manual, con datos reales

1. Con `LLM_API_KEY` configurada en el `.env` y `REPORT_DEMO_MODE` sin definir, levantar backend y
   frontend y entrar con la cuenta de prueba.
2. Abrir el Início:
   - arriba del relatório aparece **"Gerado por IA"**;
   - título, hasta 3 riesgos, hasta 3 datos de contexto, una frase por cada uno de los 7 imóveis y
     ressalvas;
   - los números citados coinciden con los del detalle de cada CAR;
   - los códigos de CAR que se ven son los reales.
3. Recargar la página: el texto es el mismo y aparece al instante.
4. Pulsar "Atualizar" en un CAR y volver al Início: el relatório se genera de nuevo.
5. Quitar `LLM_API_KEY` y reiniciar: el relatório aparece con el aviso "Gerado automaticamente por regras".
6. Con `REPORT_DEMO_MODE=true`: se muestra el ejemplo escrito a mano (si existe para el CNPJ).
