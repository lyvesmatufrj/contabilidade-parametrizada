# Spec 05 — Diário, Livro Razão e balancete `Lambda_t -> Raz_t -> b_t`

**Status:** fechamento do Marco A  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–04 + Volumes I–III  
**Bloqueia:** specs 06–11

## Objetivo

Completar o núcleo contábil mínimo do Marco A derivando, de forma puramente mecânica e auditável:

```text
Lambda_t -> Dia_t
Lambda_t -> Raz_t
Raz_t    -> b_t
```

A implementação não deve reaplicar regras econômicas dos eventos. Depois que `LANCAMENTOS` e `PARTIDAS` existem e foram validados, Diário, Razão e balancete são **visões/aggregações derivadas da escrituração**.

O objetivo é chegar ao primeiro fechamento arquitetural:

```text
P_t + u_t -> Lambda_t -> Raz_t -> b_t
```

com testes passando, sem Excel e sem demonstrações financeiras ainda.

## Contexto canônico

### Source of truth

Consultar, nessa ordem:

```text
docs/volume_I/contabilidade_parametrizada.tex
docs/volume_II/contabilidade_parametrizada_volume_II.tex
docs/volume_III/contabilidade_parametrizada_volume_III.tex
specs/00_mvp_scope.md
specs/01_canonical_model.md
specs/02_chart_of_accounts.md
specs/03_events.md
specs/04_posting_engine.md
```

### Diário

O Volume III define o Diário como ordenação de `Lambda_t` por data e identificador:

```text
Dia_t := ord_{(d^lambda,id)}(Lambda_t)
```

Ele é uma visão cronológica, não uma nova fonte de verdade.

### Razão

Para cada conta analítica, `Raz_{i,t}` reúne as partidas da conta ordenadas cronologicamente.

O Razão completo é:

```text
Raz_t = (Raz_{i,t})_{a_i in C_t^A}
```

### Saldo assinado

Adotar exatamente a convenção interna do Volume III:

```text
saldo_assinado_novo
=
saldo_assinado_anterior
+ debitos
- creditos
```

Convenção:

```text
saldo assinado >= 0 -> D
saldo assinado <  0 -> C
```

`NAT_SALDO_NORMAL` permanece atributo da conta e não substitui a orientação efetiva do saldo.

### Balancete

O balancete periódico é inspirado em I150/I155 e contém saldo inicial, movimentos e saldo final por conta.

Nesta fase existe apenas **um período contábil por execução**.

## Escopo

Implementar:

1. `DIARIO` como visão cronológica das partidas;
2. `RAZAO` como visão por conta com saldo corrido;
3. `BALANCETE` para o único período da execução;
4. reconciliação entre partidas, Razão e balancete;
5. saldo inicial zero no cenário padrão;
6. validações estruturais executáveis.

### Estado inicial no MVP

O formalismo canônico preserva `x_t`, mas esta etapa usa:

```text
saldo inicial = 0
```

para todas as contas analíticas no cenário padrão.

Aporte de capital e demais condições iniciais devem aparecer como eventos/lançamentos explícitos.

Não criar ainda uma tabela persistente de saldos iniciais. Uma futura extensão poderá receber `x_t`/saldos carregados quando houver necessidade concreta.

## Fora de escopo

Não implementar:

- múltiplos períodos na mesma execução;
- continuidade interperíodos real;
- mudança de plano durante o período;
- encerramento de contas de resultado;
- lançamentos de fechamento;
- BP;
- DRE;
- DFC;
- DVA;
- identidade patrimonial como critério desta spec;
- fórmulas Excel;
- workbook;
- tributação;
- geração aleatória;
- subledgers;
- centros de custo.

A identidade `A = P + PL` será verificada na spec 07, quando BP/DRE e tratamento do resultado corrente forem explicitados.

## Entradas

```python
journal_entry_headers: pd.DataFrame
postings: pd.DataFrame
chart_of_accounts: pd.DataFrame
period: AccountingPeriod
```

Pré-condições:

```text
validate_chart_of_accounts(...).ok is True
validate_posting_result(...).ok is True
```

`EVENTOS` não é necessário para calcular saldos, embora IDs de origem possam ser preservados nas views para auditoria.

## Saídas

```python
journal_view: pd.DataFrame
ledger_view: pd.DataFrame
trial_balance: pd.DataFrame
```

Opcionalmente retornar:

```python
@dataclass(frozen=True)
class LedgerResult:
    journal_view: pd.DataFrame
    ledger_view: pd.DataFrame
    trial_balance: pd.DataFrame
```

Se a dataclass não reduzir complexidade, três DataFrames separados são aceitáveis.

## Schema — `DIARIO`

Ordem recomendada:

| Coluna | Origem | Regra |
|---|---|---|
| `DT_LCTO` | LANCAMENTOS | ordenação primária |
| `NUM_LCTO` | LANCAMENTOS | identificador |
| `ID_PARTIDA` | PARTIDAS | desempate estável |
| `COD_CTA` | PARTIDAS | conta analítica |
| `CTA` | PLANO_CONTAS | nome para auditoria |
| `IND_DC` | PARTIDAS | D/C |
| `VL_DC_CENTS` | PARTIDAS | valor |
| `HIST` | PARTIDAS | descrição |
| `COD_PART` | PARTIDAS | participante opcional |
| `ID_ORIGEM` | PARTIDAS | evento/documento de origem |

Ordenação:

```text
DT_LCTO, NUM_LCTO, ID_PARTIDA
```

`DIARIO` não altera os valores de `PARTIDAS`.

## Schema — `RAZAO`

Ordem recomendada:

| Coluna | Tipo | Regra |
|---|---|---|
| `COD_CTA` | `str` | agrupamento primário |
| `CTA` | `str` | nome da conta |
| `DT_LCTO` | `date` | ordem cronológica |
| `NUM_LCTO` | `str` | referência ao lançamento |
| `ID_PARTIDA` | `str` | referência à partida |
| `DEBITO_CENTS` | `int` | `VL_DC_CENTS` se D, senão 0 |
| `CREDITO_CENTS` | `int` | `VL_DC_CENTS` se C, senão 0 |
| `MOVIMENTO_ASSINADO_CENTS` | `int` | débito positivo, crédito negativo |
| `SALDO_ASSINADO_CENTS` | `int` | soma acumulada por conta |
| `SALDO_ABS_CENTS` | `int` | `abs(SALDO_ASSINADO_CENTS)` |
| `IND_DC_SALDO` | enum D/C | encoding canônico do saldo |
| `HIST` | `str` | histórico |
| `ID_ORIGEM` | `str` | rastreabilidade |

Ordenação:

```text
COD_CTA (ordem hierárquica), DT_LCTO, NUM_LCTO, ID_PARTIDA
```

A ordenação de `COD_CTA` deve reutilizar a função hierárquica da spec 02; não duplicar uma nova regra divergente.

## Schema — `BALANCETE`

O MVP usa as contas analíticas ativas do plano, inclusive contas sem movimento.

Ordem canônica:

| Coluna | Tipo | Regra |
|---|---|---|
| `DT_INI` | `date` | início do período |
| `DT_FIN` | `date` | fim do período |
| `COD_CTA` | `str` | conta analítica |
| `COD_CCUS` | `str | None` | `None` no MVP |
| `VL_SLD_INI_CENTS` | `int` | 0 no MVP |
| `IND_DC_INI` | enum D/C | `D` para saldo assinado zero, conforme encoding canônico |
| `VL_DEB_CENTS` | `int` | débitos do período |
| `VL_CRED_CENTS` | `int` | créditos do período |
| `VL_SLD_FIN_CENTS` | `int` | saldo final absoluto |
| `IND_DC_FIN` | enum D/C | encoding do saldo final |

### Observação sobre zero

O Volume III define:

```text
saldo_assinado >= 0 -> D
```

Portanto, saldo zero é codificado como:

```text
0 D
```

nesta fase. Não substituir silenciosamente por `NAT_SALDO_NORMAL`.

## Regras / invariantes

### L1 — fonte de verdade

`DIARIO`, `RAZAO` e `BALANCETE` são derivados. Nenhuma função deve modificar `journal_entry_headers` ou `postings` in-place.

### L2 — Diário preserva partidas

A quantidade de linhas de `DIARIO` deve ser igual à quantidade de linhas de `PARTIDAS`.

Para cada `ID_PARTIDA`, os campos econômicos devem ser idênticos.

### L3 — movimento assinado

Para cada linha do Razão:

```text
MOVIMENTO_ASSINADO_CENTS = DEBITO_CENTS - CREDITO_CENTS
```

### L4 — saldo corrido

Por conta:

```text
SALDO_ASSINADO_CENTS[r]
=
SALDO_ASSINADO_CENTS[r-1]
+ MOVIMENTO_ASSINADO_CENTS[r]
```

com saldo inicial zero no MVP.

### L5 — encoding do saldo

```text
saldo >= 0 -> (abs(saldo), D)
saldo <  0 -> (abs(saldo), C)
```

### L6 — reconciliação por conta

Para cada conta:

```text
saldo_final_assinado
=
VL_DEB_CENTS
- VL_CRED_CENTS
```

no cenário de saldo inicial zero.

### L7 — reconciliação global

```text
sum(VL_DEB_CENTS) = sum(VL_CRED_CENTS)
```

no balancete.

Esse total deve coincidir com os totais de `PARTIDAS`.

### L8 — contas sem movimento

Contas analíticas ativas sem partidas devem aparecer no balancete com zeros.

Não precisam gerar linhas no Razão.

### L9 — integridade referencial

Toda conta no Razão e balancete deve existir no plano e ser analítica.

### L10 — período

Todas as partidas incluídas devem pertencer a lançamentos com:

```text
start_date <= DT_LCTO <= end_date
```

### L11 — determinismo

Mesmas entradas produzem Diário, Razão e balancete idênticos e ordenados da mesma forma.

