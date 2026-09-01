# Spec 07 — Mapeamento para demonstrações, BP e DRE

**Status:** fechamento do Marco B  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–06 + Volumes I–III  
**Bloqueia:** specs 08–11

## Objetivo

Fechar o Marco B do projeto derivando, a partir do núcleo contábil já validado:

```text
b_t
    -> map_t^S
    -> BP_{t+1}
    -> DRE_t
    -> Wb_t
```

sem criar uma segunda fonte de verdade, sem introduzir lançamentos de encerramento e sem antecipar DFC, DVA ou tributação.

A entrega deve acrescentar:

1. `MAPEAMENTO_DF` como materialização normalizada de `map_t^S`;
2. uma DRE mínima derivada dos **movimentos do período**;
3. um BP mínimo derivado dos **saldos finais**;
4. tratamento explícito e apenas apresentacional do resultado corrente no patrimônio líquido;
5. reconciliação automática:
   `TOTAL_ATIVO = TOTAL_PASSIVO + TOTAL_PL`;
6. novas abas `MAPEAMENTO_DF`, `BP` e `DRE` no workbook;
7. testes que provem que BP/DRE continuam sendo objetos derivados.

O fechamento desta etapa é:

```text
P_t + u_t
    -> Lambda_t
    -> Dia_t / Raz_t
    -> b_t
    -> (BP_{t+1}, DRE_t)
    -> Wb_t
```

---

# Contexto canônico

## Source of truth

Antes de implementar, consultar integralmente:

```text
docs/volume_I/contabilidade_parametrizada.tex
docs/volume_II/contabilidade_parametrizada_volume_II.tex
docs/volume_III/contabilidade_parametrizada_volume_III.tex

specs/README_specs_plan.md
specs/00_mvp_scope.md
specs/01_canonical_model.md
specs/02_chart_of_accounts.md
specs/03_events.md
specs/04_posting_engine.md
specs/05_ledger_trial_balance.md
specs/06_excel_workbook.md
```

Política de precedência:

```text
semântica dos Volumes I–III
    >
contrato das specs
    >
implementação
```

Não resolver conflitos silenciosamente.

---

# Integridade canônica que esta spec deve preservar

## 1. BP é estoque; DRE é fluxo

O Volume I define:

```text
BP_t = pi_BP(x_t)
```

e descreve o BP como posição em um instante.

A DRE, por outro lado, organiza receitas e despesas reconhecidas durante `I_t`:

```text
L_t = R_t - K_t - E_t + O_t
```

Logo, nesta spec:

```text
BP_{t+1}
    <- saldos finais

DRE_t
    <- movimentos do período
```

Não calcular a DRE simplesmente a partir do saldo final de contas de resultado como regra geral.

No cenário atual, saldos iniciais são zero e os dois caminhos coincidem numericamente, mas a implementação deve preservar a distinção conceitual.

---

## 2. `G^S` permanece operador de classificação/agregação

O Volume I mantém:

```text
G^S
=
A^S o K^S o M^acct o R^acct
```

e, com a abertura de `Lambda_t`, a cadeia pode ser lida como:

```text
u_t
    -> Lambda_t
    -> K^S / A^S
    -> S_t
```

A Spec 07 implementa apenas a parte de **classificação e agregação** necessária para BP/DRE v1.

Não reexecutar reconhecimento ou mensuração dos eventos.

Não consultar `TIPO_EVENTO` para montar BP/DRE.

---

## 3. `map_t^S` é o objeto canônico do de-para

O Volume III define:

```text
map_t^S:
    C_t -> L^S union {null}
```

onde `L^S` é o conjunto de linhas/categorias da demonstração `S`.

A representação física nesta spec será:

```text
MAPEAMENTO_DF
```

e a representação Python será:

```text
statement_mapping
```

A função do mapping é:

```text
COD_CTA
    -> DEMONSTRACAO
    -> COD_LINHA
```

Não confundir com:

```text
MAPEAMENTO_CONTAS
PAPEL_CONTABIL -> COD_CTA
```

da Spec 06.

A cadeia completa passa a ser:

```text
papel econômico
    -> MAPEAMENTO_CONTAS
    -> COD_CTA
    -> MAPEAMENTO_DF
    -> COD_LINHA
    -> BP/DRE
```

---

## 4. Balancete não substitui eventos para tributação

O Volume II demonstra que pode ocorrer:

```text
A_acct(u_t) = A_acct(u_t')
```

e simultaneamente:

```text
H_tax(u_t) != H_tax(u_t')
```

Portanto, a adição de BP/DRE não autoriza descartar:

```text
EVENTOS
DOC_REF
ID_ORIGEM
VINCULO_EVENTO_LCTO
```

A camada tributária permanece fora desta spec.

---

## 5. Demonstrações continuam derivadas

O Volume III fixa:

```text
editar entradas
    -> regenerar núcleo
    -> recalcular saídas
```

e classifica demonstrações como saídas derivadas.

Portanto:

```text
BP
DRE
```

não são fonte de verdade.

Alterações manuais nessas abas devem ser descartadas na próxima regeneração.

---

# Decisão arquitetural 1 — `MAPEAMENTO_DF` e `COD_DF`

## Situação herdada da Spec 02

`PLANO_CONTAS` já contém:

```text
COD_DF
```

A Spec 02 o reservou explicitamente como chave textual para a futura Spec 07.

O Volume III, entretanto, também prevê uma tabela separada:

```text
MAPEAMENTO_DF
```

como representação física de `map_t^S`.

Se ambos fossem tratados como entradas independentes, teríamos duas fontes de verdade.

Isso é proibido nesta spec.

---

## Regra de autoridade a partir da Spec 07

A representação normalizada e autoritativa de `map_t^S` passa a ser:

```text
MAPEAMENTO_DF
```

`PLANO_CONTAS.COD_DF` permanece no schema por compatibilidade com:

- Spec 02;
- template atual;
- inspeção humana;
- persistência do plano já implementada.

Mas, a partir desta spec, `COD_DF` deve ser tratado no workbook como:

```text
espelho denormalizado de MAPEAMENTO_DF
```

e não como uma segunda entrada independente.

### Regra operacional

```text
MAPEAMENTO_DF
    -> sincroniza
PLANO_CONTAS.COD_DF
```

Nunca o contrário durante regeneração de workbook.

### Compatibilidade Python

Para chamadas Python antigas que ainda não forneçam `statement_mapping`, é permitido construir o mapping default a partir de `PLANO_CONTAS.COD_DF`.

