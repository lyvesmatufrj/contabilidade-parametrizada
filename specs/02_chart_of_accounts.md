# Spec 02 — Plano de contas `\mathcal P_t`

**Status:** primeira implementação substancial  
**Prioridade:** bloqueadora  
**Depende de:** specs 00 e 01  
**Bloqueia:** specs 03–07

## Objetivo

Implementar o objeto canônico `\mathcal P_t` — plano de contas — como uma tabela hierárquica validada, simples o suficiente para o MVP e estruturalmente compatível com a prática observada na ECD/SPED.

A entrega deve fornecer:

1. schema canônico do plano;
2. funções de carga e validação;
3. template plausível para uma pequena empresa comercial;
4. testes de hierarquia e integridade;
5. base para lançamentos futuros referirem apenas contas analíticas válidas.

## Contexto canônico

O Volume III define:

```text
mathsf C_t = {a_{1,t}, ..., a_{p_t,t}}

P_t = (
    C_t,
    cod_t,
    nome_t,
    nat_t,
    tipo_t,
    niv_t,
    pai_t,
    map_t
)
```

Interpretação:

```text
cod_t(a)   código único
nome_t(a)  nome da conta
nat_t(a)   natureza/grupo contábil
tipo_t(a)  S = sintética; A = analítica
niv_t(a)   nível hierárquico
pai_t(a)   conta sintética imediatamente superior
map_t(a)   mapeamento para demonstrações/classificações
```

No MVP:

```text
\mathcal P_t <-> DataFrame PLANO_CONTAS
```

## Evidência estrutural

A spec é inspirada no registro **I050 — Plano de Contas** da ECD, que inclui o núcleo:

```text
DT_ALT
COD_NAT
IND_CTA
NIVEL
COD_CTA
COD_CTA_SUP
CTA
```

O Volume III adiciona campos de engenharia necessários ao simulador:

```text
NAT_SALDO_NORMAL
COD_DF
ATIVA
ORIGEM
```

O objetivo **não** é gerar uma ECD nem reproduzir integralmente o I050. O I050 é usado como evidência estrutural de como um plano real é representado.

## Escopo

Implementar apenas:

- naturezas `01`, `02`, `03`, `04` no template inicial;
- contas sintéticas e analíticas;
- hierarquia por `COD_CTA_SUP`;
- mínimo de quatro níveis no template fornecido;
- orientação normal D/C;
- mapeamento simples para BP/DRE;
- vigência por `DT_ALT` e `ATIVA` sem histórico complexo de versões;
- proveniência por `ORIGEM`.

## Fora de escopo

Não implementar agora:

- plano referencial completo (I051);
- centros de custo (I100);
- contas de compensação no template;
- múltiplos planos simultâneos;
- histórico completo de alteração de contas;
- consolidação societária;
- contas bancárias/SKUs como subledger;
- importação de ECD real;
- validação tributária do plano;
- regras de lançamento;
- balancete;
- workbook Excel.

## Schema de dados

A ordem canônica de colunas é:

| Coluna | Tipo Python | Obrigatória | Regra |
|---|---|---:|---|
| `DT_ALT` | `date` | sim | data de inclusão/alteração |
| `COD_NAT` | `str` enum | sim | `01`,`02`,`03`,`04`,`05`,`09`; template usa `01`–`04` |
| `IND_CTA` | `str` enum | sim | `S` ou `A` |
| `NIVEL` | `int` | sim | inteiro >= 1 |
| `COD_CTA` | `str` | sim | chave primária única |
| `COD_CTA_SUP` | `str | None` | condicional | nulo apenas para raiz; caso contrário deve existir |
| `CTA` | `str` | sim | nome não vazio |
| `NAT_SALDO_NORMAL` | `str` enum | sim | `D` ou `C` |
| `COD_DF` | `str | None` | condicional | obrigatório para conta analítica ativa no MVP |
| `ATIVA` | `bool` | sim | conta disponível para uso |
| `ORIGEM` | `str` enum | sim | `observada`, `sintética`, `template`, `ajustada` |

### Chave primária

```text
PK(PLANO_CONTAS) = COD_CTA
```

Não criar `account_id` redundante no MVP.

## Invariantes

### I1 — unicidade

```text
COD_CTA é único e não vazio.
```

### I2 — raiz

Toda conta de `NIVEL = 1`:

```text
COD_CTA_SUP = null
```

Toda conta de `NIVEL > 1`:

```text
COD_CTA_SUP != null
```

### I3 — pai válido

Para toda conta não raiz:

