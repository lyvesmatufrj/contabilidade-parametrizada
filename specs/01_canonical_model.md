# Spec 01 — Modelo canônico: matemática ↔ Python ↔ Excel

**Status:** implementação inicial  
**Prioridade:** bloqueadora  
**Depende de:** spec 00 + Volumes I–III  
**Bloqueia:** specs 02–11

## Objetivo

Criar uma convenção única de nomes, tipos e responsabilidades entre:

1. a notação matemática canônica dos Volumes I–III;
2. os objetos/tabelas em Python;
3. as futuras tabelas/abas do workbook Excel.

A finalidade é impedir colisões semânticas durante a implementação com múltiplas specs/agentes.

Esta spec **não** exige criar uma classe Python para cada símbolo matemático. Ela fixa o vocabulário computacional.

## Contexto canônico

Os três volumes reservam os seguintes símbolos:

```text
I_t                  período (t,t+1]
x_t                  estado econômico-contábil
u_t                  família de eventos/operações
T_{k,t}              evento/operação elementar
vartheta_t            regras aplicáveis
theta_t^acct          regras contábeis
Theta_t^tax           regras tributárias
G^S                   operador da demonstração S
Lambda_t              camada/família de lançamentos

rho_t                 configuração tributária da entidade
eta_t                 perfil factual da entidade
zeta_t                vetor mínimo de entrada
\mathfrak E_{j,t}           seletor de regra tributária efetiva
Prov                  proveniência
Q_t                   pacote de fontes empresariais
b_t                   balancete/agregado periódico

P_t                   plano de contas parametrizado
lambda_{ell,t}        lançamento contábil
H^lambda_{ell,t}      cabeçalho do lançamento
psi_{ell r,t}         partida contábil
V_t                   vínculo evento–lançamento
Dia_t                 Livro Diário / visão cronológica
Raz_t                 Livro Razão / visão por conta
Wb_t                  workbook Excel
Omega^sim             configuração computacional da simulação
Gamma                 calibração futura de verossimilhança
```

## Colisões proibidas

As seguintes reutilizações são proibidas:

| Nome | Significado canônico | Não usar para |
|---|---|---|
| `L_t` | resultado contábil na DRE | lançamentos/ledger |
| `R_t` | receitas | Livro Razão |
| `A_j` / `mathcal A_j` | operador de alíquota | plano/estrutura de contas |
| `A^S` / `mathcal A^S` | agregação de demonstração | conta ou ativo genérico |
| `mathfrak R` | operador da reforma | Razão |
| `p_{k,t}` | condição de pagamento/recebimento do evento | partida contábil |
| `r_t` | não adotar como novo vetor de saldos | Razão ou balancete |
| `z_t` | ajustes/informações fiscais adicionais do Volume I | vetor global de entrada |
| `s_{k,t}` | data/instante do evento | tratamento especial |
| `E_j` | exclusões/deduções de base no Volume I | seletor de regra efetiva |

Usar exatamente:

```text
Lambda_t  -> lançamentos
Raz_t     -> Livro Razão
psi       -> partida
b_t       -> balancete
zeta_t    -> entrada mínima
\mathfrak E -> seletor de regra efetiva
```

## Política de tradução computacional

### Regra geral

- símbolos matemáticos descrevem **semântica**;
- nomes Python descrevem **objetos de implementação**;
- nomes Excel descrevem **interfaces tabulares**.

Não exigir bijeção 1:1 entre matemática e classes Python.

## Dicionário canônico

| Formalismo | Nome Python reservado | Representação MVP | Excel futuro |
|---|---|---|---|
| `I_t` | `AccountingPeriod` / `period` | par de datas | `CONFIG` |
| `x_t` | `accounting_state` | derivado de saldos | derivado |
| `u_t` | `events` | `DataFrame` | `EVENTOS` |
| `T_{k,t}` | `event` | linha/registro | linha de `EVENTOS` |
| `vartheta_t` | `rules` | configuração reservada | governança |
| `theta_t^acct` | `accounting_rules` | templates/funções | reservado |
| `Theta_t^tax` | `tax_rules` | **reservado, não implementar** | `FISCAL_*` futuro |
| `G^S` | `statement_aggregator` | função futura | BP/DRE/... |
| `Lambda_t` | `journal_entries` | tabelas de cabeçalhos + partidas | `LANCAMENTOS` + `PARTIDAS` |
| `rho_t` | `tax_regime_config` | reservado | `ENTIDADE` futuro |
| `eta_t` | `entity_profile` | configuração simples | `ENTIDADE` |
| `zeta_t` | `simulation_input` | composição lógica | não é uma aba única |
| `\mathfrak E_{j,t}` | `effective_tax_rule_selector` | reservado | reservado |
| `Prov` | `provenance` | metadados | `PROVENIENCIA` |
| `Q_t` | `source_bundle` | reservado | fontes/importações |
| `P_t` | `chart_of_accounts` | `DataFrame` validado | `PLANO_CONTAS` |
| `C_t` (conjunto de contas) | `accounts` | linhas de `chart_of_accounts` | `PLANO_CONTAS` |
| `a_{i,t}` | `account` | uma linha | uma linha de `PLANO_CONTAS` |
| `lambda_{ell,t}` | `journal_entry` | cabeçalho + partidas | chave `NUM_LCTO` |
| `H^lambda` | `journal_entry_headers` | `DataFrame` | `LANCAMENTOS` |
| `psi_{ell r,t}` | `postings` | `DataFrame` | `PARTIDAS` |
| `V_t` | `event_entry_links` | `DataFrame` | `VINCULO_EVENTO_LCTO` |
| `Dia_t` | `journal_view` | view/DataFrame derivado | `DIARIO` |
| `Raz_t` | `ledger_view` | view/DataFrame derivado | `RAZAO` |
| `b_t` | `trial_balance` | `DataFrame` derivado | `BALANCETE` |
| `Wb_t` | `workbook` | arquivo `.xlsx` | workbook |
| `Omega^sim` | `simulation_config` | dict/dataclass simples | `CONFIG` |
| `Gamma` | `calibration_profile` | reservado | futuro |