Esse comportamento é apenas fallback de compatibilidade.

No caminho do workbook:

```text
MAPEAMENTO_DF é sempre explícito e autoritativo.
```

### Edição manual de `COD_DF`

Se o usuário alterar somente:

```text
PLANO_CONTAS.COD_DF
```

mas não alterar `MAPEAMENTO_DF`, a mudança deve:

1. não alterar BP/DRE;
2. não alterar a classificação contábil;
3. ser sobrescrita na regeneração pelo valor autoritativo de `MAPEAMENTO_DF`.

O README do workbook deve explicar que `COD_DF` é espelho.

---

# Decisão arquitetural 2 — resultado corrente e BP

## Problema

O balancete do Marco A mantém contas de resultado abertas durante o período.

Não existem lançamentos de encerramento.

No caso canônico:

```text
Receita = 50000 C
CMV     = 20000 D
```

e:

```text
L_t = 30000
```

Para apresentar o BP final:

```text
Ativos = 130000
Capital = 100000
```

é necessário que o resultado corrente componha economicamente o patrimônio líquido:

```text
PL econômico
=
Capital
+ Resultados Acumulados
+ Resultado do Período
```

---

## Solução do MVP

Criar no BP uma linha derivada:

```text
BP_RESULTADO_PERIODO
```

com:

```text
BP_RESULTADO_PERIODO = DRE_RESULTADO_PERIODO
```

Essa linha:

- não é uma conta;
- não pertence a `PLANO_CONTAS`;
- não pode receber partida;
- não gera lançamento;
- não altera o balancete;
- não encerra contas de resultado;
- existe somente para apresentação do BP.

Assim:

```text
TOTAL_ATIVO
=
TOTAL_PASSIVO
+ PATRIMONIO_LIQUIDO
```

sem modificar `Lambda_t`.

---

## Proibição explícita

Não criar nesta spec:

```text
D Resultados do Período
C Lucros Acumulados
```

ou qualquer outro lançamento de encerramento.

O número de:

```text
LANCAMENTOS
PARTIDAS
```

deve permanecer idêntico antes e depois da geração das demonstrações.

---

# Decisão arquitetural 3 — sinais

## Saldo assinado do balancete

A convenção herdada é:

```text
saldo assinado = debitos - creditos
```

Logo:

```text
D -> positivo
C -> negativo
```

---

## BP

Para contas de Ativo (`COD_NAT = 01`):

```text
contribuicao_BP
=
saldo_assinado_final
```

Isso preserva naturalmente contra-ativos:

```text
Depreciação Acumulada
saldo C
-> contribuição negativa no ativo.
```

Para Passivo e Patrimônio Líquido (`COD_NAT in {02, 03}`):

```text
contribuicao_BP
=
-saldo_assinado_final
```

Assim saldos credores usuais aparecem positivos.

Não usar `NAT_SALDO_NORMAL` para forçar artificialmente o sinal efetivo.

---

## DRE

A DRE deve usar movimentos do período.

Para qualquer conta de resultado (`COD_NAT = 04`):

```text
contribuicao_DRE
=
VL_CRED_CENTS
- VL_DEB_CENTS
```

Consequências:

```text
receita credora
    -> valor positivo

custo/despesa devedora
    -> valor negativo
```

Então:

```text
L_t
=
sum(contribuicao_DRE)
```

no conjunto completo das contas de resultado do MVP.

Essa convenção implementa diretamente:

```text
L_t = R_t - K_t - E_t + O_t
```

com `O_t = 0` na política v1, salvo linhas que sejam adicionadas explicitamente em spec posterior.

---

# Escopo

Implementar nesta spec:

1. `statement_mapping` como `DataFrame`;
2. `MAPEAMENTO_DF` no workbook;
3. catálogo fixo de linhas BP v1;
4. catálogo fixo de linhas DRE v1;
5. validação do mapping;
6. sincronização `MAPEAMENTO_DF -> PLANO_CONTAS.COD_DF`;
7. `build_income_statement()`;
8. `build_balance_sheet()`;
9. `build_financial_statements()`;
10. `validate_financial_statements()`;
11. linha derivada `BP_RESULTADO_PERIODO`;
12. identidade patrimonial;
13. abas `BP` e `DRE`;
14. round-trip de `MAPEAMENTO_DF`;
15. descarte de adulterações manuais em BP/DRE;
16. extensão de `VALIDACOES`;
17. extensão de `PROVENIENCIA`;
18. testes do caso canônico.

---

# Fora de escopo

Não implementar:

- DFC;
- DVA;
- DMPL;
- DRA;
- notas explicativas;
- fechamento/encerramento das contas de resultado;
- lançamentos de fechamento;
- imposto de renda;
- contribuição social;
- IBS;
- CBS;
- PIS/Cofins;
- ICMS;
- ISS;
- qualquer cálculo tributário;
- `FISCAL_*`;
- consolidação;
- múltiplas entidades;
- múltiplos períodos;
- saldos iniciais importados;
- comparativos entre exercícios;
- reclassificações complexas;
- equivalência patrimonial;
- reservas detalhadas;
- dividendos;
- outros resultados abrangentes;
- demonstração completa conforme todos os CPCs;
- plano referencial;
- engine genérico de demonstrações;
- fórmulas Excel como fonte de verdade;
- macros/VBA;
- geração aleatória.

A Spec 07 implementa uma **DRE e um BP mínimos para o arquétipo comercial v1**, não demonstrações societárias completas.

---

# Entradas lógicas

A geração de demonstrações recebe:

```python
trial_balance: pd.DataFrame
chart_of_accounts: pd.DataFrame
statement_mapping: pd.DataFrame
period: AccountingPeriod
```

Pré-condições:

```text
validate_chart_of_accounts(...).ok is True
validate_ledger_trial_balance(...).ok is True
validate_statement_mapping(...).ok is True
```

Não receber `EVENTOS` como argumento econômico para calcular BP/DRE.

A semântica dos eventos já foi absorvida em:

```text
Lambda_t -> b_t
```

---

# Saídas lógicas

Criar preferencialmente:

```python
@dataclass(frozen=True)
class FinancialStatements:
    balance_sheet: pd.DataFrame
    income_statement: pd.DataFrame
```

Saídas:

```text
balance_sheet
income_statement
```

Correspondência:

```text
balance_sheet     <-> BP_{t+1}
income_statement  <-> DRE_t
```

