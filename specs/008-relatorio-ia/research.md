# Research: Relatório do CNPJ explicado pela IA (feature 008)

## R1. De dónde salen los datos (sin cálculos nuevos)

- **Decision**: reutilizar `cnpj_report.car_inputs(db, client, codes)`, que ya devuelve `(CarDetail,
  CarIndicators)` por CAR (lo mismo que alimenta el nivel), y aplicar `level_rules.car_level` /
  `cnpj_level` (funciones puras) para nivel y motivos. Se elimina la segunda carga que hoy hace
  `_car_data`.
- **Rationale**: principio IV (una sola fuente de las reglas) y menos trabajo: hoy `get_report` carga los
  datos dos veces (`cnpj_status` + `_car_data`).
- **Alternatives**: llamar a `cnpj_status` y luego recargar por CAR (actual): duplicado.

## R2. Forma de los "datos del relatório" (lo único que ve la IA)

- **Decision**: función pura `build_report_facts(cars, cnpj_status, today) -> (facts: dict, aliases)` en
  `app/reports/facts.py`. JSON con claves en portugués para que el modelo las entienda:
  - `cnpj`: `nivel`, `motivos` (código + cantidad de imóveis), `imoveis_por_nivel`, `total_imoveis`,
    `sinal_eudr`, totales ya sumados (`alertas_abertas` n/ha, `alertas_pos_2020` n/ha,
    `embargos_vigentes`, `imoveis_com_embargo`, `imoveis_com_alertas_abertas`, `alertas_superadas` n/ha,
    `focos_12m`), `data_dos_dados`.
  - `imoveis[]`: `id` ("Imóvel A"), `uf`, `area_ha`, `nivel`, `motivos` (código, n, ha, pct),
    `alertas` (abertas, pós-2020, por situação con n/ha, reserva legal ha, alertas tocando APP, TI ha,
    UC integral ha, años de la primera y la última alerta), `embargos` (`estado`: verificado /
    indisponivel / nao_determinavel; `fonte`: MapBiomas / IBAMA; `vigentes`, `levantados`),
    `contexto` (vegetação nativa %, desmatado PRODES ha, DETER por clase en 24 meses, focos 12 m, manejo
    SINAFLOR, nombres de UC de uso sustentável), `fontes_indisponiveis`, `sinal_eudr`.
  - Hectáreas redondeadas a 1 decimal y porcentajes a 1 decimal **en los datos**, para que el modelo cite
    exactamente esos valores.
- **Rationale**: el modelo no suma ni calcula (decisión 1); los totales del CNPJ ya vienen hechos. Sin
  geometrías ni listas de alertas (menos tokens, menos errores). Los estados no-valor llegan como texto
  (FR-802).
- **Alternatives**: enviar `CarIndicators` crudo (tiene listas de alertas y campos internos); enviar solo
  códigos de motivo sin números (el texto quedaría vago).

## R3. Seudónimos

- **Decision**: "Imóvel A"… "Imóvel Z", luego "Imóvel AA"…, en el orden de gravedad (Bronze → Silver →
  Gold → Sem dados) y, dentro del nivel, por código. La correspondencia vive solo en la llamada. El CNPJ no
  se envía. Al volver:
  - en `imoveis[].car_code` va el código completo (el enlace "Ver detalhes" lo necesita);
  - en el texto corrido, "Imóvel A" se reemplaza por el prefijo `UF-MUNICÍPIO` del CAR (ej. `MT-5102504`),
    como en el ejemplo aprobado; si dos CARs comparten prefijo, se usa el código completo.
- **Validación**: regex `Imóvel ([A-Z]{1,2})\b` sobre todos los textos; un seudónimo desconocido invalida la
  respuesta. Si falta la frase de algún imóvel, se completa con la frase por reglas de ese imóvel (no se
  descarta todo el relatório).
- **Rationale**: principio III; mismo resultado visible para el productor.

## R4. Control de números

- **Decision**: extraer números del texto con `\d+(?:[.,]\d+)*`, normalizar pt-BR (`2.968,4` → 2968.4;
  `376,1` → 376.1; fechas `31/12/2020` se separan en 31, 12, 2020) y exigir que cada uno esté en el
  conjunto de números de los datos (todos los valores numéricos del JSON, comparados con 1 decimal) o en
  las constantes permitidas de las reglas: 2020, 31, 12, 24, 1 y 0,1.
- **Rationale**: FR-805; atrapa cifras inventadas o sumas no pedidas. Números escritos en palabras
  ("dois") no se controlan; riesgo aceptado.
- **Alternatives**: pedir citas estructuradas al modelo (más complejo); no controlar (riesgo de cifras
  falsas).

## R5. Llamada al modelo

- **Decision**: misma API (`LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL`), `temperature` 0.2,
  `response_format` JSON, timeout = `settings.llm_timeout_s` (hoy fijo en 12 s). Una sola llamada por
  CNPJ; un reintento si la validación falla. La clave se lee de `settings` (ya carga el `.env`).
- **Límite de imóveis**: hasta 40 por pedido (unos pocos miles de tokens). Con más, se envían los 40 más
  graves y los totales del CNPJ; los demás reciben la frase por reglas.
- **Prompt**: nuevo, en `app/reports/prompt.py`, basado en `docs/proposta-agente.md`: rol "assistente do
  Elo Rural que explica ao produtor"; objetivo (consolidar y explicar); glosario de los códigos de motivo;
  reglas de FR-804; formato JSON de salida. Constante `PROMPT_VERSION` para invalidar la caché al cambiar
  el prompt.

## R6. Caché

- **Decision**: diccionario en memoria del proceso, clave = SHA-256 del JSON canónico de los datos +
  `PROMPT_VERSION` + modelo. Guarda el relatório final (ya con códigos reales). Respuestas de la IA: hasta
  que cambien los datos. Fallback por reglas: 15 min (para reintentar la IA si estaba caída sin esperar a
  que cambien los datos). Máximo 256 entradas (se descartan las más antiguas).
- **Rationale**: FR-809 sin tabla nueva (principio V). Los datos cambian como mucho cada 24 h por CAR (TTL
  de la caché de indicadores) o con "Atualizar".
- **Alternatives**: tabla `report_snapshot` (persistiría entre reinicios, pero es una tabla nueva sin
  requisito que la exija).

## R7. Origen y modo demostración

- **Decision**: `CnpjReport.origem` gana `"regras"`. El texto por reglas existente sale con `"regras"` y se
  le quitan "Recomenda-se … nota ESG" (consejo) y la línea fija de SINAFLOR. El ejemplo escrito a mano solo
  se usa con `REPORT_DEMO_MODE=true` (`settings.report_demo_mode`, por defecto `false`).
- **Frontend**: con `origem="agente"`, un aviso destacado **"Gerado por IA"** arriba del relatório (antes del
  título de la sección) con la nota "o nível é calculado por regras; dados de MapBiomas, INPE e IBAMA";
  con `"regras"`, "Gerado automaticamente por regras (sem IA)"; con `"exemplo"`, "Exemplo de demonstração".

## R8. Tests sin red

- **Decision**: fixture autouse en `conftest.py` que deja `settings.llm_api_key = ""` (así ningún test usa
  la clave real del `.env`), y un `FakeLlm` montado con `respx` en `settings.llm_api_url` que los tests
  encienden: guarda los cuerpos recibidos (para verificar que no hay códigos de CAR ni CNPJ) y devuelve la
  respuesta configurada (válida, con número inventado, con "Imóvel Z", con 4 riscos, error, timeout).
