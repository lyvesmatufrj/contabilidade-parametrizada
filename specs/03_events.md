# Spec 03 — Eventos econômicos `u_t`

**Status:** próxima implementação  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–02 + Volumes I–III  
**Bloqueia:** specs 04–11

## Objetivo

Implementar a família canônica de eventos `u_t` como uma tabela simples, determinística e validada, suficientemente rica para alimentar o primeiro operador de escrituração `\mathcal E_t` sem antecipar a camada tributária.

A entrega deve fornecer:

1. schema canônico mínimo para `EVENTOS`;
2. enumeração pequena de tipos de evento do arquétipo comercial inicial;
3. carga, serialização, normalização e validação;
4. um cenário determinístico legível por humanos;
5. invariantes que garantam que a spec 04 receba dados semanticamente completos.

O objetivo desta spec não é modelar todo o ERP nem toda a realidade econômica. É criar a menor representação operacional que permita demonstrar:

```text
P_t + u_t -> Lambda_t
```

com rastreabilidade e testes.

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
```

A semântica matemática dos volumes prevalece sobre qualquer decisão local desta spec.

### Objeto herdado do Volume I

A operação externa elementar é

```text
T_{k,t} = (d_{k,t}, q_{k,t}, v_{k,t}, s_{k,t}, a_{k,t}, p_{k,t}, ell_{k,t}, ...)
```

com:

```text
d_{k,t}    direção da operação
q_{k,t}    natureza econômica principal
v_{k,t}    valor monetário bruto
s_{k,t}    data/instante
a_{k,t}    contraparte/participante
p_{k,t}    condição de pagamento/recebimento
ell_{k,t}  classificações/códigos/documentação
```

A coleção é uma família finita indexada:

```text
u_t^tr = (T_{k,t})_{k=1}^{n_t}
```

O sistema completo admite:

```text
u_t = u_t^tr ⊔ u_t^adj
```

onde `u_t^adj` contém eventos internos como depreciação e apropriações por competência.

### Relação com o Volume II

O Volume II define `u_t^min` por suficiência funcional. Nesta fase, `EVENTOS` deve conter apenas atributos consumidos pelo motor contábil determinístico da spec 04, mais identificadores e proveniência necessários à auditoria.

Não implementar `rho_t`, `eta_t`, `Theta_t^eff`, bases fiscais ou atributos tributários específicos.

### Relação com o Volume III

`EVENTOS` materializa `u_t` e deve permanecer disponível mesmo depois que `Lambda_t`, `Raz_t` e `b_t` forem derivados. A granularidade do evento não pode ser descartada, pois uma futura camada tributária poderá depender de informação que não sobreviva à agregação contábil.

## Escopo

### Arquétipo

Uma única empresa comercial simples de compra e revenda de mercadorias.

### Horizonte

- uma única entidade;
- um único período contábil por execução;
- eventos determinísticos nesta fase;
- sem geração aleatória;
- sem múltiplas moedas;
- moeda implícita: BRL.

### Tipos de evento obrigatórios

Implementar os seguintes tipos no primeiro ciclo:

```text
aporte_capital
compra_mercadoria_a_vista
compra_mercadoria_a_prazo
pagamento_fornecedor
venda_a_vista
venda_a_prazo
recebimento_cliente
despesa_operacional_a_vista
depreciacao
```

Essa lista fornece cobertura suficiente para caixa/bancos, clientes, fornecedores, estoques, receitas, CMV, despesas e imobilizado.

### Categorias auxiliares mínimas

Para evitar embutir lógica D/C no evento, usar categorias econômicas simples:

```text
MEIO_FINANCEIRO:
    caixa
    banco

CATEGORIA_DESPESA:
    salarios
    aluguel
    utilidades
    juros