---

# Schema — `MAPEAMENTO_DF`

Ordem canônica:

```text
COD_CTA
DEMONSTRACAO
COD_LINHA
```

Definir:

```python
STATEMENT_MAPPING_COLUMNS = (
    "COD_CTA",
    "DEMONSTRACAO",
    "COD_LINHA",
)
```

Tipos:

| Coluna | Tipo | Regra |
|---|---|---|
| `COD_CTA` | `str` | FK para conta analítica ativa |
| `DEMONSTRACAO` | enum `BP/DRE` | compatível com `COD_NAT` |
| `COD_LINHA` | `str` | linha detalhe válida da demonstração |

---

# Invariantes — `MAPEAMENTO_DF`

## DF1 — conta única

No MVP:

```text
COD_CTA
```

é único em `MAPEAMENTO_DF`.

Cada conta analítica ativa alimenta exatamente uma demonstração primária:

```text
COD_NAT 01,02,03 -> BP
COD_NAT 04       -> DRE
```

---

## DF2 — cobertura completa

Toda conta:

```text
IND_CTA = A
ATIVA = True
```

deve aparecer exatamente uma vez.

Não permitir conta ativa analítica sem mapping.

---

## DF3 — conta válida

`COD_CTA` deve:

- existir;
- ser analítica;
- estar ativa.

---

## DF4 — demonstração válida

Valores permitidos:

```text
BP
DRE
```

---

## DF5 — natureza compatível

```text
COD_NAT in {01,02,03}
    -> DEMONSTRACAO = BP

COD_NAT = 04
    -> DEMONSTRACAO = DRE
```

Não mapear conta de resultado diretamente para BP.

O resultado corrente entra no BP apenas por `BP_RESULTADO_PERIODO`.

---

## DF6 — linha válida

`COD_LINHA` deve existir no catálogo da demonstração.

Somente linhas com:

```text
TIPO_LINHA = DETALHE
```

podem receber contas.

Não mapear contas para:

```text
SUBTOTAL
TOTAL
DERIVADA
CABECALHO
```

---

## DF7 — muitos-para-um permitido

Várias contas podem alimentar a mesma linha.

Exemplo futuro admissível:

```text
duas contas bancárias
    -> BP_BANCOS
```

Portanto `COD_LINHA` não é chave única.

---

## DF8 — compatibilidade de natureza/saldo da linha

Cada linha detalhe possui expectativas mínimas de:

```text
COD_NAT
NAT_SALDO_NORMAL
```

O mapping deve rejeitar incompatibilidades estruturais.

Exemplo:

```text
conta de Receita
    -> DRE_CMV
```

deve ser rejeitada na política v1 porque:

```text
Receita: normal C
CMV:     normal D
```

---

## DF9 — linha derivada sem conta

`BP_RESULTADO_PERIODO`:

- não pode receber `COD_CTA`;
- não pode constar como `COD_DF` autoritativo de uma conta;
- é alimentada somente por `DRE_RESULTADO_PERIODO`.

---

# Catálogo BP v1

Implementar em código como estrutura fixa e simples.

Não criar banco/configuração genérica de layouts.

Colunas conceituais da definição:

```text
ORDEM
COD_LINHA
NIVEL
TIPO_LINHA
LINHA
```

Tipos:

```text
DETALHE
SUBTOTAL
TOTAL
DERIVADA
```

Catálogo mínimo:

| ORDEM | COD_LINHA | NIVEL | TIPO | LINHA |
|---:|---|---:|---|---|
| 10 | `BP_ATIVO` | 1 | TOTAL | Ativo |
| 20 | `BP_ATIVO_CIRCULANTE` | 2 | SUBTOTAL | Ativo Circulante |
| 30 | `BP_CAIXA` | 3 | DETALHE | Caixa |
| 40 | `BP_BANCOS` | 3 | DETALHE | Bancos Conta Movimento |
| 50 | `BP_CLIENTES` | 3 | DETALHE | Clientes |
| 60 | `BP_ESTOQUES` | 3 | DETALHE | Estoques |
| 70 | `BP_TRIBUTOS_RECUPERAR` | 3 | DETALHE | Tributos a Recuperar |
| 80 | `BP_ATIVO_NAO_CIRCULANTE` | 2 | SUBTOTAL | Ativo Não Circulante |
| 90 | `BP_IMOBILIZADO` | 3 | DETALHE | Imobilizado |
| 100 | `BP_DEPRECIACAO_ACUM` | 3 | DETALHE | (-) Depreciação Acumulada |
| 110 | `BP_PASSIVO` | 1 | TOTAL | Passivo |
| 120 | `BP_PASSIVO_CIRCULANTE` | 2 | SUBTOTAL | Passivo Circulante |
| 130 | `BP_FORNECEDORES` | 3 | DETALHE | Fornecedores |
| 140 | `BP_OBRIG_TRAB` | 3 | DETALHE | Obrigações Trabalhistas |
| 150 | `BP_OBRIG_TRIB` | 3 | DETALHE | Obrigações Tributárias |
| 160 | `BP_PASSIVO_NAO_CIRCULANTE` | 2 | SUBTOTAL | Passivo Não Circulante |
| 170 | `BP_EMPRESTIMOS` | 3 | DETALHE | Empréstimos e Financiamentos |
| 180 | `BP_PATRIMONIO_LIQUIDO` | 1 | SUBTOTAL | Patrimônio Líquido |
| 190 | `BP_CAPITAL` | 2 | DETALHE | Capital Social |
| 200 | `BP_RESULTADOS_ACUM` | 2 | DETALHE | Resultados Acumulados |
| 210 | `BP_RESULTADO_PERIODO` | 2 | DERIVADA | Resultado do Período |
| 220 | `BP_TOTAL_PASSIVO_PL` | 1 | TOTAL | Total do Passivo e Patrimônio Líquido |

---

# Metadados semânticos das linhas BP detalhe

Expectativas:

| COD_LINHA | COD_NAT | saldo normal |
|---|---|---|
| `BP_CAIXA` | `01` | `D` |
| `BP_BANCOS` | `01` | `D` |
| `BP_CLIENTES` | `01` | `D` |
| `BP_ESTOQUES` | `01` | `D` |
| `BP_TRIBUTOS_RECUPERAR` | `01` | `D` |
| `BP_IMOBILIZADO` | `01` | `D` |
| `BP_DEPRECIACAO_ACUM` | `01` | `C` |
| `BP_FORNECEDORES` | `02` | `C` |
| `BP_OBRIG_TRAB` | `02` | `C` |
| `BP_OBRIG_TRIB` | `02` | `C` |
| `BP_EMPRESTIMOS` | `02` | `C` |
| `BP_CAPITAL` | `03` | `C` |
| `BP_RESULTADOS_ACUM` | `03` | `C` |

