# Data Model: Relatório do CNPJ explicado pela IA (feature 008)

Sin tablas nuevas. La caché vive en memoria.

## Datos del relatório (`facts`, enviado a la IA)

```json
{
  "cnpj": {
    "nivel": "bronze",
    "motivos": [{"codigo": "EMBARGO_VIGENTE", "imoveis": 1}],
    "imoveis_por_nivel": {"gold": 4, "silver": 1, "bronze": 2, "sem_dados": 0},
    "total_imoveis": 7,
    "sinal_eudr": true,
    "alertas_abertas": {"n": 36, "ha": 376.1},
    "alertas_pos_2020": {"n": 31, "ha": 349.5},
    "alertas_superadas": {"n": 2, "ha": 48.5},
    "embargos_vigentes": 7,
    "imoveis_com_embargo": 2,
    "imoveis_com_alertas_abertas": 5,
    "focos_12m": 9,
    "data_dos_dados": "2026-11-08"
  },
  "imoveis": [
    {
      "id": "Imóvel A",
      "uf": "MT",
      "area_ha": 1375.6,
      "nivel": "bronze",
      "motivos": [{"codigo": "EMBARGO_VIGENTE", "n": 5, "ha": null, "pct": null}],
      "alertas": {
        "abertas": {"n": 5, "ha": 94.0},
        "pos_2020": {"n": 5, "ha": 94.0},
        "por_situacao": {"pendente": {"n": 5, "ha": 94.0}},
        "reserva_legal_ha": 71.8, "alertas_app": 0, "terra_indigena_ha": 0, "uc_integral_ha": 0,
        "primeiro_ano": 2023, "ultimo_ano": 2026
      },
      "embargos": {"estado": "verificado", "fonte": "MapBiomas", "vigentes": 5, "levantados": 0},
      "contexto": {
        "vegetacao_nativa_pct": 64.3, "desmatado_prodes_ha": 2283.7,
        "deter_24m": {"DEGRADACAO": {"n": 1, "ha": 3.2}},
        "focos_12m": 0,
        "manejo_sinaflor": {"autorizacoes": 0, "vigentes": 0, "volume_m3": 0},
        "uc_uso_sustentavel": ["APA ..."]
      },
      "fontes_indisponiveis": [],
      "sinal_eudr": true
    }
  ]
}
```

Reglas:
- Sin códigos de CAR, sin CNPJ, sin geometrías, sin listas de alertas, sin datos personales.
- Valor desconocido → `null` + estado textual (`"indisponivel"`, `"nao_determinavel"`, `"nao_se_aplica"`);
  nunca 0.
- `ha` y `%` redondeados a 1 decimal.
- Orden de `imoveis`: Bronze → Silver → Gold → Sem dados; máximo 40.

## Correspondencia de seudónimos (solo servidor, por llamada)

`{"Imóvel A": "MT-5102504-FB5206A8AF224FDC8B7E1D19...", ...}` + prefijo de texto (`MT-5102504`) por CAR.

## CnpjReport (existente, cambio de enum)

| Campo | Cambio |
|---|---|
| `origem` | `exemplo` \| `agente` \| **`regras`** (nuevo) |

Resto sin cambios (`titulo`, `riscos` ≤ 3, `contexto` ≤ 3, `ressalvas`, `imoveis[{car_code, resumo}]`,
`nivel`, `data_dos_dados`, `gerado_em`).

## Flujo de `get_report`

```
REPORT_DEMO_MODE y existe exemplo  → exemplo (origem=exemplo)
CNPJ sin imóveis / no cadastrado    → indisponivel
facts + aliases = build_report_facts(...)
cache[hash(facts, PROMPT_VERSION, modelo)] → devolver
sin clave LLM                       → regras (cache 15 min)
LLM → validar (formato, recorte 3/3, vocabulário, números, seudónimos)
   ok      → reemplazar seudónimos, nivel = regras, origem=agente (cache hasta cambio de datos)
   falla   → 1 reintento → si falla: regras (cache 15 min)
```

## Configuración nueva

- `REPORT_DEMO_MODE` (bool, por defecto `false`).
- `LLM_TIMEOUT_S` pasa a usarse de verdad (hoy está fijo en 12 s).
