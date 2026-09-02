# Spec 09 — Motor tributário mínimo CBS 2026: regime regular, NF-e 55 e tributação integral

**Status:** pronta para implementação após auditoria normativa  
**Prioridade:** bloqueadora  
**Depende de:** Specs 00–08 + Volumes I–III  
**Bloqueia:** Specs 10–11  
**Snapshot normativo-operacional:** 31/08/2026  
**Data da auditoria:** 02/09/2026

---

# Objetivo

Implementar o primeiro operador tributário concreto do projeto para uma fatia vertical deliberadamente estreita da CBS em 2026.

A Spec 09 deve transformar:

```text
EVENTOS
+
EVENTOS_FISCAIS
+
ENTIDADE
+
CENARIOS_TRIBUTARIOS
+
FISCAL_PARAM
```

em:

```text
TAX_OPERATION_RESULT
+
TAX_ASSESSMENT_RESULT
```

para um único cenário CBS regular de agosto de 2026, preservando os objetos canônicos:

```text
chi_t
mathfrak E_t
Theta_t^eff
B_CBS,k,t
tau_CBS,k,t
C_CBS,k,t
D_CBS,k,t
S_CBS,t^apur
T_CBS,t^recolher
C_CBS,t^saldo
```

A implementação deve demonstrar, com rastreabilidade normativa completa, que o sistema consegue:

1. rejeitar contextos fora do primeiro recorte;
2. selecionar regras efetivas versionadas;
3. validar os fatos/documentos fiscais mínimos;
4. calcular débito de CBS nas vendas;
5. apropriar crédito de CBS nas compras elegíveis;
6. agregar débitos e créditos mensalmente;
7. separar saldo de apuração, obrigação exigível de recolhimento, caixa e despesa contábil;
8. preservar a dispensa transitória de recolhimento de 2026 como regra condicionada, e não como constante sem causa jurídica.

---

# Contexto canônico

## Source of truth

A precedência permanece:

```text
Volumes I–III
    >
specs
    >
código
```

A Spec 08 continua autoritativa para os schemas de:

```text
ENTIDADE
EVENTOS_FISCAIS
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
TAX_OPERATION_RESULT_COLUMNS
TAX_ASSESSMENT_RESULT_COLUMNS
```

Não alterar os schemas de entrada da Spec 08 para acomodar esta implementação.

## Relação com a suficiência funcional

O Volume II define:

```text
Dep(H_tax)
=
atributos efetivamente lidos pelo operador tributário.
```

Logo, esta spec declara apenas os atributos mínimos exigidos pelo primeiro operador CBS. Não construir uma taxonomia fiscal universal.

## Preservação da semântica de apuração e recolhimento

O Volume I fornece a estrutura-base:

```text
S_j,t^apur = D_j,t - C_j,t + A_j,t^tax
```

com a parcela positiva do saldo como obrigação nominal antes das particularidades de pagamento/transição.

Para esta spec, definir internamente:

```text
T_CBS,t^nominal = max(S_CBS,t^apur, 0)
```

A transição de 2026 é aplicada depois:

```text
T_CBS,t^recolher
=
theta_2026_pag(
    T_CBS,t^nominal,
    eta_t,
    Theta_t^eff
)
```

No recorte admissível desta spec, em que as obrigações acessórias da CBS foram cumpridas:

```text
T_CBS,t^recolher = 0
```

Essa igualdade não deve ser hard-coded sem a leitura do fato de conformidade e da regra normativa versionada.

## Caixa e DRE não são apuração

Preservar:

```text
Y_CBS,t^tax
=
(
    S_apur,
    T_recolher,
    P_cash,
    E_DRE,
    C_saldo
)
```

Nesta spec:

```text
P_CASH_CENTS = None
E_DRE_CENTS  = None
```

Motivo:

- `P_cash` requer fatos financeiros de pagamento, não inferíveis apenas da apuração;
- `E_DRE` requer tratamento contábil do tributo, que não é objeto desta spec.

Não substituir `None` por zero para aparentar completude.

---

# Recorte jurídico-operacional congelado

A Spec 09 implementa **somente** o seguinte recorte:

| Dimensão | Valor suportado |
|---|---|
| Tributo | CBS |
| Período de apuração | agosto de 2026 |
| Fatos geradores suportados | 03/08/2026 a 31/08/2026 |
| Entidade | pessoa jurídica comercial |
| Atividade | compra e revenda de mercadorias |
| Situação ICMS | contribuinte do ICMS |
| Regime da entidade | não optante pelo Simples Nacional/MEI |
| Regime de consumo | regime regular da CBS |
| Regime especial | nenhum |
| Operações | compras e vendas domésticas ordinárias de bens materiais |
| Documento | NF-e modelo 55 |
| Granularidade | uma única mercadoria/item tributável por NF-e/evento |
| Tributação | integral |
| CST IBS/CBS | `000` |
| cClassTrib | `000001` |
| Alíquota CBS | 0,9% em 2026, carregada de `FISCAL_PARAM` |
| Pagamento antecipado | excluído |
| Devolução/cancelamento | excluídos |
| Ajustes fiscais | zero |
| Saldo fiscal anterior | zero |
| Estado intertemporal | não introduzido |
| Cumprimento acessório | obrigações acessórias CBS cumpridas |
| Split payment | não implementado em produção no snapshot auditado |
| Recolhimento pelo adquirente | não implementado em produção no snapshot auditado |