---

# Agregações BP

Definir explicitamente:

```text
BP_ATIVO_CIRCULANTE
=
BP_CAIXA
+ BP_BANCOS
+ BP_CLIENTES
+ BP_ESTOQUES
+ BP_TRIBUTOS_RECUPERAR
```

```text
BP_ATIVO_NAO_CIRCULANTE
=
BP_IMOBILIZADO
+ BP_DEPRECIACAO_ACUM
```

`BP_DEPRECIACAO_ACUM` será normalmente negativo.

```text
BP_ATIVO
=
BP_ATIVO_CIRCULANTE
+ BP_ATIVO_NAO_CIRCULANTE
```

```text
BP_PASSIVO_CIRCULANTE
=
BP_FORNECEDORES
+ BP_OBRIG_TRAB
+ BP_OBRIG_TRIB
```

```text
BP_PASSIVO_NAO_CIRCULANTE
=
BP_EMPRESTIMOS
```

```text
BP_PASSIVO
=
BP_PASSIVO_CIRCULANTE
+ BP_PASSIVO_NAO_CIRCULANTE
```

```text
BP_PATRIMONIO_LIQUIDO
=
BP_CAPITAL
+ BP_RESULTADOS_ACUM
+ BP_RESULTADO_PERIODO
```

```text
BP_TOTAL_PASSIVO_PL
=
BP_PASSIVO
+ BP_PATRIMONIO_LIQUIDO
```

Invariante:

```text
BP_ATIVO
=
BP_TOTAL_PASSIVO_PL
```

em centavos exatos.

---

# Catálogo DRE v1

| ORDEM | COD_LINHA | NIVEL | TIPO | LINHA |
|---:|---|---:|---|---|
| 10 | `DRE_RECEITA_VENDAS` | 1 | DETALHE | Receita de Vendas |
| 20 | `DRE_RECEITA_LIQUIDA` | 1 | SUBTOTAL | Receita Líquida |
| 30 | `DRE_CMV` | 1 | DETALHE | (-) Custo das Mercadorias Vendidas |
| 40 | `DRE_RESULTADO_BRUTO` | 1 | SUBTOTAL | Resultado Bruto |
| 50 | `DRE_DESP_SALARIOS` | 2 | DETALHE | (-) Salários e Encargos |
| 60 | `DRE_DESP_ALUGUEL` | 2 | DETALHE | (-) Aluguéis |
| 70 | `DRE_DESP_UTILIDADES` | 2 | DETALHE | (-) Energia e Utilidades |
| 80 | `DRE_DESP_DEPRECIACAO` | 2 | DETALHE | (-) Depreciação |
| 90 | `DRE_DESP_OPERACIONAIS` | 1 | SUBTOTAL | Despesas Operacionais |
| 100 | `DRE_DESP_FINANCEIRA` | 1 | DETALHE | (-) Despesas Financeiras |
| 110 | `DRE_RESULTADO_PERIODO` | 1 | TOTAL | Resultado do Período |

---

# Metadados semânticos das linhas DRE detalhe

| COD_LINHA | COD_NAT | saldo normal |
|---|---|---|
| `DRE_RECEITA_VENDAS` | `04` | `C` |
| `DRE_CMV` | `04` | `D` |
| `DRE_DESP_SALARIOS` | `04` | `D` |
| `DRE_DESP_ALUGUEL` | `04` | `D` |
| `DRE_DESP_UTILIDADES` | `04` | `D` |
| `DRE_DESP_DEPRECIACAO` | `04` | `D` |
| `DRE_DESP_FINANCEIRA` | `04` | `D` |

---

# Agregações DRE

Detalhes recebem:

```text
VL_CENTS
=
VL_CRED_CENTS
- VL_DEB_CENTS
```

agregado das contas mapeadas para a linha.

Então:

```text
DRE_RECEITA_LIQUIDA
=
DRE_RECEITA_VENDAS
```

no MVP atual, pois ainda não existem deduções de receita explicitadas.

```text
DRE_RESULTADO_BRUTO
=
DRE_RECEITA_LIQUIDA
+ DRE_CMV
```

como `DRE_CMV` já é negativo.

```text
DRE_DESP_OPERACIONAIS
=
DRE_DESP_SALARIOS
+ DRE_DESP_ALUGUEL
+ DRE_DESP_UTILIDADES
+ DRE_DESP_DEPRECIACAO
```

```text
DRE_RESULTADO_PERIODO
=
DRE_RESULTADO_BRUTO
+ DRE_DESP_OPERACIONAIS
+ DRE_DESP_FINANCEIRA
```

Assim:

```text
L_t
=
DRE_RESULTADO_PERIODO
```

---

# Schema Python — BP

Definir:

```python
BALANCE_SHEET_COLUMNS = (
    "DT_REF",
    "ORDEM",
    "COD_LINHA",
    "NIVEL",
    "TIPO_LINHA",
    "LINHA",
    "VL_CENTS",
)
```

Tipos:

| Campo | Tipo |
|---|---|
| `DT_REF` | `date` |
| `ORDEM` | `int` |
| `COD_LINHA` | `str` |
| `NIVEL` | `int` |
| `TIPO_LINHA` | `str` |
| `LINHA` | `str` |
| `VL_CENTS` | `int` |

`DT_REF`:

```text
period.end_date
```

---

# Schema Python — DRE

Definir:

```python
INCOME_STATEMENT_COLUMNS = (
    "DT_INI",
    "DT_FIN",
    "ORDEM",
    "COD_LINHA",
    "NIVEL",
    "TIPO_LINHA",
    "LINHA",
    "VL_CENTS",
)
```

Tipos:

| Campo | Tipo |
|---|---|
| `DT_INI` | `date` |
| `DT_FIN` | `date` |
| `ORDEM` | `int` |
| `COD_LINHA` | `str` |
| `NIVEL` | `int` |
| `TIPO_LINHA` | `str` |
| `LINHA` | `str` |
| `VL_CENTS` | `int` |

---

# API mínima

Criar:

```text
src/accounting_sim/statements.py
```

