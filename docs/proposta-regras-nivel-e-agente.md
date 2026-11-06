# Proposta: regras de nível (Gold / Silver / Bronze) e agente de resumos

**Status**: proposta para discussão; não implementada · **Data**: 2026-11-06

**Contexto**: indicadores por CAR da feature [`003-car-indicators`](../specs/003-car-indicators/spec.md).
Esta proposta substituiria a regra provisória de nível da feature 002 (FR-111a), inclusive na ficha
pública, e por isso precisa de confirmação antes de virar a feature 004.

## Princípio: o nível é decidido por regras fixas, e o agente só redige

O modelo de linguagem **não escolhe** Gold, Silver ou Bronze. Por três motivos:

- **Reprodutibilidade:** os mesmos dados têm de dar sempre o mesmo nível.
- **Coerência:** o painel do produtor e a ficha pública já calculam o nível com o mesmo código (constituição, princípio IV). Um modelo que escolhesse o nível poderia contradizê-los.
- **Rastreabilidade:** é possível explicar exatamente por que um CAR ficou em Bronze (constituição, princípio VII).

```
Indicadores do CAR (JSON) ──► regras fixas ──► nível + motivos (códigos)
                                                   │
                     JSON + nível + motivos ───────┴──► agente ──► resumo do cartão
Resumos e níveis de todos os CARs ──► regra de agregação ──► nível do CNPJ ──► agente ──► resumo do CNPJ
```

## 1. Regra de nível por CAR

A regra é avaliada em ordem, e vale a primeira condição atendida. Só contam os **riscos abertos**: o
que já foi superado e o contexto nunca rebaixam o nível.

| Nível | Atende se… | Código do motivo |
|---|---|---|
| **Sem dados** | O MapBiomas não responde e não há cache | `SEM_DADOS_MAPBIOMAS` |
| **Bronze** (risco grave) | Algum **embargo vigente** | `EMBARGO_VIGENTE` |
| | Alerta aberta em **terra indígena ou UC de proteção integral** | `TI_UC_INTEGRAL` |
| | Alerta aberta **posterior a 2020** em **reserva legal ou APP** | `RL_APP_POS2020` |
| | DETER: **corte seletivo desordenado ou mineração** nos últimos 24 meses | `DETER_GRAVE` |
| **Silver** (risco aberto) | Alguma alerta aberta (sem autorização registrada ou com fiscalização), de qualquer data | `ALERTA_ABERTA` |
| | DETER: **degradação** nos últimos 24 meses | `DETER_DEGRADACAO` |
| | Embargos não determináveis | `DADOS_PARCIAIS` |
| **Gold** | Nenhuma das anteriores | — |

**Nunca rebaixam o nível:**
- alertas autorizadas, com embargo levantado ou suspensas judicialmente;
- UCs de uso sustentável;
- % de vegetação nativa;
- focos de calor;
- corte seletivo com padrão de manejo;
- volume do SINAFLOR;
- falhas de PRODES, DETER, Queimadas ou SINAFLOR. Essas fontes são contexto: quando falham, aparecem como "Indisponível", mas não rebaixam o nível.

### Com os dados reais (2026-11-06)

| CAR | Nível | Motivos |
|---|---|---|
| PE-2607505 | **Bronze** | `RL_APP_POS2020`: 27,1 ha em reserva legal e 2 alertas em APP, tudo de 2026 |
| MT-5102504 | **Bronze** | `EMBARGO_VIGENTE` (5) e `RL_APP_POS2020` (71,8 ha em reserva legal) |
| TO-1712504 | **Bronze** | `RL_APP_POS2020`: 5,4 ha em reserva legal e 3 alertas em APP, de 2024 |

Os três ficarem em Bronze leva à primeira decisão pendente (ver o final).

## 2. Regra do CNPJ: vale o pior CAR

- **Nível do CNPJ = o pior nível entre os seus CARs com dados.** O comprador não sabe de qual imóvel vem o produto, então o risco de um CAR alcança o CNPJ inteiro.
- Se algum CAR estiver em Sem dados e os demais em Gold → **Silver**. É o mesmo que a feature 002 já faz com dados parciais.
- Se nenhum CAR tiver dados → **Sem dados**.
- A exposição é sempre mostrada. Exemplo: "2 de 3 CARs em Bronze · 165 ha de alertas abertas".