A data de referência normativa do cenário deve ser:

```text
2026-08-31
```

Esta é uma decisão deliberada de snapshot histórico. Não estender automaticamente as conclusões operacionais sobre split payment ou recolhimento pelo adquirente para setembro de 2026 ou períodos posteriores.

---

# Fora de escopo

Não implementar nesta spec:

- IBS;
- Imposto Seletivo;
- Simples Nacional;
- MEI;
- regime monofásico;
- alíquota reduzida;
- alíquota zero;
- isenção;
- imunidade;
- suspensão;
- diferimento;
- crédito presumido;
- ZFM/ALC;
- importação;
- exportação;
- compra governamental;
- combustíveis;
- serviços financeiros;
- imóveis;
- regimes específicos;
- devoluções;
- cancelamentos;
- antecipações de pagamento;
- múltiplos itens por NF-e;
- reconstrução integral da base fiscal a partir dos componentes comerciais da operação;
- classificação automática por NCM;
- cálculo universal de idoneidade documental;
- execução operacional do split payment;
- execução operacional do recolhimento pelo adquirente;
- múltiplos períodos;
- transporte de saldo anterior;
- ressarcimento;
- compensação intertemporal;
- pagamento financeiro do tributo;
- reconhecimento contábil/DRE da CBS;
- comparação entre cenários;
- engine tributário genérico;
- DSL normativa;
- framework genérico de regras.

Se qualquer dado de entrada exigir um desses ramos, o cenário deve ser rejeitado como fora do recorte, e não aproximado por uma regra genérica.

---

# Auditoria normativa consolidada

## Matriz normativa

| Regra | Fonte/dispositivo | Condição factual | Formalização | Dado necessário | Resultado/teste mínimo |
|---|---|---|---|---|---|
| Regime regular | Decreto 12.955/2026, art. 41, §1º | contribuinte não optante pelo Simples/MEI | `chi_t` | cenário: `REGIME_ENTIDADE`, `REGIME_CONSUMO` | cenário Simples/MEI deve ser rejeitado |
| Incidência | Decreto 12.955/2026, art. 4º | compra/venda onerosa | `INCIDE_k=True` | `TIPO_EVENTO` suportado | compra/venda ordinária admitida |
| Fato gerador | Decreto 12.955/2026, art. 11, §1º, I | bem material entregue/disponibilizado | data fiscal | `DT_FORNECIMENTO` | data fiscal controla o período |
| Base | Decreto 12.955/2026, art. 13 | operação ordinária do recorte | `B_CBS,k,t=VBC_CENTS` documental | `VBC_CENTS` | não exigir igualdade com `VL_EVENTO_CENTS` |
| Alíquota | LC 214/2025, art. 346; Decreto 12.955/2026, art. 582 | fato gerador em 2026 | `tau=Decimal("0.009")` carregado de parâmetro | `FISCAL_PARAM` + `PCBS_PERCENT` documental | `PCBS_PERCENT=0.9` |
| NF-e 55 | Ato Conjunto RFB/CGIBS 1/2025, art. 2º, §1º, I | operação documentada | validação documental | `MODELO_DFE` | deve ser `55` |
| Obrigatoriedade em agosto | Ato Conjunto RFB/CGIBS 4/2026, art. 1º, I e §4º | NF-e 55; sujeito contribuinte do ICMS | `chi_t` + data mínima | `CONTRIBUINTE_ICMS`, `DT_FORNECIMENTO` | não contribuinte do ICMS é fora do recorte de agosto |
| Validade do DF-e | Decreto 12.955/2026, arts. 130–132 | autorização de uso concedida | validação documental mínima do recorte | `CHAVE_NFE`, `PROTOCOLO_AUTORIZACAO`, `STATUS_DFE` | ausência de protocolo/status válido rejeita |
| CST/cClass | tabela oficial CST/cClassTrib de 23/06/2026 | tributação integral | seleção de regra | `CST_IBS_CBS`, `CCLASSTRIB` | somente `000`/`000001` |
| Valor CBS no DF-e | NT 2025.002 v1.51, regra UB67-10 | grupo CBS informado | verificar `vBC*(pCBS/100)` | `VBC_CENTS`, `PCBS_PERCENT`, `VCBS_CENTS` | aceitar diferença de até 1 centavo |
| Crédito — regra-base | LC 214/2025, art. 47 | adquirente no regime regular; aquisição elegível; DF-e idôneo | `C_CBS,k,t` | destino da aquisição + dados DF-e | aquisição para uso pessoal não suportada |
| Crédito — dispensa da extinção | LC 214/2025, art. 48 | nenhuma modalidade dos incisos I–II implementada | `credit_extinction_waived` | parâmetros de status operacional | se alguma modalidade estiver ativa, rejeitar recorte |
| Split — status agosto/2026 | Ato Conjunto RFB/CGIBS 2/2026 + comunicação oficial SVRS de 02/03/2026 + auditoria do rol oficial de atos até 31/08/2026 | documentação/preparação sem obrigatoriedade produtiva no snapshot | parâmetro operacional versionado | `CBS_SPLIT_PAYMENT_IMPLEMENTED=false` | se `true`, branch desta spec deixa de ser válido |
| Recolhimento pelo adquirente — status agosto/2026 | materiais oficiais do Projeto Piloto RTC + auditoria do rol oficial de atos até 31/08/2026 | funcionalidade em piloto/simulador no snapshot | parâmetro operacional versionado | `CBS_BUYER_COLLECTION_IMPLEMENTED=false` | se `true`, branch desta spec deixa de ser válido |
| Período | Decreto 12.955/2026, art. 43 | CBS mensal | agrupamento mensal | `DT_FORNECIMENTO` | uma única apuração de agosto |
| Apuração | Decreto 12.955/2026, art. 44 | saldo inicial e ajustes fixados em zero | `S_apur=sum(D)-sum(C)` | resultados operacionais | saldo positivo/devedor e negativo/credor testados |
| Dispensa 2026 | Decreto 12.955/2026, art. 464, caput e §1º | obrigações acessórias cumpridas | `theta_2026_pag` | `CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026` | `S_apur>0` e compliance `true` -> `T_recolher=0` |
| Saldo credor | estrutura canônica + Decreto 12.955/2026, art. 465 | `S_apur<0` | `C_saldo=max(-S_apur,0)` | `S_apur` | não implementar ressarcimento/carry-forward nesta spec |