```text
COD_CTA_SUP deve existir em COD_CTA.
```

### I4 — pai sintético

```text
IND_CTA(parent) = "S"
```

### I5 — nível consecutivo

```text
NIVEL(child) = NIVEL(parent) + 1
```

### I6 — aciclicidade

Nenhuma conta pode ser ancestral de si própria.

### I7 — folha analítica

Conta analítica não pode ser pai de outra conta.

### I8 — uso futuro

Somente contas com:

```text
IND_CTA = "A"
ATIVA = True
```

poderão receber partidas na spec 04.

### I9 — mapeamento de demonstração

No template do MVP, toda conta analítica ativa deve ter `COD_DF` preenchido.

Contas sintéticas podem ter `COD_DF = null`.

### I10 — natureza de saldo

`NAT_SALDO_NORMAL` é um atributo de engenharia para apresentação/validação e não substitui `COD_NAT`.

### I11 — origem

O template fornecido deve usar:

```text
ORIGEM = "template"
```

em todas as linhas.

## Naturezas aceitas

Usar os códigos:

```text
01  Ativo
02  Passivo
03  Patrimônio Líquido
04  Contas de Resultado
05  Contas de Compensação
09  Outras
```

O template inicial usa somente `01`–`04`.

## Convenção de saldo normal do template

Regra geral, com exceções explícitas:

```text
Ativo                        -> D
Passivo                      -> C
Patrimônio Líquido           -> C
Receitas                     -> C
Custos/Despesas              -> D
Contra-ativo                 -> C
```

A orientação normal não proíbe saldo oposto em situações reais; ela é usada pelo motor para apresentação e checagens.

## Mapeamento `COD_DF`

Nesta etapa, `COD_DF` é apenas uma chave textual estável para a spec 07.

Não calcular BP/DRE ainda.

Valores sugeridos:

```text
BP_CAIXA
BP_BANCOS
BP_CLIENTES
BP_ESTOQUES
BP_TRIBUTOS_RECUPERAR
BP_IMOBILIZADO
BP_DEPRECIACAO_ACUM
BP_FORNECEDORES
BP_OBRIG_TRAB
BP_OBRIG_TRIB
BP_EMPRESTIMOS
BP_CAPITAL
BP_RESULTADOS_ACUM
DRE_RECEITA_VENDAS
DRE_CMV
DRE_DESP_SALARIOS
DRE_DESP_ALUGUEL
DRE_DESP_UTILIDADES
DRE_DESP_DEPRECIACAO
DRE_DESP_FINANCEIRA
```

## Template inicial obrigatório

Criar `data/templates/chart_of_accounts_commercial.csv` com pelo menos as linhas abaixo.

Todas devem usar `ATIVA=true`, `ORIGEM=template` e uma mesma `DT_ALT` configurável pelo builder. O CSV versionado pode usar `2026-01-01` como data-base do template; `build_default_commercial_chart(effective_date=...)` deve substituir esse valor na geração em memória.

