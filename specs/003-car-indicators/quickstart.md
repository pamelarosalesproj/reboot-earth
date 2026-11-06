# Quickstart: validar los indicadores del CAR

Arranque como en [`../001-producer-car-dashboard/quickstart.md`](../001-producer-car-dashboard/quickstart.md). Contrato: [`contracts/openapi.yaml`](contracts/openapi.yaml). Reglas: [`data-model.md`](data-model.md).

## 1. Tests automáticos (sin red)

```bash
cd backend && uv sync && uv run ruff check . && uv run pytest
cd frontend && npm run build && npm test
```

Deben cubrir:
- `classify_alert`: las 6 situaciones y el orden de prioridad.
- PRODES: unión de capas superpuestas, sin contar dos veces.
- DETER: "não se aplica" fuera del bioma Amazonía.
- Focos de calor: dentro y fuera del polígono, y dentro y fuera de la ventana de 12 meses.
- Sincronización de SINAFLOR con un CSV de prueba (filas duplicadas y `,` decimal).
- Endpoint: el CAR de otro productor da 404; con una fuente caída, el resto sigue visible.
- Frontend: los tres estados (valor, indisponível, não se aplica) y ninguna aparición de "ilegal".

## 2. Sincronizar SINAFLOR (una vez al día)

```bash
cd backend && uv run python -m app.sources.sinaflor   # descarga unos 90 MB en streaming
```

Esperado: "N CARs con autorizaciones" (3.434 CARs el 2026-11-06, en unos 5 s). Una autorización puede abarcar varios CARs, en cuyo caso se repite el mismo volumen en cada uno: el volumen es el de la autorización, no un reparto por CAR.

## 3. Validación manual con los 3 CARs de referencia (SC-301)

Registra un productor y añade los tres CARs. En "Meus CARs", cada tarjeta debe mostrar (±1 %):

| | PE-2607505 | MT-5102504 | TO-1712504 |
|---|---|---|---|
| Embargo vigente | 0 | 3 · 27,5 ha | 0 |
| Sem autorização registrada | 3 · 74,5 ha | 2 · 66,6 ha | 23 · 99,1 ha |
| Desmatamento pós-2020 | 74,5 ha | 88,1 ha | 78,4 ha |
| Reserva legal (abertas) | 27,1 ha | 71,8 ha | 5,4 ha |
| Alertas que tocam APP | 2 | 0 | 3 |
| Embargos vigentes | 0 | 5 | 0 |
| UC de uso sustentável | 0 | 0 | 99,1 ha · APA Ilha do Bananal/Cantão |
| Vegetação nativa | 2,1 % | 67,1 % | 64,3 % |
| DETER | Não se aplica | Não se aplica (el polígono está en Cerrado/Pantanal) | Não se aplica |
| Focos (12 m) | 1 | 1 | 4 |
| Manejo SINAFLOR | Não se aplica | 0 | 0 |

Los valores pueden cambiar si las fuentes publican datos nuevos. Los de esta tabla son del 2026-11-06.