## Classificação epistemológica das decisões

### Fatos normativos diretos

São fatos diretamente suportados pelas normas/documentos oficiais:

```text
incidência
momento do fato gerador
base como valor da operação
alíquota 0,9%
regime regular
período mensal
regra de crédito dos arts. 47–48
validade do DF-e por autorização
NF-e 55
CST 000 / cClassTrib 000001
fórmula/tolerância documental de vCBS
dispensa de recolhimento em 2026 condicionada às obrigações acessórias
```

### Inferência normativa-operacional auditada

A conclusão:

```text
split payment não implementado em produção em 31/08/2026
recolhimento pelo adquirente não implementado em produção em 31/08/2026
```

é uma conclusão de auditoria do snapshot, baseada em documentação oficial de preparação/piloto e na verificação do rol de atos conjuntos existente até essa data.

Ela deve ser:

- versionada;
- datada;
- limitada ao snapshot;
- representada como parâmetro operacional;
- nunca transformada em constante permanente de código.

### Decisões de engenharia

São escolhas desta spec, e não imposições da lei:

```text
agosto de 2026 como primeiro período
uma única mercadoria/item por NF-e/evento
saldo inicial zero
ajustes zero
base consumida como vBC documental
P_CASH_CENTS=None
E_DRE_CENTS=None
```

---

# Fontes oficiais utilizadas

## Corpus local principal

Usar prioritariamente os arquivos já versionados no repositório:

```text
docs/tax_sources/rtc/normative/02_LC_214_2025_compilada.html
docs/tax_sources/rtc/normative/04_Decreto_12955_2026.html

docs/tax_sources/rtc/operational/06_Ato_Conjunto_RFB_CGIBS_01_2025.pdf
docs/tax_sources/rtc/operational/07_Ato_Conjunto_RFB_CGIBS_04_2026.pdf
docs/tax_sources/rtc/operational/09_NFe_Nota_Tecnica_2025_002_v1.51.pdf
docs/tax_sources/rtc/operational/14_Tabela_cClassTrib_IBS_CBS_2026-06-23.xlsx
docs/tax_sources/rtc/operational/15_Tabela_Aliquotas_CBS_2026-05-12.xlsx
docs/tax_sources/rtc/operational/18_Ato_Conjunto_RFB_CGIBS_02_2026.pdf
docs/tax_sources/rtc/operational/20_Ato_Tecnico_Conjunto_RFB_CGIBS_02_2026.pdf
docs/tax_sources/rtc/operational/21_NFe_NT_2026_006_v1.00.pdf
```

## Fontes oficiais online de apoio ao snapshot operacional

As seguintes páginas/documentos oficiais fundamentam parâmetros operacionais do snapshot e devem ser registradas em `FISCAL_PARAM` quando o parâmetro delas depender:

```text
https://dfe-portal.svrs.rs.gov.br/Nfe/Busca?palavraschave=2026

https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/reforma-tributaria-do-consumo/20250817-rtc-empresas-versao-2.pdf/@@download/file/20250817%20RTC%20Empresas%20Vers%C3%A3o%202.pdf

https://www.cgibs.gov.br/atos-conjuntos
```

## Fonte 22 — defeito de corpus não bloqueador

No estado auditado do repositório, o arquivo:

```text
docs/tax_sources/rtc/operational/22_NFe_NT_2026_002_v1.10a.pdf
```

é byte a byte idêntico ao arquivo 16 (`v1.10`).

A NT 2026.002 v1.10a trata de DANFE Simplificado Tipo 2/contingência e **não pertence a `Dep(H_tax)` deste recorte**.

Portanto:

- não usar o arquivo 22 na implementação;
- não bloquear a Spec 09 por esse defeito;
- não corrigir ou substituir o arquivo automaticamente nesta spec.

---

# Entradas

A API principal recebe:

```python
events: pd.DataFrame
tax_context: TaxContext
scenario_id: str
```

`TaxContext` é o objeto já implementado na Spec 08.

Não reconstruir o contexto tributário a partir do workbook dentro do motor.

---

# `chi_t` — admissibilidade mínima

Implementar uma função específica, não um classificador universal:

```python
def validate_cbs_2026_admissibility(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> ValidationReport:
    ...
```

Interpretar:

```text
chi_t = 1  <=>  report.ok is True
```

## Condições obrigatórias

### Cenário