### L12 — sem recomputar eventos

Não consultar `TIPO_EVENTO` para decidir saldos. A semântica econômica já foi resolvida na spec 04.

## API mínima

Implementar preferencialmente em:

```text
src/accounting_sim/ledger.py
```

API esperada:

```python
def build_journal(
    journal_entry_headers: pd.DataFrame,
    postings: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    ...


def build_ledger(
    journal_entry_headers: pd.DataFrame,
    postings: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> pd.DataFrame:
    ...


def build_trial_balance(
    ledger: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    period: AccountingPeriod,
) -> pd.DataFrame:
    ...


def validate_ledger_trial_balance(
    postings: pd.DataFrame,
    ledger: pd.DataFrame,
    trial_balance: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    period: AccountingPeriod,
) -> ValidationReport:
    ...
```

Criar helpers privados para:

```text
_encode_signed_balance
```

e reutilizar o sort de código de conta da spec 02 por API pública ou helper compartilhado mínimo.

Não criar uma camada genérica de query/view.

## Passos de implementação

1. executar toda a suíte 00–04 antes da alteração;
2. declarar constantes imutáveis para schemas de Diário, Razão e balancete;
3. implementar join de cabeçalhos + partidas + nome da conta para Diário;
4. implementar colunas D/C separadas e movimento assinado;
5. calcular saldo acumulado por `COD_CTA`;
6. implementar encoding absoluto + indicador D/C;
7. construir balancete para todas as contas analíticas ativas;
8. reconciliar movimentos com `PARTIDAS`;
9. adicionar testes do exemplo canônico do Volume III;
10. executar suíte completa e garantir ausência de regressões.

## Caso canônico do Volume III

Entrada econômica:

```text
aporte de capital      100000
compra à vista          30000
venda a prazo           50000  custo 20000
recebimento cliente     30000
```

Depois da spec 04, os saldos esperados são:

```text
Caixa                        100000 D
Clientes                      20000 D
Estoques                      10000 D
Capital Social               100000 C
Receita de Vendas             50000 C
CMV                            20000 D
```

Em centavos:

```text
Caixa                        10000000 D
Clientes                      2000000 D
Estoques                      1000000 D
Capital Social              10000000 C
Receita de Vendas            5000000 C
CMV                           2000000 D
```

A soma dos saldos devedores e credores é:

```text
15000000 cents = 15000000 cents
```

Não derivar DRE ou BP ainda; apenas verificar que o Razão e o balancete reproduzem os saldos.

## Testes obrigatórios

Criar `tests/test_ledger.py` cobrindo pelo menos:

1. Diário possui uma linha por partida;
2. Diário é ordenado por data, lançamento e partida;
3. Razão separa débito/crédito corretamente;
4. movimento assinado = débito - crédito;
5. saldo corrido é correto por conta;
6. saldo final do Razão corresponde ao balancete;
7. conta de natureza credora produz `IND_DC_SALDO=C` quando saldo assinado é negativo;
8. saldo zero produz `0 D` conforme convenção canônica;
9. contas analíticas ativas sem movimento aparecem no balancete;
10. contas sintéticas não aparecem como linhas do balancete MVP;
11. soma dos débitos = soma dos créditos no balancete;
12. totais coincidem com `PARTIDAS`;
13. lançamentos fora do período são rejeitados;
14. cenário canônico produz exatamente os seis saldos não zero esperados;
15. mesma entrada executada duas vezes produz DataFrames idênticos;
16. funções não alteram os DataFrames de entrada in-place.

## Critérios de aceitação

A spec 05 está aceita se:

- [ ] `DIARIO` é uma visão fiel e ordenada de `PARTIDAS`;
- [ ] `RAZAO` calcula saldos corridos corretamente;
- [ ] `BALANCETE` reconcilia com o Razão e com as partidas;
- [ ] totais globais de débito e crédito são iguais;
- [ ] o exemplo canônico do Volume III fecha exatamente;
- [ ] nenhuma regra econômica é recalculada a partir de eventos;
- [ ] nenhuma demonstração financeira foi antecipada;
- [ ] nenhum workbook foi criado;
- [ ] nenhum cálculo tributário foi introduzido;
- [ ] `pytest` completo passa.

## Arquivos esperados

```text
src/accounting_sim/ledger.py
tests/test_ledger.py
```

Atualizar apenas se necessário:

```text
src/accounting_sim/canonical.py
src/accounting_sim/chart_of_accounts.py
src/accounting_sim/__init__.py
```

## Dependências de outras specs

- spec 00 — escopo do MVP;
- spec 01 — convenções e tipos;
- spec 02 — plano hierárquico;
- spec 03 — eventos;
- spec 04 — lançamentos e partidas.

Com a conclusão desta spec, o **Marco A — núcleo contábil mínimo** está completo:

```text
P_t + u_t -> Lambda_t -> Raz_t -> b_t
```

A próxima etapa será a spec 06, materialização do modelo lógico no workbook Excel.