API recomendada:

```python
def build_default_statement_mapping(
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    ...
```

Fallback a partir de `PLANO_CONTAS.COD_DF`.

```python
def validate_statement_mapping(
    statement_mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def synchronize_chart_statement_codes(
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
) -> pd.DataFrame:
    ...
```

Essa função:

- retorna cópia;
- não modifica input in-place;
- preenche `COD_DF` a partir de `MAPEAMENTO_DF`.

```python
def build_income_statement(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
    period: AccountingPeriod,
) -> pd.DataFrame:
    ...
```

```python
def build_balance_sheet(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
    income_statement: pd.DataFrame,
    period: AccountingPeriod,
) -> pd.DataFrame:
    ...
```

```python
@dataclass(frozen=True)
class FinancialStatements:
    balance_sheet: pd.DataFrame
    income_statement: pd.DataFrame
```

```python
def build_financial_statements(
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
    period: AccountingPeriod,
) -> FinancialStatements:
    ...
```

```python
def validate_financial_statements(
    statements: FinancialStatements,
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    statement_mapping: pd.DataFrame,
    period: AccountingPeriod,
) -> ValidationReport:
    ...
```

Não criar uma classe genérica `StatementEngine`.

---

# Construção da DRE — algoritmo mínimo

1. validar mapping;
2. selecionar contas:
   ```text
   COD_NAT = 04
   ```
3. fazer join:
   ```text
   BALANCETE
       + PLANO_CONTAS
       + MAPEAMENTO_DF
   ```
4. para cada conta:
   ```text
   contribution_cents
   =
   VL_CRED_CENTS - VL_DEB_CENTS
   ```
5. agrupar por `COD_LINHA`;
6. preencher linhas detalhe sem movimento com zero;
7. calcular subtotais;
8. calcular `DRE_RESULTADO_PERIODO`;
9. produzir linhas na ordem fixa;
10. validar.

Não usar:

```text
VL_SLD_FIN_CENTS
```

como fonte primária da DRE.

---

# Construção do BP — algoritmo mínimo

1. validar mapping;
2. selecionar contas:
   ```text
   COD_NAT in {01,02,03}
   ```
3. reconstruir saldo final assinado:
   ```text
   if IND_DC_FIN == D:
       signed = +VL_SLD_FIN_CENTS
   else:
       signed = -VL_SLD_FIN_CENTS
   ```
4. transformar em contribuição:
   ```text
   COD_NAT = 01 -> +signed
   COD_NAT in {02,03} -> -signed
   ```
5. agrupar por `COD_LINHA`;
6. preencher linhas detalhe sem saldo com zero;
7. obter:
   ```text
   BP_RESULTADO_PERIODO
   =
   DRE_RESULTADO_PERIODO
   ```
8. calcular subtotais;
9. verificar identidade patrimonial;
10. produzir linhas na ordem fixa.

---

# Identidade patrimonial e prova estrutural do MVP

Com saldo assinado devedor-positivo, defina:

```text
A_signed  = soma das contas COD_NAT=01
P_signed  = soma das contas COD_NAT=02
PL_signed = soma das contas COD_NAT=03
R_signed  = soma das contas COD_NAT=04
```

Como o balancete deriva de partidas dobradas:

```text
A_signed + P_signed + PL_signed + R_signed = 0
```

No BP:

```text
Ativo = A_signed
Passivo = -P_signed
PL_contabil = -PL_signed
```

No cenário do MVP, com contas de resultado inicialmente zeradas:

```text
L_t = -R_signed
```

Logo:

```text
Ativo
=
Passivo
+ PL_contabil
+ L_t
```

Portanto, a linha:

```text
BP_RESULTADO_PERIODO = L_t
```

é a ponte de apresentação que fecha:

```text
A = P + PL
```

sem necessidade de lançar encerramento.

Implementar essa identidade como teste, não apenas como comentário.

---

# Invariantes das demonstrações

## S1 — BP usa estoque

Valores detalhe do BP são derivados de:

```text
VL_SLD_FIN_CENTS
IND_DC_FIN
```

Não dos movimentos isolados.

---

## S2 — DRE usa fluxo

Valores detalhe da DRE são derivados de:

```text
VL_DEB_CENTS
VL_CRED_CENTS
```

Não de `VL_SLD_FIN_CENTS`.

---

## S3 — resultado canônico

```text
DRE_RESULTADO_PERIODO
=
sum(
    VL_CRED_CENTS - VL_DEB_CENTS
    para contas COD_NAT=04
)
```

desde que todas as contas de resultado estejam mapeadas.

---

## S4 — ponte BP/DRE

```text
BP_RESULTADO_PERIODO
=
DRE_RESULTADO_PERIODO
```

exatamente em centavos.

---

## S5 — identidade patrimonial

```text
BP_ATIVO
=
BP_TOTAL_PASSIVO_PL
```

sem tolerância de `float`.

---

## S6 — nenhuma mutação da escrituração

Gerar demonstrações não pode:

- criar lançamento;
- excluir lançamento;
- criar partida;
- alterar partida;
- alterar balancete;
- alterar Razão.

---

## S7 — linha derivada não é conta

```text
BP_RESULTADO_PERIODO
```

não pode aparecer em:

```text
PLANO_CONTAS.COD_CTA
PARTIDAS.COD_CTA
```

por causa da geração de demonstrações.

---

## S8 — mapping é classificação, não escrituração

Alterar `MAPEAMENTO_DF` pode alterar a linha de apresentação de uma conta, mas nunca:

- débito/crédito;
- `VL_DC_CENTS`;
- `NUM_LCTO`;
- saldo do Razão;
- saldo do balancete.

---

## S9 — contas sem movimento

Linhas detalhe definidas no catálogo aparecem com zero mesmo quando nenhuma conta mapeada teve movimento/saldo.

---

## S10 — determinismo

Mesmas entradas produzem BP/DRE idênticos e na mesma ordem.

---

## S11 — centavos

Todos os cálculos Python de demonstrações usam:

```text
int cents
```

---

## S12 — DFC/DVA ausentes

Não produzir objetos ou abas:

```text
DFC
DVA
```

---

# Caso canônico do Volume III

Eventos:

```text
aporte de capital      100000
compra à vista          30000
venda a prazo           50000  custo 20000
recebimento cliente     30000
```

O núcleo continua produzindo:

```text
Caixa                   100000 D
Clientes                  20000 D
Estoques                  10000 D
Capital Social           100000 C
Receita de Vendas         50000 C
CMV                        20000 D
```

