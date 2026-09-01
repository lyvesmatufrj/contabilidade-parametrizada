# Spec 04 — Operador de escrituração `u_t -> Lambda_t`

**Status:** próxima implementação  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–03 + Volumes I–III  
**Bloqueia:** specs 05–11

## Objetivo

Implementar o primeiro operador contábil determinístico de escrituração:

```text
(x_t, u_t, P_t; theta_t^acct) -> Lambda_t
```

em uma versão deliberadamente pequena, explícita e auditável.

No MVP, a implementação deve transformar os tipos de evento da spec 03 em:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
```

respeitando partida dobrada, integridade referencial, contas analíticas ativas e determinismo.

Esta spec é o primeiro ponto em que a parametrização canônica se torna um sistema contábil executável.

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
```

### Objeto do Volume III

O operador é:

```text
E_t : (x_t, u_t, P_t; theta_t^acct) -> Lambda_t
```

A família de lançamentos é:

```text
Lambda_t = (lambda_{ell,t})_{ell=1}^{M_t}
```

Cada lançamento possui:

```text
lambda_{ell,t} = (H^lambda_{ell,t}, Psi_{ell,t})
```

com cabeçalho e partidas.

A relação:

```text
V_t subset K_t x L_t
```

preserva o vínculo evento–lançamento e não exige cardinalidade 1:1.

### Decisão de engenharia do MVP

A matemática admite `x_t` e regras contábeis gerais. Nesta primeira implementação, não criar objetos artificiais apenas para espelhar cada argumento da equação.

O contexto efetivamente consumido é:

```text
events
chart_of_accounts
simulation_id
rule_version
```

O estado inicial é zero para as contas do cenário padrão; o aporte de capital é um evento explícito. Estados iniciais não nulos serão adicionados quando uma spec posterior exigir.

`theta_t^acct` é materializada nesta fase por um conjunto pequeno e versionado de regras determinísticas, não por um engine genérico de regras.

## Escopo

### Política contábil determinística v1

Implementar regras apenas para os tipos da spec 03.

### Contas usadas

Usar apenas contas analíticas ativas do template da spec 02.

Mapeamento mínimo:

```text
caixa                       -> 1.1.01.01
banco                       -> 1.1.01.02
clientes                    -> 1.1.02.01
estoques                    -> 1.1.03.01
imobilizado                 -> 1.2.01.01
depreciacao_acumulada       -> 1.2.01.02
fornecedores                -> 2.1.01.01
capital_social              -> 3.1.01.01
receita_vendas              -> 4.1.01.01
cmv                         -> 4.2.01.01
despesa_salarios            -> 4.3.01.01
despesa_aluguel             -> 4.3.01.02
despesa_utilidades          -> 4.3.01.03
despesa_depreciacao         -> 4.3.01.04
despesa_juros               -> 4.3.02.01
```

Não espalhar esses códigos como literais por múltiplas funções. Centralizar em uma constante/mapeamento pequeno e testável.

### Tipo de lançamento

O enum canônico deve admitir:

```text
N = normal
E = encerramento
X = extemporâneo
```

mas esta spec deve produzir apenas:

```text
IND_LCTO = N
```

Encerramento e extemporaneidade ficam fora do MVP desta etapa.

## Fora de escopo

Não implementar:

- encerramento de contas de resultado;
- lançamentos extemporâneos;
- centros de custo;
- históricos padronizados complexos;
- consolidação automática de vários eventos em um lançamento;
- regras configuráveis por DSL/JSON/YAML;
- engine genérico de regras;
- reversões automáticas;
- accrual engine;
- estoque por quantidade/SKU;
- validação de saldo disponível de estoque;
- tributação;
- impostos recuperáveis/a recolher;
- Excel;
- BP/DRE;
- geração aleatória.

## Entradas

```python
events: pd.DataFrame
chart_of_accounts: pd.DataFrame
simulation_config: SimulationConfig
```

Pré-condições:

```text
validate_events(events, period).ok is True
validate_chart_of_accounts(chart_of_accounts).ok is True
```

A função deve falhar cedo se receber entradas inválidas.

## Saídas

Retornar um objeto simples, preferencialmente dataclass congelada:

```python
@dataclass(frozen=True)
class PostingResult:
    journal_entry_headers: pd.DataFrame
    postings: pd.DataFrame
    event_entry_links: pd.DataFrame
```

Não criar uma árvore extensa de classes de domínio.

## Schema — `LANCAMENTOS`

Ordem canônica do DataFrame `journal_entry_headers`:

| Coluna | Tipo interno | Regra |
|---|---|---|
| `NUM_LCTO` | `str` | chave primária estável |
| `DT_LCTO` | `date` | data do lançamento |
| `VL_LCTO_CENTS` | `int` | soma de um dos lados D/C |
| `IND_LCTO` | enum | `N` no MVP |
| `DT_LCTO_EXT` | `date | None` | sempre `None` no MVP |
| `ID_GERACAO` | `str` | `simulation_id` |
| `VERSAO_REGRA` | `str` | versão explícita da política |