```

A spec 04 mapeará essas categorias para `COD_CTA` do plano.

## Fora de escopo

Não implementar nesta spec:

- regras de débito/crédito;
- criação de `LANCAMENTOS` ou `PARTIDAS`;
- estoque por SKU;
- quantidade/unidade de mercadoria;
- custo médio, FIFO ou PEPS;
- notas fiscais reais;
- importação de ECD/ERP;
- centro de custos;
- parcelamento detalhado;
- subledger de clientes/fornecedores;
- contas bancárias individualizadas;
- tributos destacados, créditos fiscais ou apuração;
- `rho_t`, `eta_t` ou `Theta_t^eff`;
- geração estocástica;
- workbook Excel.

## Entradas

### Período

Usar `AccountingPeriod` já definido em `canonical.py`.

### Configuração

Quando necessário para metadados, usar `SimulationConfig` já definido na spec 01. A `seed` existe como campo reservado, mas **não deve ser usada para gerar eventos nesta fase**.

### Arquivo de eventos

O cenário de demonstração deve poder ser carregado de:

```text
data/examples/events_mvp.csv
```

O arquivo deve ser legível manualmente e serializável sem perda semântica relevante.

## Saídas

A representação primária é:

```python
events: pd.DataFrame
```

com exatamente uma linha por evento econômico.

A ordem física do DataFrame não constitui identidade de domínio. `ID_EVENTO` é a chave.

## Schema de dados

Ordem canônica inicial:

| Coluna | Tipo interno | Obrigatória | Semântica |
|---|---|---:|---|
| `ID_EVENTO` | `str` | sim | identificador estável e único |
| `DT_EVENTO` | `date` | sim | materialização de `s_{k,t}` |
| `CLASSE_EVENTO` | enum `TR`/`ADJ` | sim | transação externa ou ajuste interno |
| `TIPO_EVENTO` | enum | sim | tipo operacional da lista do MVP |
| `DIRECAO` | enum `in`/`out`/`na` | sim | materialização simplificada de `d_{k,t}` |
| `NATUREZA` | enum `bem`/`servico`/`financeiro`/`ajuste` | sim | materialização operacional de `q_{k,t}`/extensão |
| `VL_EVENTO_CENTS` | `int` | sim | `v_{k,t}` em centavos, estritamente positivo |
| `VL_CUSTO_CENTS` | `int | None` | condicional | custo associado a venda quando necessário ao CMV |
| `MEIO_FINANCEIRO` | `str | None` | condicional | `caixa` ou `banco` para eventos com liquidação financeira |
| `CATEGORIA_DESPESA` | `str | None` | condicional | categoria econômica para despesa operacional |
| `COD_PART` | `str | None` | não | participante/contraparte simplificado |
| `COND_PAGTO` | enum `vista`/`prazo`/`na` | sim | simplificação de `p_{k,t}` |
| `DOC_REF` | `str | None` | não | referência documental futura/auditável |
| `HIST` | `str` | sim | descrição humana curta |
| `ORIGEM` | enum já existente | sim | `observada`, `sintética`, `template`, `ajustada` |
| `SPEC_VERSION` | `str` | sim | versão da spec usada na construção |

### Decisão monetária

Não usar `float` como fonte de verdade.

```text
VL_EVENTO_CENTS : int
VL_CUSTO_CENTS  : int | None
```

A apresentação em reais pertence às camadas de relatório/Excel.

### Campos nulos

Usar `None` internamente para campos opcionais. CSV pode usar célula vazia.

Não usar string vazia como estado semântico depois da normalização.

## Enumerações mínimas

Adicionar em `canonical.py` apenas se forem efetivamente utilizadas pelo código:

```python
class EventClass(StrEnum):
    TRANSACTION = "TR"
    ADJUSTMENT = "ADJ"

class EventDirection(StrEnum):
    IN = "in"
    OUT = "out"
    NA = "na"

class EventNature(StrEnum):
    GOOD = "bem"
    SERVICE = "servico"
    FINANCIAL = "financeiro"
    ADJUSTMENT = "ajuste"

class PaymentTerm(StrEnum):
    CASH = "vista"
    CREDIT = "prazo"
    NA = "na"