---

## DRE esperada

Detalhes:

```text
DRE_RECEITA_VENDAS       +50000
DRE_CMV                  -20000
```

Demais despesas:

```text
0
```

Logo:

```text
DRE_RECEITA_LIQUIDA       50000
DRE_RESULTADO_BRUTO       30000
DRE_DESP_OPERACIONAIS         0
DRE_DESP_FINANCEIRA           0
DRE_RESULTADO_PERIODO     30000
```

Em centavos:

```text
DRE_RESULTADO_PERIODO = 3000000
```

---

## BP esperado

Ativo:

```text
Caixa       100000
Clientes     20000
Estoques     10000
```

Logo:

```text
BP_ATIVO_CIRCULANTE = 130000
BP_ATIVO             = 130000
```

Passivo:

```text
0
```

Patrimônio líquido:

```text
Capital Social          100000
Resultados Acumulados        0
Resultado do Período     30000
```

Logo:

```text
BP_PATRIMONIO_LIQUIDO = 130000
BP_TOTAL_PASSIVO_PL    = 130000
```

Identidade:

```text
130000 = 130000
```

Em centavos:

```text
BP_ATIVO            = 13000000
BP_TOTAL_PASSIVO_PL = 13000000
```

---

# Teste adicional — perda do período

Criar cenário simples com:

```text
receita = 10000
despesas = 15000
```

Então:

```text
DRE_RESULTADO_PERIODO = -5000
```

e:

```text
BP_RESULTADO_PERIODO = -5000
```

O resultado negativo deve reduzir o patrimônio líquido sem criar lançamentos de encerramento.

---

# Teste adicional — DRE é fluxo

Criar um `trial_balance` sintético de teste em que uma conta de resultado possua:

```text
VL_SLD_INI_CENTS != 0
```

e movimento do período conhecido.

Mesmo que o cenário operacional atual use saldo inicial zero, `build_income_statement()` deve usar apenas:

```text
VL_DEB_CENTS
VL_CRED_CENTS
```

para a DRE.

Esse teste protege a distinção estoque/fluxo para extensões futuras.

---

# Teste adicional — BP é estoque

Criar `trial_balance` de teste com uma conta patrimonial contendo:

```text
saldo inicial != 0
movimento no período != 0
```

O BP deve usar:

```text
VL_SLD_FIN_CENTS
IND_DC_FIN
```

e não apenas o movimento.

---

# Workbook — novas abas

A partir da Spec 07, a ordem canônica passa a ser:

```text
README
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
MAPEAMENTO_DF
BP
DRE
VALIDACOES
PROVENIENCIA
```

Não adicionar:

```text
DFC
DVA
ENTIDADE
FISCAL_*
```

---

# Classes das novas abas

## `MAPEAMENTO_DF`

Classe:

```text
entrada/configuração
```

É a quinta fonte de entrada do workbook.

## `BP`

Classe:

```text
saída derivada
```

## `DRE`

Classe:

```text
saída derivada
```

---

# Fontes de verdade do workbook a partir da Spec 07

Ler somente:

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
MAPEAMENTO_DF
```

com a ressalva:

```text
PLANO_CONTAS.COD_DF
```

é espelho de `MAPEAMENTO_DF`.

As seguintes abas nunca são lidas como entradas:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
BP
DRE
VALIDACOES
PROVENIENCIA
```

---

# Schema físico — `MAPEAMENTO_DF`

Igual ao lógico:

```text
COD_CTA
DEMONSTRACAO
COD_LINHA
```

Tabela Excel:

```text
tbl_MAPEAMENTO_DF
```

---

# Schema físico — `BP`

Converter:

```text
VL_CENTS -> VL
```

Schema:

```text
DT_REF
ORDEM
COD_LINHA
NIVEL
TIPO_LINHA
LINHA
VL
```

Tabela:

```text
tbl_BP
```

`VL` em BRL com duas casas decimais.

---

# Schema físico — `DRE`

Converter:

```text
VL_CENTS -> VL
```

Schema:

```text
DT_INI
DT_FIN
ORDEM
COD_LINHA
NIVEL
TIPO_LINHA
LINHA
VL
```

Tabela:

```text
tbl_DRE
```

---

# Workbook — `README`

Atualizar para explicar:

```text
ABAS EDITÁVEIS:
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
MAPEAMENTO_DF
```

com observação explícita:

```text
PLANO_CONTAS.COD_DF é espelho de MAPEAMENTO_DF.
Edite o de-para em MAPEAMENTO_DF.
```

Abas geradas:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
BP
DRE
VALIDACOES
PROVENIENCIA
```

---

# Workbook — `VALIDACOES`

Adicionar etapas:

```text
MAPEAMENTO_DF
DEMONSTRACOES
```

A lista mínima passa a conter:

```text
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
LANCAMENTOS_PARTIDAS
RAZAO_BALANCETE
MAPEAMENTO_DF
DEMONSTRACOES
```

Um workbook canônico aceito deve apresentar apenas:

```text
OK = TRUE
```

---

# Workbook — `PROVENIENCIA`

Registrar adicionalmente:

```text
financial_statement_spec_version = spec_07_financial_statements_v1
statement_mapping_source
```

Exemplo:

```text
statement_mapping_source = MAPEAMENTO_DF
```

Não adicionar timestamp obrigatório.

---

# Workbook — versão

O schema físico do workbook mudou.

Atualizar a versão para:

```text
spec_07_excel_workbook_v1
```

Manter separadamente:

```text
FINANCIAL_STATEMENT_SPEC_VERSION
=
spec_07_financial_statements_v1
```

A alteração de versão é esperada e não deve ser tratada como quebra indevida da Spec 06.

---

# `WorkbookInputs`

Estender:

```python
@dataclass(frozen=True)
class WorkbookInputs:
    simulation_config: SimulationConfig
    chart_of_accounts: pd.DataFrame
    account_role_mapping: pd.DataFrame
    events: pd.DataFrame
    statement_mapping: pd.DataFrame | None = None