### Compatibilidade com Volume III

`VL_LCTO_CENTS` é a representação computacional inteira de `VL_LCTO`.

Não criar simultaneamente colunas monetárias redundantes em reais e centavos no núcleo Python.

## Schema — `PARTIDAS`

Ordem canônica do DataFrame `postings`:

| Coluna | Tipo interno | Regra |
|---|---|---|
| `ID_PARTIDA` | `str` | chave primária |
| `NUM_LCTO` | `str` | FK para `LANCAMENTOS` |
| `COD_CTA` | `str` | conta analítica ativa |
| `COD_CCUS` | `str | None` | `None` no MVP |
| `VL_DC_CENTS` | `int` | valor positivo |
| `IND_DC` | enum `D`/`C` | natureza da partida |
| `NUM_ARQ` | `str | None` | referência documental quando houver |
| `COD_HIST_PAD` | `str | None` | `None` no MVP |
| `HIST` | `str` | histórico legível |
| `COD_PART` | `str | None` | participante herdado do evento |
| `ID_ORIGEM` | `str` | evento de origem direto |

## Schema — `VINCULO_EVENTO_LCTO`

Ordem canônica:

| Coluna | Tipo | Regra |
|---|---|---|
| `ID_EVENTO` | `str` | FK para `EVENTOS` |
| `NUM_LCTO` | `str` | FK para `LANCAMENTOS` |
| `ORDEM_LCTO_EVENTO` | `int` | 1, 2, ... dentro do evento |

Chave composta:

```text
(ID_EVENTO, NUM_LCTO)
```

Nesta versão, cada lançamento deriva de exatamente um evento, mas a tabela de vínculo deve ser mantida porque o modelo canônico permite muitos-para-muitos no futuro.

## Regras de escrituração v1

### R1 — aporte de capital

```text
D  caixa/banco               VL_EVENTO
C  Capital Social            VL_EVENTO
```

Um lançamento.

### R2 — compra de mercadoria à vista

```text
D  Estoques                  VL_EVENTO
C  caixa/banco               VL_EVENTO
```

Um lançamento.

### R3 — compra de mercadoria a prazo

```text
D  Estoques                  VL_EVENTO
C  Fornecedores              VL_EVENTO
```

Um lançamento.

### R4 — pagamento de fornecedor

```text
D  Fornecedores              VL_EVENTO
C  caixa/banco               VL_EVENTO
```

Um lançamento.

Não validar nesta fase se o pagamento excede saldo do fornecedor; isso pertence a uma futura camada de estado/subledger.

### R5 — venda à vista

Lançamento 1 — receita:

```text
D  caixa/banco               VL_EVENTO
C  Receita de Vendas         VL_EVENTO
```

Lançamento 2 — custo:

```text
D  CMV                       VL_CUSTO
C  Estoques                  VL_CUSTO
```

### R6 — venda a prazo

Lançamento 1 — receita:

```text
D  Clientes                  VL_EVENTO
C  Receita de Vendas         VL_EVENTO
```

Lançamento 2 — custo:

```text
D  CMV                       VL_CUSTO
C  Estoques                  VL_CUSTO
```

### R7 — recebimento de cliente

```text
D  caixa/banco               VL_EVENTO
C  Clientes                  VL_EVENTO
```

### R8 — despesa operacional à vista

Mapear `CATEGORIA_DESPESA`:

```text
salarios   -> Salários e Encargos
aluguel    -> Aluguéis
utilidades -> Energia e Utilidades
juros      -> Juros e Encargos Financeiros
```

Lançamento:

```text
D  conta de despesa mapeada  VL_EVENTO
C  caixa/banco               VL_EVENTO
```

### R9 — depreciação

```text
D  Despesa de Depreciação    VL_EVENTO
C  Depreciação Acumulada     VL_EVENTO
```

Um lançamento.

## Identificadores determinísticos

Não usar UUID aleatório para `NUM_LCTO` e `ID_PARTIDA` no MVP.

Depois de ordenar eventos por:

```text
DT_EVENTO, ID_EVENTO
```

atribuir:

```text
NUM_LCTO   = L000001, L000002, ...
ID_PARTIDA = P000001, P000002, ...
```

Para eventos que geram dois lançamentos, a ordem é:

```text
1. reconhecimento da receita
2. reconhecimento do custo/CMV
```

Assim, o mesmo input deve produzir exatamente as mesmas chaves.

## Invariantes

### P1 — entrada validada

O engine não deve tentar corrigir eventos ou plano inválidos.

### P2 — conta existente

Toda `COD_CTA` em `PARTIDAS` deve existir em `PLANO_CONTAS`.

### P3 — conta analítica e ativa

Toda conta utilizada deve satisfazer:

```text
IND_CTA = A
ATIVA = True
```

### P4 — valor de partida

```text
VL_DC_CENTS > 0
```

### P5 — partida dobrada por lançamento

Para todo `NUM_LCTO`:

```text
sum(VL_DC_CENTS where IND_DC=D)
=
sum(VL_DC_CENTS where IND_DC=C)
=VL_LCTO_CENTS
```

### P6 — identificadores

`NUM_LCTO` e `ID_PARTIDA` são únicos.

### P7 — integridade referencial

Todo `NUM_LCTO` de `PARTIDAS` existe em `LANCAMENTOS`.

Todo par de `VINCULO_EVENTO_LCTO` referencia evento e lançamento existentes.

### P8 — origem

Todo lançamento produzido pelo MVP deve possuir vínculo com pelo menos um evento.

### P9 — datas

`DT_LCTO = DT_EVENTO` no MVP.

`DT_LCTO_EXT = None`.

### P10 — valor do cabeçalho

`VL_LCTO_CENTS` é a soma de **um lado** do lançamento, não a soma de todas as partidas.

### P11 — determinismo

Mesmo `events`, plano, `simulation_id` e `VERSAO_REGRA` produzem DataFrames idênticos, inclusive IDs e ordenação.

### P12 — ausência de tributação

As contas genéricas de tributos existentes no plano não devem ser usadas pelas regras v1.

## API mínima

Implementar preferencialmente em:

```text
src/accounting_sim/posting.py
```

API esperada:

```python
def post_events(
    events: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    simulation_config: SimulationConfig,
    *,
    rule_version: str = "posting_rules_v1",
) -> PostingResult:
    ...


def validate_posting_result(
    result: PostingResult,
    events: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    ...
```

É aceitável criar helpers privados pequenos por tipo de evento.

Não criar `RuleEngine`, plugin system, DSL ou classes de estratégia nesta fase.

## Passos de implementação

1. garantir que specs 00–03 e testes existentes passam antes da alteração;
2. adicionar enum `JournalEntryType` com `N/E/X` em `canonical.py`;
3. declarar constantes imutáveis para os três schemas;
4. centralizar o mapeamento semântico de contas do template;
5. implementar `PostingResult`;
6. implementar um dispatcher simples por `TIPO_EVENTO`;
7. gerar cabeçalhos, partidas e vínculos em memória;
8. validar partida dobrada e FKs antes de retornar;
9. garantir ordenação determinística;
10. adicionar testes por regra e testes globais.

## Caso canônico do Volume III

Usar como teste de aceitação:

```text
E001 aporte de capital       100000
E002 compra à vista           30000
E003 venda a prazo            50000 custo 20000
E004 recebimento cliente      30000
```

Esperar cinco lançamentos:

```text
L001 aporte
L002 compra
L003 receita da venda
L004 CMV da venda
L005 recebimento
```

com dez partidas.

Somas globais:

```text
Débitos  = 230000
Créditos = 230000
```

em reais, ou:

```text
23000000 cents
```

por lado.

## Testes obrigatórios

Criar `tests/test_posting.py` cobrindo pelo menos:

1. cada tipo de evento produz as contas e D/C esperados;
2. vendas produzem dois lançamentos em ordem estável;
3. `VL_LCTO_CENTS` corresponde a um lado do lançamento;
4. partida dobrada por lançamento;
5. soma global de débitos = soma global de créditos;
6. apenas contas analíticas ativas são usadas;
7. conta inexistente gera erro claro;
8. conta sintética usada por mapeamento inválido gera erro;
9. IDs de lançamentos são únicos e determinísticos;
10. IDs de partidas são únicos e determinísticos;
11. vínculos evento–lançamento são íntegros;
12. `DT_LCTO` preserva data do evento;
13. `IND_LCTO=N` para todos os lançamentos;
14. `DT_LCTO_EXT=None`;
15. cenário canônico do Volume III produz 5 lançamentos, 10 partidas e total 23.000.000 cents por lado;
16. mesma entrada executada duas vezes produz exatamente os mesmos três DataFrames.

## Critérios de aceitação

A spec 04 está aceita se:

- [ ] todos os tipos da spec 03 têm regra explícita;
- [ ] todo lançamento satisfaz partida dobrada;
- [ ] FKs para plano e eventos são válidas;
- [ ] vendas demonstram evento `1 -> 2 lançamentos`;
- [ ] o engine não depende de aleatoriedade;
- [ ] nenhuma dependência nova foi adicionada;
- [ ] nenhum cálculo tributário foi antecipado;
- [ ] `pytest` completo passa;
- [ ] o resultado pode alimentar mecanicamente a spec 05.

## Arquivos esperados

```text
src/accounting_sim/posting.py
tests/test_posting.py
```

Atualizar apenas se necessário:

```text
src/accounting_sim/canonical.py
src/accounting_sim/__init__.py
```

## Dependências de outras specs

- spec 00 — fronteira do MVP;
- spec 01 — tipos e nomes;
- spec 02 — contas válidas;
- spec 03 — eventos validados.

A spec 05 deve derivar Diário, Razão e balancete exclusivamente de `LANCAMENTOS`/`PARTIDAS`, sem recomputar regras econômicas a partir de `EVENTOS`.