| COD_CTA | NIVEL | IND_CTA | COD_NAT | COD_CTA_SUP | CTA | NAT_SALDO_NORMAL | COD_DF |
|---|---:|---|---|---|---|---|---|
| `1` | 1 | S | 01 |  | Ativo | D |  |
| `1.1` | 2 | S | 01 | `1` | Ativo Circulante | D |  |
| `1.1.01` | 3 | S | 01 | `1.1` | Disponibilidades | D |  |
| `1.1.01.01` | 4 | A | 01 | `1.1.01` | Caixa | D | `BP_CAIXA` |
| `1.1.01.02` | 4 | A | 01 | `1.1.01` | Bancos Conta Movimento | D | `BP_BANCOS` |
| `1.1.02` | 3 | S | 01 | `1.1` | Clientes | D |  |
| `1.1.02.01` | 4 | A | 01 | `1.1.02` | Clientes | D | `BP_CLIENTES` |
| `1.1.03` | 3 | S | 01 | `1.1` | Estoques | D |  |
| `1.1.03.01` | 4 | A | 01 | `1.1.03` | Mercadorias para Revenda | D | `BP_ESTOQUES` |
| `1.1.04` | 3 | S | 01 | `1.1` | Tributos a Recuperar | D |  |
| `1.1.04.01` | 4 | A | 01 | `1.1.04` | Tributos a Recuperar | D | `BP_TRIBUTOS_RECUPERAR` |
| `1.2` | 2 | S | 01 | `1` | Ativo Não Circulante | D |  |
| `1.2.01` | 3 | S | 01 | `1.2` | Imobilizado | D |  |
| `1.2.01.01` | 4 | A | 01 | `1.2.01` | Móveis e Equipamentos | D | `BP_IMOBILIZADO` |
| `1.2.01.02` | 4 | A | 01 | `1.2.01` | (-) Depreciação Acumulada | C | `BP_DEPRECIACAO_ACUM` |
| `2` | 1 | S | 02 |  | Passivo | C |  |
| `2.1` | 2 | S | 02 | `2` | Passivo Circulante | C |  |
| `2.1.01` | 3 | S | 02 | `2.1` | Fornecedores | C |  |
| `2.1.01.01` | 4 | A | 02 | `2.1.01` | Fornecedores | C | `BP_FORNECEDORES` |
| `2.1.02` | 3 | S | 02 | `2.1` | Obrigações Trabalhistas | C |  |
| `2.1.02.01` | 4 | A | 02 | `2.1.02` | Salários a Pagar | C | `BP_OBRIG_TRAB` |
| `2.1.03` | 3 | S | 02 | `2.1` | Obrigações Tributárias | C |  |
| `2.1.03.01` | 4 | A | 02 | `2.1.03` | Tributos a Recolher | C | `BP_OBRIG_TRIB` |
| `2.2` | 2 | S | 02 | `2` | Passivo Não Circulante | C |  |
| `2.2.01` | 3 | S | 02 | `2.2` | Empréstimos e Financiamentos | C |  |
| `2.2.01.01` | 4 | A | 02 | `2.2.01` | Empréstimos Bancários | C | `BP_EMPRESTIMOS` |
| `3` | 1 | S | 03 |  | Patrimônio Líquido | C |  |
| `3.1` | 2 | S | 03 | `3` | Capital | C |  |
| `3.1.01` | 3 | S | 03 | `3.1` | Capital Social | C |  |
| `3.1.01.01` | 4 | A | 03 | `3.1.01` | Capital Social Integralizado | C | `BP_CAPITAL` |
| `3.2` | 2 | S | 03 | `3` | Resultados Acumulados | C |  |
| `3.2.01` | 3 | S | 03 | `3.2` | Lucros ou Prejuízos Acumulados | C |  |
| `3.2.01.01` | 4 | A | 03 | `3.2.01` | Lucros ou Prejuízos Acumulados | C | `BP_RESULTADOS_ACUM` |
| `4` | 1 | S | 04 |  | Contas de Resultado | C |  |
| `4.1` | 2 | S | 04 | `4` | Receitas | C |  |
| `4.1.01` | 3 | S | 04 | `4.1` | Receita Bruta | C |  |
| `4.1.01.01` | 4 | A | 04 | `4.1.01` | Receita de Vendas | C | `DRE_RECEITA_VENDAS` |
| `4.2` | 2 | S | 04 | `4` | Custos | D |  |
| `4.2.01` | 3 | S | 04 | `4.2` | Custo das Mercadorias Vendidas | D |  |
| `4.2.01.01` | 4 | A | 04 | `4.2.01` | Custo das Mercadorias Vendidas | D | `DRE_CMV` |
| `4.3` | 2 | S | 04 | `4` | Despesas Operacionais | D |  |
| `4.3.01` | 3 | S | 04 | `4.3` | Despesas Administrativas | D |  |
| `4.3.01.01` | 4 | A | 04 | `4.3.01` | Salários e Encargos | D | `DRE_DESP_SALARIOS` |
| `4.3.01.02` | 4 | A | 04 | `4.3.01` | Aluguéis | D | `DRE_DESP_ALUGUEL` |
| `4.3.01.03` | 4 | A | 04 | `4.3.01` | Energia e Utilidades | D | `DRE_DESP_UTILIDADES` |
| `4.3.01.04` | 4 | A | 04 | `4.3.01` | Depreciação | D | `DRE_DESP_DEPRECIACAO` |
| `4.3.02` | 3 | S | 04 | `4.3` | Despesas Financeiras | D |  |
| `4.3.02.01` | 4 | A | 04 | `4.3.02` | Juros e Encargos Financeiros | D | `DRE_DESP_FINANCEIRA` |

### Observação sobre verossimilhança

Esse plano é um **template sintético plausível**, não uma afirmação de que empresas reais devam adotar exatamente essas contas ou códigos.

O objetivo da primeira versão é fornecer uma topologia contábil suficiente para validar o motor. A calibração de frequência, profundidade, granularidade e combinações de contas pertence à spec 09.

## API mínima

Implementar em `src/accounting_sim/chart_of_accounts.py`:

```python
def load_chart_of_accounts(path: str | Path) -> pd.DataFrame:
    ...


def validate_chart_of_accounts(df: pd.DataFrame) -> ValidationReport:
    ...


def build_default_commercial_chart(
    effective_date: date,
) -> pd.DataFrame:
    ...


def get_analytic_accounts(df: pd.DataFrame, active_only: bool = True) -> pd.DataFrame:
    ...


def get_account(df: pd.DataFrame, code: str) -> pd.Series:
    ...
```

`ValidationReport` deve ser simples. Sugestão:

```python
@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    account_code: str | None = None

@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    issues: tuple[ValidationIssue, ...]
```

Não criar framework genérico de validação.

## Ordenação

Criar uma ordenação hierárquica determinística dos códigos.

Não assumir que ordenação lexicográfica pura sempre será suficiente.

Exemplo desejado:

```text
1
1.1
1.1.01
1.1.01.01
1.1.01.02
1.1.02
...
2
...
```

Uma função simples que tokenize por `.` é suficiente para o template inicial.

## Passos de implementação

1. importar enums/constantes da spec 01;
2. declarar `CHART_OF_ACCOUNTS_COLUMNS` na ordem canônica;
3. implementar builder do template;
4. implementar serialização CSV;
5. implementar loader do CSV;
6. normalizar tipos sem corrigir valores semanticamente inválidos;
7. implementar validadores dos invariantes I1–I11;
8. implementar consulta de contas analíticas;
9. implementar busca por código;
10. criar testes positivos e negativos.

## Casos de exemplo

### Caso válido

```text
1          Ativo                    S
1.1        Ativo Circulante         S
1.1.01     Disponibilidades         S
1.1.01.01  Caixa                    A
```

Deve passar.

### Pai inexistente

```text
COD_CTA     = 1.1.99.01
COD_CTA_SUP = 1.1.99
```

sem `1.1.99` no plano.

Deve falhar com issue `missing_parent`.

### Pai analítico

Se `1.1.01.01` (Caixa) for pai de outra conta, deve falhar com `analytic_account_has_children`.

### Ciclo

```text
A -> B
B -> A
```

Deve falhar com `hierarchy_cycle`.

### Nível inconsistente

Pai nível 2 com filho nível 4 deve falhar com `invalid_level_transition`.

### Conta analítica sem mapeamento

Conta `A`, ativa, com `COD_DF = null` deve falhar no template MVP com `missing_statement_mapping`.

## Testes obrigatórios

Implementar `tests/test_chart_of_accounts.py` cobrindo pelo menos:

1. builder produz todas as colunas canônicas na ordem definida;
2. `COD_CTA` é único;
3. template completo é válido;
4. todas as contas analíticas do template estão no nível 4;
5. todos os pais existem;
6. todos os pais são sintéticos;
7. nenhuma conta analítica tem filhos;
8. ausência de ciclo;
9. `NIVEL(child) = NIVEL(parent)+1`;
10. `COD_NAT` pertence ao enum;
11. `NAT_SALDO_NORMAL` pertence a D/C;
12. toda conta analítica ativa tem `COD_DF`;
13. `get_analytic_accounts()` retorna somente `IND_CTA=A`;
14. `get_account()` retorna a conta correta;
15. conta inexistente gera erro claro;
16. salvar e recarregar CSV preserva chaves e tipos semanticamente relevantes.

## Critérios de aceitação

A spec 02 está aceita se:

- [ ] `build_default_commercial_chart()` gera o template definido;
- [ ] `validate_chart_of_accounts(template).ok is True`;
- [ ] todos os cenários inválidos dos testes são detectados;
- [ ] o CSV pode ser aberto manualmente e entendido sem Python;
- [ ] nenhuma conta analítica é usada como pai;
- [ ] o schema permanece compatível com a futura aba `PLANO_CONTAS`;
- [ ] nenhum cálculo de lançamento, saldo ou tributo foi antecipado nesta spec;
- [ ] `pytest tests/test_chart_of_accounts.py` passa.

## Arquivos esperados

```text
src/accounting_sim/chart_of_accounts.py
data/templates/chart_of_accounts_commercial.csv
tests/test_chart_of_accounts.py
```

Atualizar apenas se necessário:

```text
src/accounting_sim/canonical.py
```

## Dependências de outras specs

- spec 00 — escopo, stack e regras de simplicidade;
- spec 01 — enums, nomes canônicos e tipos primitivos.

A spec 03 deve consumir o plano apenas por suas interfaces públicas e não redefinir o schema.
