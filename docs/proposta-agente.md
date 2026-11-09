# Proposta: agente de resumos

**Status**: **implementada na feature 008** (`specs/008-relatorio-ia/`) em 2026-11-08, com diferenças · **Data**:
2026-11-06

Diferenças em relação a esta proposta:
- **Uma só chamada por CNPJ** (não uma por CAR): a IA recebe os dados já calculados de todos os imóveis e
  devolve o relatório inteiro, inclusive a frase de cada imóvel.
- **Pseudônimos** ("Imóvel A"…) no lugar dos códigos de CAR, e sem o CNPJ.
- O formato de saída é o `CnpjReport` da feature 005 (`titulo`, `riscos`, `contexto`, `ressalvas`,
  `imoveis`); não há `data_dos_dados` no texto da IA (o backend o preenche).
- Se os controles falham duas vezes, o texto é montado por regras (`origem="regras"`).
- O modelo é o configurado no `.env` (padrão Gemini `gemini-3.5-flash`).

O funcionamento atual está em [`arquitetura.md`](arquitetura.md#relatório-do-cnpj-features-005-e-008). O
restante deste documento é a proposta original.

As regras de nível que o agente recebe estão em
[`proposta-regras-nivel.md`](proposta-regras-nivel.md).

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

## Duas chamadas separadas

1. **Uma por CAR:** recebe o JSON de indicadores, o nível e os códigos de motivo, e devolve um resumo estruturado.
2. **Uma por CNPJ:** recebe os dados estruturados de todos os CARs, e não apenas os textos, para que o resumo não perca informação de um passo para o outro. Devolve o resumo do CNPJ.

## Formato de saída (JSON validado)

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

## Regras do prompt

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

## Controles depois da geração

- O nível do JSON tem de ser igual ao calculado.
- Cada número do texto tem de existir nos dados de entrada.
- O texto não pode conter nenhuma palavra proibida.

Se algum controle falhar, o resumo é gerado de novo. Se falhar outra vez, mostra-se um resumo de modelo,
sem IA. O resumo fica em cache conforme os dados de entrada e só é refeito quando os indicadores mudam.

**Modelo sugerido**: Claude Sonnet 5.5, pela qualidade do texto, ou Haiku 5.5 para grandes volumes de CARs, com temperatura baixa.