class EventType(StrEnum):
    CAPITAL_CONTRIBUTION = "aporte_capital"
    PURCHASE_CASH = "compra_mercadoria_a_vista"
    PURCHASE_CREDIT = "compra_mercadoria_a_prazo"
    SUPPLIER_PAYMENT = "pagamento_fornecedor"
    SALE_CASH = "venda_a_vista"
    SALE_CREDIT = "venda_a_prazo"
    CUSTOMER_RECEIPT = "recebimento_cliente"
    OPERATING_EXPENSE_CASH = "despesa_operacional_a_vista"
    DEPRECIATION = "depreciacao"
```

Não criar taxonomia extensível de eventos nesta fase.

## Regras / invariantes

### E1 — identidade

`ID_EVENTO` deve ser único, não vazio e estável.

### E2 — período

Todo `DT_EVENTO` deve satisfazer:

```text
start_date <= DT_EVENTO <= end_date
```

para o `AccountingPeriod` da execução.

### E3 — valor

`VL_EVENTO_CENTS` deve ser `int > 0`.

`VL_CUSTO_CENTS`, quando presente, deve ser `int >= 0`.

### E4 — custo de venda

Para:

```text
venda_a_vista
venda_a_prazo
```

`VL_CUSTO_CENTS` é obrigatório e deve satisfazer:

```text
0 < VL_CUSTO_CENTS <= VL_EVENTO_CENTS
```

A desigualdade estrita no limite inferior é uma restrição simplificadora do cenário MVP para preservar a exigência da spec 04 de que toda partida tenha valor positivo; não é uma lei contábil universal.

### E5 — classe

```text
depreciacao -> CLASSE_EVENTO = ADJ
outros tipos do MVP -> CLASSE_EVENTO = TR
```

### E6 — direção

Regras mínimas:

```text
compra_*              -> in
pagamento_fornecedor  -> out
venda_*               -> out
recebimento_cliente   -> in
aporte_capital         -> in
despesa_*             -> out
depreciacao            -> na
```

A direção descreve o fluxo econômico/financeiro do evento em relação à entidade; não é sinônimo de débito/crédito.

### E7 — condição de pagamento

```text
compra_mercadoria_a_vista -> vista
compra_mercadoria_a_prazo -> prazo
venda_a_vista             -> vista
venda_a_prazo             -> prazo
```

Para aporte, pagamentos, recebimentos e ajustes, usar `na` quando a distinção não acrescentar informação.

### E8 — meio financeiro

Obrigatório para eventos que movimentam imediatamente caixa/banco:

```text
aporte_capital
compra_mercadoria_a_vista
pagamento_fornecedor
venda_a_vista
recebimento_cliente
despesa_operacional_a_vista
```

Valores permitidos:

```text
caixa
banco
```

Deve ser `None` para depreciação e pode ser `None` para compra/venda a prazo.

### E9 — categoria de despesa

Obrigatória apenas para `despesa_operacional_a_vista`.

Valores do MVP:

```text
salarios
aluguel
utilidades
juros
```

### E10 — texto de histórico

`HIST` não pode ser vazio. O histórico deve ser informativo, mas não será usado como chave de regra.

### E11 — ausência de semântica tributária

Nenhum campo desta spec pode ser interpretado como base fiscal, alíquota, crédito tributário ou débito tributário.

### E12 — determinismo

Para o mesmo arquivo de entrada e mesmo período, normalização e ordenação devem produzir o mesmo DataFrame.

Ordenação canônica:

```text
DT_EVENTO, ID_EVENTO
```

## API mínima

Implementar em:

```text
src/accounting_sim/events.py
```

API esperada:

```python
def load_events(path: str | Path) -> pd.DataFrame:
    ...


def save_events(df: pd.DataFrame, path: str | Path) -> Path:
    ...


def validate_events(
    df: pd.DataFrame,
    period: AccountingPeriod,
) -> ValidationReport:
    ...


def build_demo_events(period: AccountingPeriod) -> pd.DataFrame:
    ...
