# Quickstart: validar la consulta pública por CNPJ

Requisitos y arranque: igual que [`../001-producer-car-dashboard/quickstart.md`](../001-producer-car-dashboard/quickstart.md) (backend en :8000, frontend en :5173). Contrato: [`contracts/openapi.yaml`](contracts/openapi.yaml). Reglas de nivel: [`data-model.md`](data-model.md#status).

## 1. Tests automáticos

```bash
cd backend && uv run ruff check . && uv run pytest     # incluye compute_status, aggregate_cars, endpoint público, rate limit
cd frontend && npm run build && npm test               # validador CNPJ, StatusBadge, página /consulta
```

Lo que deben cubrir, como mínimo:

| Caso | Esperado |
|---|---|
| Tabla de reglas de `data-model.md` (6 filas + datos parciales + CAR `not_in_mapbiomas`) | Nivel y motivo exactos |
| CNPJ inválido | 422, `field=cnpj` |
| CNPJ con máscara y sin máscara | Respuestas idénticas |
| Dos cuentas con el mismo CNPJ y un CAR compartido | `cars_count` sin duplicar |
| MapBiomas simulado caído, con caché | 200, `stale=true` |
| MapBiomas simulado caído, sin caché | 200, `sem_dados` / `data_unavailable` |
| 31 búsquedas desde la misma IP en una hora | La 31ª responde 429 con `Retry-After` |
| JSON público, recorrido completo | Sin claves `car_code`, `geometry`, `email`, `id` |
| `/api/dashboard` vs `/api/public/cnpj/{cnpj}` | `cnpj_status` y `cnpj_score` idénticos |

## 2. Validación manual (sin sesión)

1. Abre http://localhost:5173 en una ventana privada. La landing explica los dos usos (productor / comprador), **no** tiene buscador y muestra el botón "É comprador? Consulte o status do seu produtor". Pulsarlo lleva a `/consulta`. La pestaña "Consultar CNPJ" de la barra superior lleva al mismo sitio.
2. En `/consulta`, busca `04.654.691/0001-06` (productor de prueba con los CARs de ejemplo). Navega a `/consulta/04654691000106` y ves el nivel, "Score em cálculo", el número de propiedades y la fecha de los datos, sin códigos de CAR ni mapa.
3. Busca `11.222.333/0001-81` (válido, no registrado): "Sem dados", con el motivo "CNPJ não cadastrado na plataforma".
4. Busca `11.222.333/0001-00` (dígitos verificadores incorrectos): el error aparece al instante y no se hace ninguna petición (compruébalo en la pestaña Red).
5. Copia la URL de la ficha y ábrela en otra ventana: la misma ficha.

## 3. Validación manual (productor)

1. Inicia sesión como el productor de `04.654.691/0001-06`. En "Início" aparece el mismo nivel y score que en el paso 2.2.
2. En la barra lateral, "Consultar CNPJ" abre la búsqueda dentro del panel. Busca `11.222.333/0001-81`: la ficha es la misma que sin sesión, sin datos adicionales.
3. Quita un CAR y vuelve a consultar la ficha pública: refleja el cambio.

## 4. Puntos a confirmar con el usuario

**Resultado real (2026-11-05, T043)**: `04.654.691/0001-06` con su CAR de ejemplo (`PE-2607505-…`, 3 alertas y 0 embargos) da **Silver**, `partial=false` y "Score em cálculo". `11.222.333/0001-81` da Sem dados / não cadastrado; `11.222.333/0001-00` da 422. Las rutas `/`, `/consulta`, `/consulta/:cnpj` y `/painel/consulta` responden.

- Corrección de la nota original: el CAR de ejemplo `PE-2607505-…` **sí tiene 3 alertas**, así que da Silver por las alertas, no por datos parciales. Para ver un Gold hace falta un CAR registrado en MapBiomas sin alertas ni embargos. Un CAR `not_in_mapbiomas` da Silver con `partial=true` (research R5, confirmado).
- Mientras MapBiomas devuelva 502, un CNPJ sin caché aparecerá como "Sem dados".