O cenário ativo selecionado deve satisfazer:

```text
REGIME_ENTIDADE = "nao_optante_simples_mei"
REGIME_CONSUMO  = "cbs_regime_regular"
REGIME_ESPECIAL = None ou vazio normalizado
DT_REFERENCIA_NORMATIVA = 2026-08-31
```

O `ID_VERSAO_NORMATIVA` deve existir em `FISCAL_PARAM`.

### ENTIDADE

A tabela longa deve conter, para a entidade do cenário:

```text
TIPO_PESSOA = "pj"
ATIVIDADE = "comercio_revenda_mercadorias"
CONTRIBUINTE_ICMS = true
CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026 = true
```

Esses campos são fatos de `eta_t`, não parâmetros normativos.

`CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026` não deve ser inferido de inscrição no PNCT.

### EVENTOS

São suportados como eventos fiscalmente relevantes apenas:

```text
compra_mercadoria_a_vista
compra_mercadoria_a_prazo
venda_a_vista
venda_a_prazo
```

Os demais eventos contábeis permanecem válidos no DataFrame, porém:

```text
não geram linha em TAX_OPERATION_RESULT
```

Não registrar `INCIDE=False` para aporte, pagamento, recebimento, depreciação etc. Eles simplesmente estão fora do domínio operacional desta regra tributária.

### Data

Para todo evento fiscal suportado:

```text
2026-08-03 <= DT_FORNECIMENTO <= 2026-08-31
```

`DT_FORNECIMENTO` controla o período fiscal.

Não substituir automaticamente por `DT_EVENTO`.

---

# `EVENTOS_FISCAIS` — `Dep(H_tax)` mínimo

Para cada compra/venda suportada, exigir exatamente os atributos necessários abaixo.

## Atributos comuns

```text
MODELO_DFE
CHAVE_NFE
PROTOCOLO_AUTORIZACAO
STATUS_DFE
DT_FORNECIMENTO
QTD_ITENS_DFE
CST_IBS_CBS
CCLASSTRIB
VBC_CENTS
PCBS_PERCENT
VCBS_CENTS
```

## Atributo adicional para compras

```text
DESTINACAO_AQUISICAO
```

Valor suportado:

```text
revenda
```

## Semântica e validações

### `MODELO_DFE`

```text
55
```

O valor efetivo permitido deve ser obtido de `FISCAL_PARAM`, não repetido como constante normativa no cálculo.

### `CHAVE_NFE`

- string;
- exatamente 44 dígitos;
- não vazia;
- única entre os eventos fiscais deste recorte.

Não implementar nesta spec o algoritmo completo de validação do dígito verificador da chave.

### `PROTOCOLO_AUTORIZACAO`

String não vazia.

### `STATUS_DFE`

Valor suportado:

```text
autorizado_nao_cancelado
```

Essa é uma simplificação operacional do recorte para representar que existe autorização de uso vigente e que o documento não está cancelado.

### `DT_FORNECIMENTO`

Tipo lógico `date`, armazenado pelo contrato longo da Spec 08.

### `QTD_ITENS_DFE`

```text
1
```

A restrição é de engenharia.

### `CST_IBS_CBS`

Carregado/validado contra o parâmetro efetivo correspondente a `000`.

### `CCLASSTRIB`

Carregado/validado contra o parâmetro efetivo correspondente a `000001`.

### `VBC_CENTS`

Inteiro estritamente positivo.

Representa a base fiscal documental observada.

### `PCBS_PERCENT`

Decimal documental em unidades percentuais.

No recorte:

```text
0.9
```

A regra efetiva interna deve ser armazenada como fração:

```text
0.009
```

Não misturar percentual com fração.

### `VCBS_CENTS`

Inteiro não negativo em centavos.

### `DESTINACAO_AQUISICAO`

Apenas para compra:

```text
revenda
```

Isso evita que a primeira regra de crédito alcance consumo pessoal ou outra destinação não auditada.

---

# `FISCAL_PARAM` — parâmetros efetivamente consumidos

A versão normativa de exemplo deve utilizar:

```text
ID_VERSAO_NORMATIVA = "CBS_2026_08_31_V1"
```

A implementação não deve depender do texto exato desse ID, apenas da referência feita pelo cenário.

Exigir exatamente uma ocorrência vigente, para o cenário/data, de cada `CHAVE_PARAM` abaixo:

```text
CBS_RATE_FRACTION
CBS_ASSESSMENT_PERIOD
CBS_NFE_MODEL
CBS_NFE_MANDATORY_FROM
CBS_CST_INTEGRAL
CBS_CCLASSTRIB_INTEGRAL
CBS_VCBS_TOLERANCE_CENTS
CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT
CBS_SPLIT_PAYMENT_IMPLEMENTED
CBS_BUYER_COLLECTION_IMPLEMENTED
CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT
```

## Valores esperados no fixture canônico

```text
CBS_RATE_FRACTION = 0.009
CBS_ASSESSMENT_PERIOD = monthly
CBS_NFE_MODEL = 55
CBS_NFE_MANDATORY_FROM = 2026-08-03
CBS_CST_INTEGRAL = 000
CBS_CCLASSTRIB_INTEGRAL = 000001
CBS_VCBS_TOLERANCE_CENTS = 1
CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT = true
CBS_SPLIT_PAYMENT_IMPLEMENTED = false
CBS_BUYER_COLLECTION_IMPLEMENTED = false
CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT = true
```