```

Reutilizar `ValidationIssue` e `ValidationReport` de modo simples. Se hoje esses tipos estiverem em `chart_of_accounts.py`, é aceitável movê-los para `canonical.py` **somente se isso reduzir duplicação sem alterar a API pública desnecessariamente**.

Não criar framework genérico de schemas.

## Cenário determinístico obrigatório

`build_demo_events()` deve produzir um cenário com pelo menos:

```text
E001  aporte de capital
E002  compra de mercadoria a prazo
E003  pagamento parcial de fornecedor
E004  venda à vista com custo
E005  venda a prazo com custo
E006  recebimento de cliente
E007  despesa operacional a vista
E008  depreciação
```

Os valores podem ser simples e redondos. O cenário deve garantir que a spec 04 consiga gerar lançamentos sem depender de regras tributárias.

Além disso, os testes da etapa devem incluir o exemplo canônico do Volume III:

```text
aporte de capital      100000
compra à vista          30000
venda a prazo           50000  custo 20000
recebimento cliente     30000
```

## Passos de implementação

1. ler e preservar as convenções de `canonical.py`;
2. adicionar enums mínimos de evento;
3. declarar `EVENT_COLUMNS` como tupla imutável;
4. implementar normalização de strings, datas, inteiros e nulos;
5. implementar loader e saver CSV;
6. implementar `validate_events()`;
7. implementar `build_demo_events()`;
8. criar `data/examples/events_mvp.csv` a partir do mesmo schema;
9. escrever testes positivos e negativos;
10. executar a suíte existente para garantir ausência de regressões.

## Casos de exemplo

### Evento válido — compra a prazo

```text
ID_EVENTO=E002
TIPO_EVENTO=compra_mercadoria_a_prazo
CLASSE_EVENTO=TR
DIRECAO=in
NATUREZA=bem
VL_EVENTO_CENTS=3000000
COND_PAGTO=prazo
```

### Evento válido — depreciação

```text
ID_EVENTO=E008
TIPO_EVENTO=depreciacao
CLASSE_EVENTO=ADJ
DIRECAO=na
NATUREZA=ajuste
VL_EVENTO_CENTS=20000
COND_PAGTO=na
MEIO_FINANCEIRO=null
```

### Evento inválido — venda sem custo

`venda_a_prazo` com `VL_CUSTO_CENTS=None` deve falhar com issue:

```text
missing_sale_cost
```

### Evento inválido — data fora do período

Deve falhar com:

```text
event_outside_period
```

### Evento inválido — tipo desconhecido

Deve falhar com:

```text
invalid_event_type
```

## Testes obrigatórios

Criar `tests/test_events.py` cobrindo pelo menos:

1. colunas canônicas na ordem definida;
2. IDs únicos;
3. datas convertidas para `date`;
4. valores monetários convertidos para `int` sem `float`;
5. rejeição de valores não positivos;
6. rejeição de evento fora do período;
7. validação da classe `TR/ADJ`;
8. validação da direção por tipo;
9. validação da condição de pagamento;
10. meio financeiro obrigatório quando aplicável;
11. categoria de despesa obrigatória quando aplicável;
12. custo obrigatório para vendas;
13. cenário de demonstração completo é válido;
14. salvar e recarregar CSV preserva IDs, datas e valores;
15. ordenação determinística por data e ID.

## Critérios de aceitação

A spec 03 está aceita se:

- [ ] `build_demo_events()` retorna um `DataFrame` válido;
- [ ] `validate_events(...).ok is True` para o cenário padrão;
- [ ] todos os cenários inválidos obrigatórios são detectados;
- [ ] nenhum lançamento foi criado nesta spec;
- [ ] nenhuma regra tributária foi introduzida;
- [ ] o arquivo CSV pode ser entendido sem Python;
- [ ] a suíte `pytest` completa continua passando;
- [ ] `EVENTOS` contém informação suficiente para as regras determinísticas da spec 04.

## Arquivos esperados

```text
src/accounting_sim/events.py
data/examples/events_mvp.csv
tests/test_events.py
```

Atualizar apenas se necessário:

```text
src/accounting_sim/canonical.py
src/accounting_sim/__init__.py
```

## Dependências de outras specs

- spec 00 — escopo e simplicidade;
- spec 01 — tipos, moeda, datas e vocabulário;
- spec 02 — plano de contas disponível para a próxima etapa.

A spec 04 deve consumir `events` e `chart_of_accounts` por suas APIs públicas, sem redefinir seus schemas.
