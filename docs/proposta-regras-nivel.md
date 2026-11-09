# Regras de nível: Gold, Silver e Bronze

**Situação**: em uso no painel do produtor e na consulta pública por CNPJ · **Atualizado em**: 2026-11-08

Este documento descreve as regras que o Elo Rural usa **hoje** para definir o nível de cada imóvel (CAR)
e de cada CNPJ. O produtor vê a mesma explicação, em linguagem simples, na página **"Entenda o nível"**
do painel.

## Princípios

- **Regras fixas, iguais para todos.** Os mesmos dados sempre dão o mesmo nível. Nenhuma inteligência
  artificial escolhe ou altera o nível.
- **Só contam os riscos em aberto.** O que já foi resolvido e as informações de contexto aparecem no
  detalhe do CAR, mas nunca rebaixam o nível.
- **Dado indisponível não é zero.** Se não foi possível verificar algo, o nível diz isso ("dados
  parciais") em vez de supor que está tudo bem.
- **Todos os motivos são mostrados.** O imóvel recebe o nível do motivo mais grave, mas a lista inclui
  todos os motivos encontrados, com seus números (quantidade, hectares, porcentagem).
- **Não é uma certificação.** O nível é um indicador calculado com dados públicos, não um parecer
  jurídico nem um selo ambiental.

## Os níveis

| Nível | Significado |
|---|---|
| **Gold** | Nenhum risco em aberto. |
| **Silver** | Há riscos em aberto, mas nenhum grave, ou parte dos dados não pôde ser verificada. |
| **Bronze** | Há pelo menos um risco grave em aberto. |
| **Sem dados** | Não foi possível obter os dados do imóvel (nem uma cópia recente). |

## Nível de cada imóvel (CAR)

Todos os critérios abaixo são avaliados. **Basta um motivo de Bronze para o imóvel ser Bronze**; sem
nenhum motivo de Bronze, basta um de Silver para ser Silver; sem nenhum motivo, o imóvel é Gold.

### Bronze: riscos graves

| Motivo | Quando se aplica |
|---|---|
| **Embargo vigente** | O imóvel tem pelo menos um embargo sem data de término. |
| **Terra indígena ou UC de proteção integral** | Uma alerta em aberto cruza, mesmo em parte, uma terra indígena ou uma unidade de conservação de proteção integral. |
| **Reserva legal ou APP depois de 2020** | Alertas em aberto detectadas depois de 31/12/2020, em reserva legal ou tocando uma APP, somam **1 % ou mais da área do imóvel**. Se a área do imóvel é desconhecida, conta como Bronze (critério conservador). |
| **Corte seletivo desordenado ou mineração** | O DETER (INPE) detectou alguma dessas classes no imóvel nos **últimos 24 meses**. Só se aplica na Amazônia. |

### Silver: riscos em aberto sem gravidade alta

| Motivo | Quando se aplica |
|---|---|
| **Alertas em aberto** | Qualquer alerta de desmatamento em aberto, de qualquer data. |
| **Reserva legal ou APP depois de 2020 (abaixo de 1 %)** | O mesmo caso do Bronze, mas somando **menos de 1 %** da área do imóvel. |
| **Degradação** | O DETER detectou degradação florestal nos **últimos 24 meses**. Só na Amazônia. |
| **Dados parciais** | Não foi possível determinar os embargos do imóvel (nem pelo MapBiomas nem pelo IBAMA) ou consultar as alertas do MapBiomas. |

### Gold

Nenhum dos motivos acima.

### Sem dados

O MapBiomas Alerta não respondeu e não há uma cópia recente dos dados do imóvel.

## O que conta como "em aberto"

Cada alerta de desmatamento do MapBiomas recebe **uma única situação**, verificada nesta ordem (vale a
primeira que se cumpre):

| Ordem | Situação | Conta para o nível? |
|---|---|---|
| 1 | Suspensa por decisão judicial | Não (superada) |
| 2 | Embargo vigente | **Sim (em aberto)** |
| 3 | Autorizada (autorização de supressão ou plano de manejo) | Não (superada) |
| 4 | Embargo levantado | Não (superada) |
| 5 | Com fiscalização | **Sim (em aberto)** |
| 6 | Sem autorização registrada | **Sim (em aberto)** |

Uma alerta sem autorização, fiscalização nem embargo aparece como **"sem autorização registrada"**,
nunca como "ilegal".

## De onde vêm os embargos

1. **MapBiomas Alerta** é a fonte principal (embargos do IBAMA, do ICMBio e de órgãos estaduais).
2. Quando o MapBiomas não consegue informar os embargos de um imóvel, usamos as **áreas embargadas
   publicadas pelo IBAMA**:
   - um embargo conta para o imóvel se a área embargada se sobrepõe **0,1 ha ou mais** ao polígono do CAR
     (descarta toques de borda com vizinhos);
   - essa camada não indica embargos levantados, então **todos contam como vigentes**;
   - cobre só embargos do IBAMA (não do ICMBio nem de órgãos estaduais).
3. Se nenhuma das duas fontes responde, os embargos ficam "indisponíveis" e o imóvel recebe o motivo
   **dados parciais**.

O mesmo embargo (mesmo órgão e mesmo número de processo) conta uma só vez.

## O que nunca rebaixa o nível

- Alertas superadas: autorizadas, com embargo levantado ou suspensas judicialmente.
- Embargos levantados.
- Unidades de conservação de uso sustentável (por exemplo, APAs).
- Porcentagem de vegetação nativa (PRODES).
- Focos de calor.
- Corte seletivo com padrão geométrico, típico de manejo florestal autorizado.
- Manejo florestal autorizado no SINAFLOR.
- Falhas temporárias do INPE (PRODES, DETER, Queimadas) ou do SINAFLOR: o dado aparece como
  "Indisponível", sem penalizar.

## Nível do CNPJ

- **É o nível do imóvel em pior situação**, porque quem compra não sabe de qual imóvel vem o produto.
- Se algum imóvel está **Sem dados** e todos os demais estão em **Gold**, o CNPJ fica em **Silver**
  (dados parciais).
- Se **nenhum** imóvel tem dados, o CNPJ fica em **Sem dados**.
- CNPJ não cadastrado ou sem imóveis informados → **Sem dados**.
- Se várias contas usam o mesmo CNPJ, contam todos os imóveis delas, sem repetir.
- Junto do nível aparecem a distribuição (por exemplo, "2 de 3 imóveis em Bronze") e os motivos que
  definem o nível, com o número de imóveis em que cada um aparece.
- O comprador vê na consulta pública o **mesmo nível** que o produtor vê no painel, só com dados
  agregados: nunca códigos de CAR, mapas ou listas de alertas e embargos.

## Sinal "Atenção EUDR" (separado do nível)

O regulamento europeu contra o desmatamento (EUDR, Regulamento (UE) 2023/1115) exige produtos sem
desmatamento depois de 31/12/2020, **mesmo que autorizado**. Por isso:

- o sinal aparece quando o imóvel tem **alguma alerta do MapBiomas detectada depois de 31/12/2020**, em
  qualquer situação (inclusive autorizada ou superada);
- no CNPJ, aparece se algum imóvel tem o sinal;
- se as alertas do MapBiomas não puderam ser consultadas, o sinal fica sem dado (não "não");
- é **separado do nível**: um imóvel pode ser Gold e ter o sinal.

Limitações: usa a data de **detecção** da alerta (não a data exata do desmatamento), só considera alertas
do MapBiomas e não distingue floresta de outras formações nativas. É um sinal de atenção, não uma
verificação de conformidade com a EUDR.

## Limites usados

| Limite | Valor |
|---|---|
| Corte do desmatamento recente (reserva legal/APP e EUDR) | 31/12/2020 |
| Reserva legal ou APP depois de 2020: Bronze a partir de | 1 % da área do imóvel |
| Janela do DETER | 24 meses |
| Sobreposição mínima de um embargo do IBAMA | 0,1 ha |

## Onde está no código

As regras ficam em um único lugar, usado pelo painel, pela consulta pública e pelo relatório:
`backend/app/services/level_rules.py` (`car_level` e `cnpj_level`). A situação de cada alerta é definida
em `backend/app/services/car_indicators.py` (`classify_alert`) e os embargos do IBAMA em
`backend/app/sources/ibama.py`. Se um limite mudar, atualize também os textos de "Entenda o nível"
(`t.rules` em `frontend/src/i18n/pt-BR.ts`) e este documento.