```

## Compatibilidade

Se:

```text
statement_mapping is None
```

em chamada Python direta:

```text
build_default_statement_mapping(chart_of_accounts)
```

pode ser usado como fallback.

Ao carregar workbook Spec 07:

```text
statement_mapping nunca é None
```

porque `MAPEAMENTO_DF` é aba obrigatória.

---

# Regeneração do workbook

Fluxo obrigatório:

```text
1. ler CONFIG
2. ler PLANO_CONTAS
3. ler MAPEAMENTO_CONTAS
4. ler EVENTOS
5. ler MAPEAMENTO_DF
6. sincronizar MAPEAMENTO_DF -> PLANO_CONTAS.COD_DF
7. validar entradas
8. post_events()
9. build_journal()
10. build_ledger()
11. build_trial_balance()
12. build_financial_statements()
13. validate_financial_statements()
14. construir VALIDACOES
15. construir PROVENIENCIA
16. escrever workbook completo
```

Não ler BP/DRE existentes.

---

# Teste de autoridade do mapping

## Caso A — edição em `MAPEAMENTO_DF`

Usar uma conta de despesa operacional e redirecioná-la entre duas linhas semanticamente compatíveis.

Exemplo:

```text
despesa de aluguel:
DRE_DESP_ALUGUEL
    ->
DRE_DESP_UTILIDADES
```

desde que a conta continue `COD_NAT=04`, saldo normal D.

Após regeneração:

- `LANCAMENTOS` idênticos;
- `PARTIDAS` idênticas;
- `RAZAO` idêntico;
- `BALANCETE` idêntico;
- DRE muda apenas a classificação da despesa;
- resultado final permanece idêntico.

Esse teste demonstra:

```text
map_t^S
```

como operador de classificação, não de escrituração.

---

## Caso B — edição somente em `PLANO_CONTAS.COD_DF`

Alterar manualmente `COD_DF` de uma conta no Excel sem alterar `MAPEAMENTO_DF`.

Após regeneração:

- BP/DRE não mudam;
- `COD_DF` volta ao valor de `MAPEAMENTO_DF`.

Isso elimina dupla fonte de verdade.

---

# Teste de adulteração das demonstrações

1. gerar workbook;
2. alterar manualmente um valor em `BP`;
3. alterar manualmente um valor em `DRE`;
4. salvar;
5. regenerar;
6. verificar que os valores corretos são restaurados.

Demonstrações não são entradas.

---

# Validações das demonstrações

## VDF1 — schemas

BP/DRE possuem exatamente as colunas canônicas.

## VDF2 — linhas

Todos os códigos do catálogo aparecem exatamente uma vez.

## VDF3 — ordem

`ORDEM` é crescente e determinística.

## VDF4 — inteiros

`VL_CENTS` é `int`.

## VDF5 — DRE completa

A soma das contribuições de todas as contas `COD_NAT=04` coincide com:

```text
DRE_RESULTADO_PERIODO
```

## VDF6 — BP completo

Todas as contas ativas analíticas de natureza `01`, `02`, `03` estão representadas pelo mapping.

## VDF7 — resultado integrado

```text
BP_RESULTADO_PERIODO
=
DRE_RESULTADO_PERIODO
```

## VDF8 — identidade patrimonial

```text
BP_ATIVO
=
BP_TOTAL_PASSIVO_PL
```

## VDF9 — reconciliação com balancete

Cada linha detalhe é reconciliável às contas mapeadas e seus valores no balancete.

## VDF10 — sem efeito sobre núcleo

Conteúdo de:

```text
LANCAMENTOS
PARTIDAS
RAZAO
BALANCETE
```

é idêntico antes/depois da agregação de demonstrações.

---

# Testes obrigatórios — `statements.py`

Criar:

```text
tests/test_statements.py
```

Cobrir pelo menos:

1. `STATEMENT_MAPPING_COLUMNS` na ordem canônica;
2. default mapping cobre todas as contas analíticas ativas;
3. `COD_CTA` duplicado é rejeitado;
4. conta ausente é rejeitada;
5. conta sintética é rejeitada;
6. conta inativa é rejeitada;
7. conta patrimonial mapeada para DRE é rejeitada;
8. conta de resultado mapeada para BP é rejeitada;
9. linha inexistente é rejeitada;
10. mapping para subtotal é rejeitado;
11. mapping para `BP_RESULTADO_PERIODO` é rejeitado;
12. múltiplas contas para a mesma linha detalhe são permitidas;
13. incompatibilidade de saldo normal é rejeitada;
14. sincronização de `COD_DF` retorna cópia;
15. `COD_DF` sincronizado coincide com `MAPEAMENTO_DF`;
16. DRE usa `VL_CRED - VL_DEB`;
17. DRE não depende de `VL_SLD_FIN` para calcular fluxo;
18. BP usa saldo final;
19. contra-ativo aparece negativo;
20. passivo credor aparece positivo;
21. canonical DRE produz resultado `3000000`;
22. canonical BP produz ativo `13000000`;
23. canonical BP produz total passivo+PL `13000000`;
24. `BP_RESULTADO_PERIODO = 3000000`;
25. cenário de perda produz resultado negativo em DRE e BP;
26. identidade patrimonial é satisfeita;
27. gerar statements não modifica trial balance;
28. gerar statements não modifica chart;
29. mesma entrada gera DataFrames idênticos;
30. todos os valores Python são inteiros em centavos.

---

# Testes obrigatórios — workbook Spec 07

Atualizar:

```text
tests/test_workbook.py
```

Cobrir adicionalmente:

1. ordem exata das 16 abas;
2. `MAPEAMENTO_DF` existe;
3. `BP` existe;
4. `DRE` existe;
5. `DFC` e `DVA` não existem;
6. `tbl_MAPEAMENTO_DF` existe;
7. `tbl_BP` existe;
8. `tbl_DRE` existe;
9. `MAPEAMENTO_DF` round-trip;
10. `MAPEAMENTO_DF` é lido na regeneração;
11. `PLANO_CONTAS.COD_DF` é sincronizado pelo mapping;
12. edição isolada de `COD_DF` é descartada;
13. mudança válida de classificação em `MAPEAMENTO_DF` altera linha da DRE;
14. mudança de mapping não altera partidas;
15. BP canônico exibe `130000.00`;
16. DRE canônica exibe resultado `30000.00`;
17. BP/DRE usam duas casas decimais;
18. adulteração manual de BP é descartada;
19. adulteração manual de DRE é descartada;
20. `VALIDACOES` contém etapas novas;
21. `VALIDACOES` não possui falha no caso canônico;
22. `PROVENIENCIA` contém versão da Spec 07;
23. duas materializações produzem mesmas tabelas;
24. nenhuma fórmula Excel é necessária para BP/DRE;
25. nenhuma aba tributária foi adicionada.

---

# Teste de regressão do núcleo

Antes de implementar:

```text
python -m pytest -q
```

registrar baseline.

Depois:

```text
python -m pytest -q
```

A implementação deve manter todos os testes 00–06.

Em particular, o núcleo deve continuar produzindo:

```text
5 lançamentos
10 partidas
23000000 cents de débito
23000000 cents de crédito
15000000 cents de saldos devedores
15000000 cents de saldos credores
```

A introdução de demonstrações não altera esses números.

---

# Passos de implementação

1. rodar suíte completa e registrar baseline;
2. reler `COD_DF` no plano atual;
3. criar `statements.py`;
4. adicionar constantes do mapping e schemas;
5. implementar catálogos BP/DRE v1;
6. implementar default statement mapping;
7. implementar validação do mapping;
8. implementar sincronização `MAPEAMENTO_DF -> COD_DF`;
9. implementar DRE por movimentos;
10. implementar BP por saldos finais;
11. implementar `BP_RESULTADO_PERIODO`;
12. implementar identidade patrimonial;
13. implementar `FinancialStatements`;
14. implementar validador;
15. adicionar `test_statements.py`;
16. atualizar `WorkbookInputs`;
17. atualizar `WORKBOOK_SHEETS`;
18. adicionar `MAPEAMENTO_DF`;
19. adicionar `BP`;
20. adicionar `DRE`;
21. atualizar `VALIDACOES`;
22. atualizar `PROVENIENCIA`;
23. atualizar README interno do workbook;
24. implementar round-trip do mapping;
25. testar autoridade de `MAPEAMENTO_DF`;
26. testar adulteração BP/DRE;
27. testar caso canônico;
28. rodar suíte completa;
29. atualizar README raiz;
30. atualizar metadata desatualizada de `pyproject.toml`.

---

# Metadata do projeto

O `pyproject.toml` atualmente possui descrição antiga referindo-se apenas às specs 00–02.

Atualizar para texto compatível com o estado atual, por exemplo:

```text
MVP contábil parametrizado conforme specs 00-07.
```

Essa alteração é somente metadata.

Não alterar versão do pacote por causa desta spec, salvo necessidade técnica real.

---

# Critérios de aceitação

A Spec 07 está aceita se:

- [ ] existe `MAPEAMENTO_DF` normalizado;
- [ ] `MAPEAMENTO_DF` é a fonte autoritativa de `map_t^S` no workbook;
- [ ] `COD_DF` funciona como espelho sincronizado;
- [ ] toda conta analítica ativa possui mapping;
- [ ] BP usa saldos finais;
- [ ] DRE usa movimentos;
- [ ] DRE implementa sinais consistentes com `L_t = R_t-K_t-E_t+O_t`;
- [ ] `BP_RESULTADO_PERIODO` deriva da DRE;
- [ ] nenhuma conta artificial foi criada para o resultado corrente;
- [ ] nenhum lançamento de encerramento foi criado;
- [ ] identidade patrimonial fecha em centavos exatos;
- [ ] caso canônico produz DRE `3000000` cents;
- [ ] caso canônico produz BP `13000000 = 13000000` cents;
- [ ] cenário de prejuízo reduz PL corretamente;
- [ ] mapping altera apresentação sem alterar escrituração;
- [ ] BP/DRE são descartáveis e regeneráveis;
- [ ] workbook contém exatamente as abas definidas;
- [ ] DFC/DVA não foram implementadas;
- [ ] tributação não foi implementada;
- [ ] geração aleatória não foi implementada;
- [ ] não foi criado engine genérico de demonstrações;
- [ ] todos os testes 00–07 passam.

---

# Arquivos esperados

Criar:

```text
specs/07_financial_statements.md