## 3. O agente

### Duas chamadas separadas

1. **Uma por CAR:** recebe o JSON de indicadores, o nível e os códigos de motivo, e devolve um resumo estruturado.
2. **Uma por CNPJ:** recebe os dados estruturados de todos os CARs, e não apenas os textos, para que o resumo não perca informação de um passo para o outro. Devolve o resumo do CNPJ.

### Formato de saída (JSON validado)

```json
{
  "nivel": "bronze",
  "titulo": "Desmatamento recente em reserva legal, sem autorização registrada",
  "riscos": [
    "3 alertas de 2026 (74,5 ha) sem autorização registrada, 27,1 ha em reserva legal"
  ],
  "contexto": ["1 foco de calor em out/2026"],
  "ressalvas": [
    "O PRODES não registra regeneração: os 2,1 % de vegetação nativa podem subestimar a vegetação atual"
  ],
  "data_dos_dados": "2026-11-06"
}
```

### Regras do prompt

- Usar **apenas** os dados recebidos: cada número citado no texto tem de estar no JSON.
- **Não alterar nem discutir o nível**: o texto o explica a partir dos códigos de motivo recebidos.
- Separar riscos de contexto: o contexto nunca é apresentado como problema.
- Vocabulário: "sem autorização registrada", **nunca "ilegal" nem "crime"**; "alerta", e não "desmatamento ilegal".
- Incluir sempre as ressalvas que se aplicarem:
  - o PRODES não registra regeneração;
  - reserva legal e APP são calculadas sobre a área da alerta;
  - o volume do SINAFLOR é o da autorização inteira, que pode abranger vários CARs;
  - "Indisponível" não significa 0.
- Não dar conselhos jurídicos nem de compra (por exemplo, "não compre").
- Escrever em pt-BR, com no máximo 3 riscos e 3 itens de contexto por CAR, e uma frase de título.

### Controles depois da geração

- O nível do JSON tem de ser igual ao calculado.
- Cada número do texto tem de existir nos dados de entrada.
- O texto não pode conter nenhuma palavra proibida.

Se algum controle falhar, o resumo é gerado de novo. Se falhar outra vez, mostra-se um resumo de modelo,
sem IA. O resumo fica em cache conforme os dados de entrada e só é refeito quando os indicadores mudam.

**Modelo sugerido**: Claude Sonnet 5.5, pela qualidade do texto, ou Haiku 5.5 para grandes volumes de CARs, com temperatura baixa.

## Glossário

- **APP (Área de Preservação Permanente)**: faixas que o Código Florestal (Lei 12.651/2012) manda manter com vegetação nativa — margens de rios, entorno de nascentes e lagos, topos de morro e encostas íngremes, veredas e manguezais. Suprimir vegetação ali só é permitido em casos excepcionais, com autorização. "Alertas em APP" conta as alertas abertas que cruzam, mesmo em parte, uma APP.
- **Reserva legal**: porcentagem do imóvel que deve manter vegetação nativa (80 % em floresta na Amazônia Legal, 35 % no Cerrado da Amazônia Legal e 20 % nas demais regiões). Pode ser explorada com manejo sustentável, mas não desmatada.
- **Alerta aberta**: situação "sem autorização registrada", "com fiscalização" ou "embargo vigente".
- **Alerta superada**: situação "autorizada", "embargo levantado" ou "suspensa judicialmente".
- **EUDR**: regulamento europeu que exige produtos livres de desmatamento posterior a 31/12/2020.

## Decisões pendentes

1. **Reserva legal ou APP depois de 2020: Bronze ou Silver?** Com Bronze, os 3 CARs de referência ficam em Bronze. Alternativa: Bronze só acima de um limite — por exemplo, ≥ 1 % da área do CAR deixaria o TO (0,09 %) em Silver, enquanto PE (10 %) e MT continuariam em Bronze.
2. **Agregar o CNPJ pelo pior CAR?** É a recomendação, a menos que no futuro o comprador possa informar de qual CAR vem o produto.
3. **Um sinal EUDR separado do nível?** A EUDR exige ausência de desmatamento depois de 2020, **mesmo que legal**. Uma alerta autorizada de 2022 é Gold por esta regra, mas não cumpriria a EUDR. Proposta: um selo "Atenção EUDR" separado do nível.