Esses valores devem estar apenas no arquivo de parâmetros/fixture versionado e em testes explicitamente vinculados à fonte. Não criar equivalentes como constantes legais em `canonical.py` ou no motor.

## Proveniência mínima por parâmetro

### `CBS_RATE_FRACTION`

```text
TIPO_FONTE = norm
FONTE = LC 214/2025
DISPOSITIVO = art. 346
VIG_INI = 2026-01-01
VIG_FIM = 2026-12-31
```

### `CBS_ASSESSMENT_PERIOD`

```text
TIPO_FONTE = reg
FONTE = Decreto 12.955/2026
DISPOSITIVO = art. 43
```

### `CBS_NFE_MODEL`

```text
TIPO_FONTE = oper
FONTE = Ato Conjunto RFB/CGIBS 1/2025
DISPOSITIVO = art. 2º, §1º, I
```

### `CBS_NFE_MANDATORY_FROM`

```text
TIPO_FONTE = oper
FONTE = Ato Conjunto RFB/CGIBS 4/2026
DISPOSITIVO = art. 1º, I e §4º
```

### `CBS_CST_INTEGRAL` / `CBS_CCLASSTRIB_INTEGRAL`

```text
TIPO_FONTE = tec
FONTE = Tabela CST/cClassTrib oficial de 23/06/2026
```

### `CBS_VCBS_TOLERANCE_CENTS`

```text
TIPO_FONTE = tec
FONTE = NT 2025.002 v1.51
DISPOSITIVO = regra UB67-10
```

### `CBS_CREDIT_WAIVER_IF_MODALITIES_ABSENT`

```text
TIPO_FONTE = norm
FONTE = LC 214/2025
DISPOSITIVO = art. 48
```

### `CBS_SPLIT_PAYMENT_IMPLEMENTED`

```text
TIPO_FONTE = oper
VALOR = false
VIG_FIM = 2026-08-31
DATA_CONSULTA = 2026-09-02
```

A proveniência deve apontar para comunicação oficial que caracteriza os campos de split em 2026 como preparatórios e informa que eventual obrigatoriedade produtiva dependerá de instrumentos conjuntos posteriores. A auditoria deve estar limitada ao snapshot de 31/08/2026.

### `CBS_BUYER_COLLECTION_IMPLEMENTED`

```text
TIPO_FONTE = oper
VALOR = false
VIG_FIM = 2026-08-31
DATA_CONSULTA = 2026-09-02
```

A proveniência deve apontar para material oficial do Projeto Piloto RTC que trata o recolhimento pelo adquirente/RAD como funcionalidade de teste/simulador, complementado pela auditoria do rol oficial de atos até o snapshot.

### `CBS_2026_COLLECTION_WAIVER_IF_ACCESSORY_COMPLIANT`

```text
TIPO_FONTE = reg
FONTE = Decreto 12.955/2026
DISPOSITIVO = art. 464, caput e §1º
VIG_INI = 2026-01-01
VIG_FIM = 2026-12-31
```

---

# `mathfrak E_t` — seletor mínimo de regras efetivas

Implementar:

```python
@dataclass(frozen=True)
class EffectiveCbs2026Rules:
    normative_version_id: str
    rule_version: str
    rate_fraction: Decimal
    assessment_period: str
    nfe_model: str
    nfe_mandatory_from: date
    cst_integral: str
    cclasstrib_integral: str
    vcbs_tolerance_cents: Decimal
    credit_waiver_if_modalities_absent: bool
    split_payment_implemented: bool
    buyer_collection_implemented: bool
    collection_waiver_if_accessory_compliant: bool

    @property
    def credit_extinction_waived(self) -> bool:
        return (
            self.credit_waiver_if_modalities_absent
            and not self.split_payment_implemented
            and not self.buyer_collection_implemented
        )
```

Implementar o seletor:

```python
def select_effective_cbs_2026_rules(
    tax_context: TaxContext,
    scenario_id: str,
) -> EffectiveCbs2026Rules:
    ...
```

Regras:

1. selecionar a linha do cenário;
2. obter `ID_VERSAO_NORMATIVA`;
3. filtrar parâmetros dessa versão e `TRIBUTO == "CBS"`;
4. respeitar `VIG_INI <= DT_REFERENCIA_NORMATIVA <= VIG_FIM`, tratando `VIG_FIM=None` como aberto;
5. exigir todas as chaves desta spec;
6. exigir unicidade por chave vigente;
7. converter `VALOR` conforme `TIPO_VALOR` usando a infraestrutura da Spec 08 ou helper local pequeno;
8. exigir proveniência válida já coberta por `validate_tax_parameters()`;
9. exigir uma única `VERSAO_REGRA` coerente entre os parâmetros efetivos, ou rejeitar;
10. não criar linguagem genérica de regras.

Se:

```text
credit_extinction_waived is False
```

rejeitar o cenário como fora do recorte da Spec 09.

Não implementar o ramo que exige rastreamento da extinção do débito da aquisição.

---

# Regra de incidência

Para eventos fiscais suportados e contexto admissível:

```text
INCIDE = True
```

Não criar uma função universal de incidência.

A presença de um evento contábil não suportado não implica `INCIDE=False`; ele simplesmente não é processado pelo motor CBS desta spec.

---

# Base `B_CBS,k,t`

Definir nesta primeira implementação:

```text
B_CBS,k,t = VBC_CENTS
```

onde `VBC_CENTS` é o `vBC` documental observado na NF-e.

Não definir:

```text
B_CBS,k,t = VL_EVENTO_CENTS
```

Não exigir:

```text
VBC_CENTS == VL_EVENTO_CENTS
```

A reconstrução legal completa do valor da operação e de suas inclusões/exclusões pertence a uma spec posterior.

---

# Validação documental de `vCBS`

Para o recorte integral, sem redução, diferimento, devolução tributária ou crédito presumido:

```python
expected_vcbs_cents = Decimal(VBC_CENTS) * rate_fraction
```

Validar:

```python
abs(Decimal(VCBS_CENTS) - expected_vcbs_cents)
    <= vcbs_tolerance_cents
```

Também validar:

```python
Decimal(PCBS_PERCENT) / Decimal("100") == rate_fraction
```

## Regra de arredondamento

Não inventar `ROUND_HALF_UP`, `ROUND_HALF_EVEN` ou qualquer outro método como fonte de verdade.

O documento fornece `VCBS_CENTS` inteiro e a NT fornece tolerância de ±R$ 0,01.

Depois de validar o documento dentro da tolerância:

```text
VCBS_CENTS documental
```

é o valor utilizado no débito/crédito do recorte.

---

# Débito `D_CBS,k,t`

Para venda admitida:

```text
D_CBS,k,t = VCBS_CENTS
C_CBS,k,t = 0
```

O valor utilizado é o destaque documental validado.

---

# Crédito `C_CBS,k,t`

Para compra admitida:

```text
DESTINACAO_AQUISICAO = revenda
DF-e válido/autorizado
CST = 000
cClassTrib = 000001
pCBS correto
vCBS correto dentro da tolerância
credit_extinction_waived = True
```

então:

```text
C_CBS,k,t = VCBS_CENTS
D_CBS,k,t = 0
```

A implementação deve tornar explícito que a dispensa de comprovação/extinção é consequência de:

```text
art. 48
+
status operacional das modalidades
```

Não assumir universalmente:

```text
crédito = 0.9% * compra
```

O valor de crédito desta spec vem do `VCBS_CENTS` documental correto e validado.

---

# Resultado por operação

Usar exatamente:

```python
TAX_OPERATION_RESULT_COLUMNS
```

já definido em `canonical.py`:

```text
ID_CENARIO
ID_EVENTO
TRIBUTO
INCIDE
BASE_CENTS
ALIQUOTA
CREDITO_CENTS
DEBITO_CENTS
VERSAO_REGRA
```

Regras:

- uma linha por evento de compra/venda suportado;
- ordenar por `ID_EVENTO` de forma determinística;
- `TRIBUTO="CBS"`;
- `INCIDE=True`;
- `BASE_CENTS=VBC_CENTS`;
- `ALIQUOTA=Decimal("0.009")` obtido da regra efetiva;
- compra: crédito documental, débito zero;
- venda: débito documental, crédito zero;
- `VERSAO_REGRA` deve vir da regra efetiva selecionada.

---

# Apuração mensal

No recorte:

```text
saldo fiscal anterior = 0
ajustes = 0
```

Logo:

```python
total_debits = sum(DEBITO_CENTS)
total_credits = sum(CREDITO_CENTS)
S_APUR_CENTS = total_debits - total_credits
```

Convenção:

```text
S_APUR_CENTS > 0  => saldo nominal devedor
S_APUR_CENTS < 0  => saldo credor/recuperável
```

Definir internamente:

```python
T_NOMINAL_CENTS = max(S_APUR_CENTS, 0)
C_SALDO_CENTS = max(-S_APUR_CENTS, 0)
```

`T_NOMINAL_CENTS` é intermediário e não exige alteração do schema canônico.

---

# Recolhimento 2026

Aplicar a regra efetiva somente depois da apuração nominal.

No recorte admissível:

```text
collection_waiver_if_accessory_compliant = True
CUMPRIU_OBRIGACOES_ACESSORIAS_CBS_2026 = True
```

portanto:

```python
T_RECOLHER_CENTS = 0
```

O teste deve demonstrar explicitamente o caso:

```text
S_APUR_CENTS > 0
T_RECOLHER_CENTS = 0
```

Se o atributo de cumprimento estiver ausente ou for `False`:

```text
rejeitar cenário como fora do recorte
```

Não implementar nesta spec o cálculo para contribuinte que não cumpriu as obrigações acessórias.

---

# Resultado de apuração

Usar exatamente:

```python
TAX_ASSESSMENT_RESULT_COLUMNS
```

já definido em `canonical.py`:

```text
ID_CENARIO
TRIBUTO
S_APUR_CENTS
T_RECOLHER_CENTS
P_CASH_CENTS
E_DRE_CENTS
C_SALDO_CENTS
VERSAO_REGRA
```

Nesta spec:

```text
P_CASH_CENTS = None
E_DRE_CENTS = None
```

Não inferir caixa nem DRE.

---

# API mínima

Criar:

```text
src/accounting_sim/tax_cbs_2026.py
```

API esperada:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EffectiveCbs2026Rules:
    ...


@dataclass(frozen=True)
class Cbs2026Result:
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame


def validate_cbs_2026_admissibility(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> ValidationReport:
    ...


def select_effective_cbs_2026_rules(
    tax_context: TaxContext,
    scenario_id: str,
) -> EffectiveCbs2026Rules:
    ...


def calculate_cbs_2026_operations(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> pd.DataFrame:
    ...


def assess_cbs_2026(
    operation_results: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> pd.DataFrame:
    ...


def run_cbs_2026(
    events: pd.DataFrame,
    tax_context: TaxContext,
    scenario_id: str,
) -> Cbs2026Result:
    ...
```

`run_cbs_2026()` deve:

1. validar `TaxContext` pela Spec 08;
2. validar admissibilidade desta spec;
3. selecionar regras efetivas;
4. calcular resultados por operação;
5. calcular apuração;
6. devolver cópias independentes/determinísticas.

Se o contexto for inválido, levantar `SchemaValidationError` com mensagem legível a partir do `ValidationReport`.

---

# Helpers permitidos

Helpers pequenos locais são permitidos para:

- converter `ENTIDADE` longa em mapa tipado da entidade;
- converter `EVENTOS_FISCAIS` longa em mapa por `ID_EVENTO`;
- converter `FISCAL_PARAM.VALOR` conforme `TIPO_VALOR`;
- selecionar parâmetros vigentes;
- validar chaves obrigatórias.

Não promover esses helpers a framework genérico nesta spec.

---

# Arquivos de exemplo

Criar:

```text
data/examples/cbs_2026/events.csv
data/examples/cbs_2026/entity_profile.csv
data/examples/cbs_2026/fiscal_event_attributes.csv
data/examples/cbs_2026/tax_scenarios.csv
data/examples/cbs_2026/tax_parameters.csv
```

Os arquivos devem ser legíveis manualmente e compatíveis com os schemas existentes.

## Exemplo canônico mínimo

Usar pelo menos:

```text
Compra para revenda
VBC = 100000 cents
pCBS = 0.9%
vCBS = 900 cents

Venda
VBC = 200000 cents
pCBS = 0.9%
vCBS = 1800 cents
```

Resultado esperado:

```text
C_total = 900
D_total = 1800
S_APUR_CENTS = 900
T_NOMINAL_CENTS = 900
T_RECOLHER_CENTS = 0
C_SALDO_CENTS = 0
P_CASH_CENTS = None
E_DRE_CENTS = None
```

O exemplo deve usar `VL_EVENTO_CENTS` pelo menos em uma linha com valor diferente de `VBC_CENTS`, demonstrando que a base fiscal documental não é identificada automaticamente com o valor econômico do evento.

---

# Testes obrigatórios

Criar:

```text
tests/test_tax_cbs_2026.py
```

## Grupo A — `chi_t`

1. cenário canônico é admissível;
2. Simples/MEI é rejeitado;
3. regime de consumo diferente de CBS regular é rejeitado;
4. regime especial não vazio é rejeitado;
5. pessoa não PJ é rejeitada;
6. atividade diferente do recorte é rejeitada;
7. não contribuinte do ICMS é rejeitado para agosto;
8. compliance acessório ausente/false é rejeitado;
9. `DT_REFERENCIA_NORMATIVA != 2026-08-31` é rejeitada;
10. evento fiscal antes de 03/08/2026 é rejeitado;
11. evento fiscal depois de 31/08/2026 é rejeitado.

## Grupo B — seleção de regras

12. todas as chaves obrigatórias são selecionadas;
13. parâmetro ausente gera erro;
14. parâmetro duplicado vigente gera erro;
15. parâmetro fora da vigência não é usado;
16. parâmetros de versão normativa diferente não vazam para o cenário;
17. proveniência inválida continua sendo rejeitada pela Spec 08;
18. `split_payment_implemented=true` torna o recorte de crédito inadmissível;
19. `buyer_collection_implemented=true` torna o recorte de crédito inadmissível;
20. `VERSAO_REGRA` inconsistente entre parâmetros efetivos gera erro.

## Grupo C — documento fiscal

21. NF-e modelo diferente de 55 é rejeitada;
22. chave não formada por 44 dígitos é rejeitada;
23. chave duplicada é rejeitada;
24. protocolo vazio é rejeitado;
25. status diferente de `autorizado_nao_cancelado` é rejeitado;
26. `QTD_ITENS_DFE != 1` é rejeitado;
27. CST diferente da regra efetiva é rejeitado;
28. cClassTrib diferente da regra efetiva é rejeitado;
29. `VBC_CENTS <= 0` é rejeitado;
30. `PCBS_PERCENT` diferente de 0,9% é rejeitado;
31. `VCBS_CENTS < 0` é rejeitado;
32. compra sem `DESTINACAO_AQUISICAO=revenda` é rejeitada.

## Grupo D — cálculo documental

33. `vCBS` exatamente calculado é aceito;
34. diferença de +1 centavo é aceita;
35. diferença de -1 centavo é aceita quando não produz valor negativo;
36. diferença maior que 1 centavo é rejeitada;
37. o motor não depende de igualdade `VL_EVENTO_CENTS == VBC_CENTS`;
38. nenhuma política arbitrária de arredondamento é necessária para aceitar documento dentro da tolerância.

## Grupo E — operação

39. venda gera débito e crédito zero;
40. compra gera crédito e débito zero;
41. `BASE_CENTS` vem de `VBC_CENTS`;
42. `ALIQUOTA` vem de `FISCAL_PARAM`;
43. `VERSAO_REGRA` vem da regra efetiva;
44. eventos contábeis não fiscais não geram linhas de resultado;
45. ordem física dos DataFrames de entrada não altera o resultado ordenado.

## Grupo F — apuração

46. caso positivo: `D=1800`, `C=900` -> `S_APUR=900`;
47. caso positivo e compliance -> `T_RECOLHER=0`;
48. caso negativo produz `C_SALDO=max(-S,0)`;
49. `P_CASH_CENTS is None`;
50. `E_DRE_CENTS is None`;
51. uma única linha de apuração é produzida para o cenário;
52. execução repetida com mesmas entradas produz DataFrames equivalentes.

## Grupo G — regressão arquitetural

53. não alterar `EVENT_COLUMNS`;
54. não inserir lógica CBS em `events.py`, `posting.py`, `ledger.py`, `statements.py`, `account_mapping.py` ou `chart_of_accounts.py`;
55. `validate_tax_context()` da Spec 08 continua passando para contextos anteriores válidos;
56. schemas reservados `TAX_OPERATION_RESULT_COLUMNS` e `TAX_ASSESSMENT_RESULT_COLUMNS` permanecem exatamente iguais.

---

# Workbook

A Spec 09 **não modifica o workbook**.

As abas futuras já reservadas:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

continuam reservadas.

Motivo: esta spec fecha primeiro o operador e os DataFrames tributários; a materialização/execução multi-cenário pertence ao próximo bloco do Marco C.

Não alterar `WORKBOOK_SHEETS` nesta implementação.

---

# Passos de implementação

1. ler os Volumes I–III e a Spec 08 antes de editar código;
2. confirmar `main` atual e não assumir contagem de testes;
3. inspecionar `canonical.py` e `tax_context.py` para reutilizar schemas/tipos;
4. criar `tax_cbs_2026.py` sem tocar no motor contábil;
5. implementar `EffectiveCbs2026Rules`;
6. implementar seleção tipada de parâmetros vigentes;
7. implementar admissibilidade mínima;
8. implementar validação dos atributos fiscais do recorte;
9. implementar débito/crédito documental;
10. implementar resultado por operação;
11. implementar apuração mensal e regra transitória de recolhimento;
12. criar fixtures CSV canônicos;
13. criar testes focados;
14. corrigir apenas falhas relacionadas;
15. executar suíte completa uma única vez ao final.

---

# Política de testes

Seguir obrigatoriamente:

1. baseline completa no máximo uma vez antes da implementação, apenas se necessária;
2. durante a implementação, rodar somente `tests/test_tax_cbs_2026.py` e testes diretamente afetados da Spec 08;
3. ao fechar o bloco, rodar o subconjunto tributário relevante;
4. executar a suíte completa uma única vez ao final;
5. se a suíte final passar, não repeti-la;
6. se houver falha, executar primeiro apenas o teste que falhou;
7. voltar à suíte completa somente depois da correção final.

Não executar `python -m pytest -q` após cada pequena edição.

---

# Critérios de aceitação

A Spec 09 está concluída somente se:

- `chi_t` rejeita explicitamente tudo que está fora do recorte;
- `mathfrak E_t` seleciona regras exclusivamente de `FISCAL_PARAM` com vigência/proveniência;
- nenhuma alíquota/código normativo é hard-coded como fonte de verdade no motor;
- base fiscal é documental e distinta de `VL_EVENTO_CENTS`;
- cálculo documental respeita tolerância da NT sem inventar regra de arredondamento;
- débito da venda usa o `vCBS` documental validado;
- crédito da compra usa o `vCBS` documental validado e depende explicitamente da regra do art. 48;
- a conclusão operacional sobre as modalidades do art. 48 é limitada ao snapshot de 31/08/2026;
- `S_APUR_CENTS` pode ser diferente de zero enquanto `T_RECOLHER_CENTS=0` por causa da regra transitória;
- `P_CASH_CENTS` e `E_DRE_CENTS` permanecem `None`;
- estado fiscal anterior não é introduzido desnecessariamente;
- motor contábil existente permanece inalterado;
- testes focados passam;
- suíte completa passa uma única vez ao final;
- o relatório do Codex informa arquivos alterados, decisões locais, testes executados e eventuais limitações sem reinterpretar a legislação.

---

# Arquivos esperados

Criar:

```text
src/accounting_sim/tax_cbs_2026.py
tests/test_tax_cbs_2026.py

data/examples/cbs_2026/events.csv
data/examples/cbs_2026/entity_profile.csv
data/examples/cbs_2026/fiscal_event_attributes.csv
data/examples/cbs_2026/tax_scenarios.csv
data/examples/cbs_2026/tax_parameters.csv
```

Modificar somente se necessário:

```text
src/accounting_sim/__init__.py
```

Não modificar, salvo necessidade demonstrada e reportada:

```text
src/accounting_sim/events.py
src/accounting_sim/posting.py
src/accounting_sim/ledger.py
src/accounting_sim/statements.py
src/accounting_sim/account_mapping.py
src/accounting_sim/chart_of_accounts.py
src/accounting_sim/workbook.py
```

---

# Dependências para a Spec 10

Ao final, a Spec 09 deve deixar uma API pura e determinística do tipo:

```text
(events, tax_context, scenario_id)
    ->
Cbs2026Result
```

A Spec 10 poderá então iterar sobre diferentes cenários mantendo:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

sem duplicar a lógica CBS implementada aqui.