src/accounting_sim/statements.py

tests/test_statements.py
```

Alterar quando necessário:

```text
src/accounting_sim/canonical.py
src/accounting_sim/workbook.py
src/accounting_sim/__init__.py

tests/test_workbook.py

README.md
pyproject.toml
```

Evitar alterações sem necessidade em:

```text
events.py
posting.py
ledger.py
account_mapping.py
```

Não alterar a política econômica de escrituração.

---

# Dependências e preservação das specs anteriores

## Spec 00

Preserva:

- empresa comercial simples;
- centavos como fonte de verdade;
- Python como motor;
- Excel como interface;
- sem tributação.

## Spec 01

Preserva símbolos:

```text
L_t -> resultado
R_t -> receitas
G^S -> operador de demonstração
P_t -> plano
b_t -> balancete
Wb_t -> workbook
```

Não introduzir alias conflitante.

## Spec 02

Preserva:

```text
COD_DF
```

no schema de `PLANO_CONTAS`.

A Spec 07 apenas normaliza a autoridade de `map_t^S` em `MAPEAMENTO_DF` e mantém `COD_DF` como espelho.

## Spec 03

`EVENTOS` permanece preservado.

Não usar eventos diretamente para agregar BP/DRE.

## Spec 04

Nenhuma regra de lançamento muda.

## Spec 05

Preserva:

```text
Lambda_t -> Dia_t
Lambda_t -> Raz_t
Raz_t -> b_t
```

e cumpre a promessa de tratar na Spec 07:

```text
A = P + PL
```

e o resultado corrente.

## Spec 06

Preserva:

```text
modelo lógico != interface física
```

e:

```text
editar entradas
-> regenerar núcleo
-> recalcular saídas
```

Apenas adiciona:

```text
MAPEAMENTO_DF
BP
DRE
```

à interface.

`MAPEAMENTO_CONTAS` continua com significado distinto.

---

# Preservação explícita dos Volumes I–III

A Spec 07 não altera:

```text
I_t = (t,t+1]

x_{t+1} = F(x_t,u_t;vartheta_t)

vartheta_t
=
(theta_t^acct, Theta_t^tax)

u_t
=
u_t^tr sqcup u_t^adj

E_t:
(x_t,u_t,P_t;theta_t^acct)
-> Lambda_t

Lambda_t -> Dia_t
Lambda_t -> Raz_t
Raz_t -> b_t

G^S
rho_t
eta_t
zeta_t
Theta_t^eff
Prov
```

A extensão é somente:

```text
b_t
+ map_t^S
-> BP_{t+1}
-> DRE_t
```

com a distinção temporal:

```text
BP = estoque no fim do período

DRE = fluxo reconhecido durante o período
```

e mantendo a futura camada tributária separada.