## Nomes de campos

Quando um schema já foi fixado no Volume III, o código deve preferir o nome de coluna canônico em MAIÚSCULAS.

Exemplo do plano de contas:

```text
DT_ALT
COD_NAT
IND_CTA
NIVEL
COD_CTA
COD_CTA_SUP
CTA
NAT_SALDO_NORMAL
COD_DF
ATIVA
ORIGEM
```

O código Python pode usar constantes para essas colunas, mas **não renomeá-las silenciosamente** para outra taxonomia na fronteira de persistência.

## Tipos primitivos canônicos

### Datas

```python
datetime.date
```

Serialização:

```text
YYYY-MM-DD
```

### Valores monetários

Fonte de verdade interna:

```python
int  # centavos
```

Convenção:

```text
100.00 BRL -> 10000 cents
```

Nunca usar igualdade de `float` para testar partida dobrada ou reconciliação.

### Booleanos

Usar `bool` internamente e `TRUE/FALSE` ou equivalente ao exportar.

### Chaves

Usar `str`.

Não usar índice posicional do DataFrame como identificador de domínio.

## Enums mínimos

Criar em `src/accounting_sim/canonical.py`:

```python
from enum import StrEnum

class DebitCredit(StrEnum):
    DEBIT = "D"
    CREDIT = "C"

class AccountType(StrEnum):
    SYNTHETIC = "S"
    ANALYTIC = "A"

class AccountNature(StrEnum):
    ASSET = "01"
    LIABILITY = "02"
    EQUITY = "03"
    RESULT = "04"
    COMPENSATION = "05"
    OTHER = "09"

class Origin(StrEnum):
    OBSERVED = "observada"
    SYNTHETIC = "sintética"
    TEMPLATE = "template"
    ADJUSTED = "ajustada"
```

`AccountNature` reproduz a codificação estrutural utilizada pelo SPED/ECD. O template inicial da spec 02 usará apenas `01`–`04`.

Enums de lançamento (`N/E/X`) serão introduzidos apenas na spec 04, quando `Lambda_t` for implementada.

## Representação tabular

### Decisão

Usar `pandas.DataFrame` como representação de coleções tabulares do MVP.

Exemplos:

```python
chart_of_accounts: pd.DataFrame
events: pd.DataFrame
journal_entry_headers: pd.DataFrame
postings: pd.DataFrame
ledger_view: pd.DataFrame
trial_balance: pd.DataFrame
```

### Não fazer ainda

Não criar uma classe mutável por linha do DataFrame como requisito obrigatório.

Dataclasses podem ser usadas para configuração compacta (`AccountingPeriod`, `SimulationConfig`) se reduzirem ambiguidade, mas não devem envolver cada linha em objetos para depois convertê-los novamente em tabelas.

## Contratos funcionais reservados

As seguintes assinaturas conceituais devem orientar as specs futuras:

```python
validate_chart_of_accounts(df) -> ValidationReport

post_events(state, events, chart_of_accounts, accounting_rules)
    -> (journal_entry_headers, postings, event_entry_links)

build_journal(journal_entry_headers, postings) -> DataFrame

build_ledger(journal_entry_headers, postings, chart_of_accounts) -> DataFrame

build_trial_balance(ledger, period) -> DataFrame

build_financial_statements(trial_balance, mapping) -> dict[str, DataFrame]

write_workbook(model, path) -> Path
```

Somente `validate_chart_of_accounts` pertence à implementação imediata das specs 00–02.

## Convenções de erro

Criar tipos simples:

```python
class AccountingSimError(Exception): ...
class SchemaValidationError(AccountingSimError): ...
class ReferentialIntegrityError(AccountingSimError): ...
class AccountingInvariantError(AccountingSimError): ...
```

Não criar uma taxonomia extensa de exceções nesta fase.

## Proveniência mínima

Todo objeto materializado que vier de dados externos ou template deve poder carregar ao menos:

```text
ORIGEM
spec_version
source_ref (quando aplicável)
```

No plano de contas, `ORIGEM` já faz parte do schema canônico.

## Testes obrigatórios

Implementar em `tests/test_canonical.py`:

1. todos os enums produzem exatamente os valores definidos;
2. conversão monetária para centavos é determinística;
3. `100.10` não passa por `float` antes de virar centavos;
4. datas ISO válidas são convertidas para `date`;
5. os nomes de colunas canônicos do plano estão disponíveis como constante imutável;
6. nomes proibidos não são introduzidos como aliases públicos (`ledger = R_t`, `L_t = journal_entries`, etc.).

## Critérios de aceitação

- [ ] `canonical.py` concentra enums, constantes e helpers primitivos;
- [ ] não existe colisão com símbolos reservados dos Volumes I–III;
- [ ] valores monetários críticos não usam `float` como fonte de verdade;
- [ ] specs futuras podem importar as constantes sem redefini-las;
- [ ] `pytest tests/test_canonical.py` passa.

## Arquivos esperados

```text
src/accounting_sim/canonical.py
tests/test_canonical.py
```

Opcionalmente atualizar:

```text
src/accounting_sim/__init__.py
```

apenas para exportar símbolos estáveis realmente úteis.

## Dependências de outras specs

- spec 00 — escopo e stack.
- Volume III — tabela canônica de símbolos e reconciliação de colisões.
