# Spec 08 — Interface tributária contrafactual e governança normativa

**Status:** abertura do Marco C revisado  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–07 + Volumes I–III  
**Bloqueia:** specs 09–11 do roadmap revisado

---

# Objetivo

Promover para implementação o contrato conceitual da camada tributária que estava reservado para uma etapa posterior e preparar o sistema para o experimento contrafactual:

```text
base econômico-operacional fixa
    +
perfil factual da entidade eta_t
    +
cenário tributário (rho_t^(s), Theta_t^(s))
    ->
contexto tributário validado
```

A Spec 08 **não calcula tributos**.

Ela implementa somente:

1. a revisão formal do roadmap;
2. os contratos computacionais de `eta_t`, `rho_t`, `Theta_t^tax` e `Prov`;
3. uma extensão fiscal de `EVENTOS` sem modificar o schema contábil da Spec 03;
4. cenários tributários que variam regime e versão normativa sobre a mesma base factual;
5. um repositório tabular de parâmetros normativos com proveniência obrigatória;
6. validações estruturais e referenciais da nova camada;
7. a materialização dessas entradas no workbook;
8. nomes e schemas reservados para os resultados tributários das specs seguintes.

A entrega desta spec deve deixar preparado:

```text
EVENTOS ----------------------+
                              |
EVENTOS_FISCAIS --------------+
                              |
ENTIDADE ---------------------+--> TaxContext validado
                              |
CENARIOS_TRIBUTARIOS ---------+
                              |
FISCAL_PARAM -----------------+
```

sem ainda executar:

```text
mathfrak E
B_j
A_j
C_j
D_j
H^tax
```

O primeiro cálculo tributário concreto pertence à Spec 09.

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

Os principais objetos canônicos envolvidos nesta spec são:

```text
Theta_t^tax
rho_t
eta_t
zeta_t
bar_zeta_t
chi_t
mathfrak E_t
Theta_t^eff
Prov
u_t^min
```

A Spec 08 não altera nenhum deles.

---

# Evidência canônica da mudança de prioridade

## 1. O experimento contrafactual já existe nos Volumes

O Volume I admite comparar regras tributárias mantendo a atividade fixa:

```text
H^tax(u_t; Theta_old)
versus
H^tax(u_t; Theta_new)
```

O Volume II refina o problema por:

```text
bar_zeta_t
=
(x_t^min, u_t^min, eta_t)
```

e, para cada cenário `s`:

```text
zeta_t^(s)
=
(bar_zeta_t, rho_t^(s))

Y_t^(s)
=
H(zeta_t^(s); Theta_t^(s))
```

Logo, a geração de um novo `u_t` não é pré-condição para esse experimento.

A base econômica pode permanecer fixa enquanto variamos:

```text
rho
Theta
```

---

## 2. A camada contábil existente não deve ser substituída

O Volume III fixa a arquitetura paralela:

```text
ramo contábil:
(P_t, u_t)
    -> Lambda_t
    -> Raz_t
    -> b_t
    -> S_t

ramo tributário:
(x_t^min, u_t^min, rho_t, eta_t; Theta_t^eff)
    -> H^tax
    -> Y_t^tax
```

A Spec 08 deve preservar essa separação.

Não criar:

```text
motor contábil-tributário híbrido
```

Não inserir lógica tributária em:

```text
events.py
posting.py
ledger.py
statements.py
account_mapping.py
chart_of_accounts.py
```

---

## 3. Balancete e DRE não substituem a granularidade dos eventos

O Volume II permite:

```text
A_acct(u_t)
=
A_acct(u_t')
```

e simultaneamente:

```text
H_tax(u_t)
!=
H_tax(u_t')
```

Portanto:

```text
EVENTOS
DOC_REF
ID_ORIGEM
VINCULO_EVENTO_LCTO
```

continuam preservados.

A camada tributária deve consumir os fatos granulares necessários sem reconstruí-los a partir de BP/DRE.

---

## 4. Regime, perfil factual e legislação são objetos distintos

Preservar:

```text
Theta_t^tax
=
legislação/regras disponíveis no sistema normativo

rho_t
=
configuração tributária do cenário

eta_t
=
fatos da entidade

Theta_t^eff
=
regras efetivamente aplicáveis depois da seleção
```

Não fundir esses quatro objetos.

---

# Revisão oficial do roadmap

A implementação da Spec 08 deve atualizar `specs/README_specs_plan.md`.

O roadmap anterior:

```text
08 -> geração sintética
09 -> validade/verossimilhança
10 -> demo end-to-end
11 -> interface tributária
```

é substituído por:

| Spec | Questão | Produto |
|---|---|---|
| 00–07 | já implementadas | núcleo contábil + workbook + BP/DRE |
| **08** | Como representar fatos fiscais, entidade, regime, versão normativa e proveniência? | **interface tributária contrafactual** |
| **09** | Como selecionar regras efetivas e calcular um primeiro recorte tributário? | **motor tributário mínimo** |
| **10** | Como executar vários pares `(rho, Theta)` sobre a mesma base? | **experimento contrafactual** |
| **11** | Como comparar resultados e produzir uma decisão auditável? | **comparação/relatório de cenários** |
| posterior | Como gerar/projetar novas bases econômicas? | geração sintética, calibração e projeção |

---

# Marcos revisados

## Marco A — núcleo contábil mínimo

Specs 00–05.

Status:

```text
concluído
```

## Marco B — workbook e demonstrações

Specs 06–07.

Status:

```text
concluído
```

## Marco C — experimento tributário contrafactual

Specs 08–11.

Alvo:

```text
bar_zeta_t
+
(rho_t^(s), Theta_t^(s))
    ->
Y_t^(s)
```

## Marco D — projeção/geração de bases econômicas

Fase posterior.

Alvo futuro:

```text
Omega^sim
    ->
u_t^(Omega^sim)
```

A geração sintética não foi descartada.

Ela apenas deixa o caminho crítico atual.

---

# Atualização da Spec 00

`specs/00_mvp_scope.md` descreve corretamente a fronteira histórica do MVP contábil inicial.

Não apagar seu histórico.

Adicionar um adendo de transição deixando explícito:

```text
Specs 00–07
=
MVP contábil concluído

Specs 08–11
=
MVP tributário contrafactual
```

A antiga seção que colocava tributação fora do escopo deve permanecer interpretada como:

```text
fora do escopo do MVP contábil inicial
```

e não como proibição permanente do projeto.

---

# Atualização da Spec 01

Alguns nomes que estavam reservados passam a possuir representação concreta.

Atualizar o dicionário canônico para refletir:

| Formalismo | Python | Representação Spec 08 | Excel |
|---|---|---|---|
| `eta_t` | `entity_profile` | `DataFrame` normalizado | `ENTIDADE` |
| `rho_t` | `tax_scenarios` / linha de cenário | campos por eixo | `CENARIOS_TRIBUTARIOS` |
| `Theta_t^tax` | `tax_parameters` | parâmetros versionados | `FISCAL_PARAM` |
| `u_t^min` | `events + fiscal_event_attributes` | composição lógica | `EVENTOS` + `EVENTOS_FISCAIS` |
| `zeta_t` | `tax_context` / composição lógica | não é tabela única | composição |
| `bar_zeta_t` | `fixed_tax_base` | composição lógica fixa | composição |
| `Prov` | proveniência normativa | colunas de `FISCAL_PARAM` | `FISCAL_PARAM` |
| `chi_t` | `tax_regime_admissibility` | **reservado para Spec 09** | derivado futuro |
| `mathfrak E_t` | `effective_tax_rule_selector` | **reservado para Spec 09** | derivado futuro |
| `Theta_t^eff` | `effective_tax_rules` | **reservado para Spec 09** | derivado futuro |

A Spec 08 implementa os dados necessários para `chi_t` e `mathfrak E_t`.

Ela não implementa esses operadores.

---

# Regra arquitetural central — base factual fixa

O contrafactual da fase atual deve satisfazer:

```text
EVENTOS^(s)
=
EVENTOS

EVENTOS_FISCAIS^(s)
=
EVENTOS_FISCAIS

ENTIDADE^(s)
=
ENTIDADE
```

para todos os cenários `s`.

A única variação permitida em `CENARIOS_TRIBUTARIOS` é:

```text
rho_t^(s)
Theta_t^(s)
```

Logo:

```text
bar_zeta_t
```

é fixo.

---

# Consequência física

Não colocar `ID_CENARIO` em:

```text
ENTIDADE
EVENTOS
EVENTOS_FISCAIS
```

O cenário não pode modificar:

```text
valor da operação
quantidade
data do fato
contraparte
local factual
documento
natureza econômica
```

Se uma futura análise quiser modelar reação comportamental da empresa à legislação, isso pertence ao Marco D, não ao contrafactual puro do Marco C.

---

# Decisão arquitetural — `ENTIDADE`

O Volume III havia descrito `ENTIDADE` como uma interface possível para `(eta_t, rho_t)`.

Para o experimento contrafactual, essa materialização é refinada:

```text
ENTIDADE
=
eta_t fixo

CENARIOS_TRIBUTARIOS
=
rho_t^(s) + referência a Theta_t^(s)
```

Motivo:

se `rho` permanecesse dentro de `ENTIDADE`, haveria uma única configuração tributária e não uma família de cenários sobre a mesma entidade.

Essa separação preserva melhor o Volume II.

---

# Decisão arquitetural — `EVENTOS` e `EVENTOS_FISCAIS`

Não alterar `EVENT_COLUMNS`.

A Spec 03 continua autoritativa para `EVENTOS`.

Criar:

```text
EVENTOS
    <--- ID_EVENTO --->
EVENTOS_FISCAIS
```

`EVENTOS_FISCAIS` armazena somente atributos adicionais de natureza factual/documental necessários a cálculos fiscais futuros.

Não armazenar em `EVENTOS_FISCAIS`:

- base calculada;
- alíquota aplicada;
- crédito calculado;
- débito calculado;
- tributo apurado;
- regra efetiva;
- resultado de cenário.

Esses objetos são derivados e pertencem às Specs 09–10.

---

# Por que `EVENTOS_FISCAIS` será normalizado em formato longo

O Volume II estabelece que o conteúdo exato de:

```text
ell_k,t^min
g_k,t
h_k,t
```

depende dos operadores tributários concretos.

Não existe uma lista universal correta de campos fiscais.

Portanto, na Spec 08, usar:

```text
ID_EVENTO
ATRIBUTO_FISCAL
VALOR
TIPO_VALOR
ORIGEM
```

em vez de antecipar colunas como:

```text
NCM
CFOP
CST
UF_ORIGEM
UF_DESTINO
...
```

como se fossem universalmente obrigatórias.

A Spec 09 poderá declarar quais atributos são necessários ao primeiro tributo implementado.

---

# Decisão arquitetural — `FISCAL_PARAM`

`FISCAL_PARAM` representa parâmetros de `Theta_t^tax`.

Não colocar parâmetros normativos em:

```text
canonical.py
tax_context.py
workbook.py
```

como constantes do tipo:

```python
CBS_RATE = ...
IBS_RATE = ...
PRESUMED_PROFIT_RATE = ...
```

`canonical.py` define apenas:

```text
schema
tipos
nomes
contratos
```

Os valores legais serão dados versionados e rastreáveis.

---

# Regra de governança normativa

Todo parâmetro normativo implementado deve satisfazer:

```text
fonte oficial
    ->
dispositivo
    ->
vigência
    ->
regra/parametrização
    ->
versão computacional
    ->
teste
```

Preservar:

```text
Prov(p)
=
(fonte, dispositivo, versão, vigência, data de consulta)
```

e a regra:

```text
para todo p em Theta_t^eff:
Prov(p) != vazio
```

---

# Limite da validação automática

A Spec 08 pode validar estruturalmente:

- existência de fonte;
- tipo da fonte;
- URL não vazia;
- dispositivo não vazio;
- versão não vazia;
- vigência;
- data de consulta;
- versão computacional.

Ela **não deve afirmar automaticamente** que:

```text
a URL é juridicamente oficial
a interpretação está correta
a norma é superior a outra
o dispositivo foi modelado corretamente
```

Essa auditoria normativa é requisito da Spec 09 para cada recorte tributário concreto.

---

# Taxonomia de fontes

Implementar a classificação de engenharia definida no Volume II:

```text
norm
reg
tec
oper
```

correspondendo a:

```text
S^norm
S^reg
S^tec
S^oper
```

Essa classificação:

```text
não é uma nova hierarquia jurídica.
```

Materiais técnicos/operacionais não devem ser tratados como superiores às normas.

---

# Tipos escalares normalizados

Criar um enum reutilizável para valores das novas tabelas:

```python
class ScalarValueType(StrEnum):
    STRING = "str"
    INTEGER = "int"
    DECIMAL = "decimal"
    BOOLEAN = "bool"
    DATE = "date"
```

Internamente:

- valores monetários continuam em `int` centavos;
- taxas/parâmetros decimais futuros devem usar `Decimal`;
- `float` binário não deve ser fonte de verdade normativa;
- `VALOR` nas tabelas genéricas da Spec 08 é persistido como texto + `TIPO_VALOR`.

A conversão efetiva para o tipo consumido por uma regra pertence ao contexto/regra que o lê.

---

# Enums novos

Criar em `canonical.py`:

```python
class ScalarValueType(StrEnum):
    STRING = "str"
    INTEGER = "int"
    DECIMAL = "decimal"
    BOOLEAN = "bool"
    DATE = "date"
```

```python
class TaxSourceType(StrEnum):
    NORMATIVE = "norm"
    REGULATORY = "reg"
    TECHNICAL = "tec"
    OPERATIONAL = "oper"
```

Não criar ainda enums para:

```text
Simples Nacional
Lucro Real
Lucro Presumido
IBS
CBS
IRPJ
CSLL
```

Esses valores pertencem ao recorte normativo concreto.

Na Spec 08, identificadores de regime e tributo continuam strings governadas pelos dados futuros.

---

# Schema — `ENTIDADE`

Constante:

```python
ENTITY_PROFILE_COLUMNS = (
    "ID_ENTIDADE",
    "ATRIBUTO",
    "VALOR",
    "TIPO_VALOR",
    "ORIGEM",
)
```

Representação:

```text
entity_profile: DataFrame
```

Chave:

```text
(ID_ENTIDADE, ATRIBUTO)
```

---

# Invariantes — `ENTIDADE`

## E1 — formato longo

Uma linha representa:

```text
um fato da entidade
```

A Spec 08 não define lista obrigatória de `ATRIBUTO`.

## E2 — uma única entidade por workbook

Enquanto o MVP permanecer de entidade única:

```text
nunique(ID_ENTIDADE) <= 1
```

Se houver cenários tributários, deve existir exatamente uma entidade.

## E3 — atributo único

Não permitir duplicidade de:

```text
(ID_ENTIDADE, ATRIBUTO)
```

## E4 — tipo válido

`TIPO_VALOR` deve pertencer a `ScalarValueType`.

## E5 — origem

`ORIGEM` continua usando o enum `Origin`.

## E6 — sem regime

Não adicionar colunas:

```text
REGIME_*
ID_CENARIO
```

em `ENTIDADE`.

`eta_t` não é `rho_t`.

---

# Schema — `EVENTOS_FISCAIS`

Constante:

```python
FISCAL_EVENT_ATTRIBUTE_COLUMNS = (
    "ID_EVENTO",
    "ATRIBUTO_FISCAL",
    "VALOR",
    "TIPO_VALOR",
    "ORIGEM",
)
```

Representação:

```text
fiscal_event_attributes: DataFrame
```

Chave:

```text
(ID_EVENTO, ATRIBUTO_FISCAL)
```

---

# Invariantes — `EVENTOS_FISCAIS`

## F1 — FK

Todo:

```text
ID_EVENTO
```

deve existir em `EVENTOS`.

## F2 — não exige uma linha por evento

Eventos sem atributos fiscais adicionais são permitidos nesta spec.

A Spec 09 poderá exigir determinados atributos de acordo com:

```text
Dep(H)
```

do primeiro cálculo tributário.

## F3 — atributo único por evento

Não permitir duplicidade de:

```text
(ID_EVENTO, ATRIBUTO_FISCAL)
```

## F4 — sem cenário

Não existe:

```text
ID_CENARIO
```

nesta tabela.

Isso é obrigatório para preservar o contrafactual com fatos fixos.

## F5 — sem resultados fiscais

Não armazenar resultados derivados nessa tabela.

---

# Schema — `CENARIOS_TRIBUTARIOS`

Constante:

```python
TAX_SCENARIO_COLUMNS = (
    "ID_CENARIO",
    "ID_ENTIDADE",
    "DESCRICAO",
    "E_BASELINE",
    "DT_REFERENCIA_NORMATIVA",
    "REGIME_ENTIDADE",
    "REGIME_IR",
    "REGIME_CONSUMO",
    "REGIME_ESPECIAL",
    "ID_VERSAO_NORMATIVA",
    "ATIVO",
)
```

Representação:

```text
tax_scenarios: DataFrame
```

---

# Relação com `rho_t`

Uma linha materializa:

```text
rho_t^(s)
=
(
REGIME_ENTIDADE,
REGIME_IR,
REGIME_CONSUMO,
REGIME_ESPECIAL
)
```

A Spec 09 definirá os valores válidos do primeiro recorte normativo.

---

# Relação com `Theta_t^(s)`

A coluna:

```text
ID_VERSAO_NORMATIVA
```

seleciona um conjunto de linhas em:

```text
FISCAL_PARAM
```

A seleção efetiva de regras aplicáveis ainda não é `mathfrak E_t`.

Nesta spec há apenas referência estrutural ao bundle normativo.

---

# Invariantes — `CENARIOS_TRIBUTARIOS`

## C1 — ID único

`ID_CENARIO` é chave primária.

## C2 — entidade válida

Se a tabela não estiver vazia, `ID_ENTIDADE` deve referenciar a única entidade de `ENTIDADE`.

## C3 — baseline

Se houver cenários ativos:

```text
exatamente um E_BASELINE = True
```

entre as linhas `ATIVO = True`.

## C4 — regime geral presente

`REGIME_ENTIDADE` não pode ser vazio em cenário ativo.

Não validar ainda se esse regime é juridicamente admissível.

Isso pertence a `chi_t` na Spec 09.

## C5 — versão normativa

`ID_VERSAO_NORMATIVA` deve ser não vazio.

Se houver cenários, a versão referenciada deve existir em `FISCAL_PARAM`.

## C6 — data normativa

`DT_REFERENCIA_NORMATIVA` é `datetime.date`.

Não exigir que coincida com o período contábil.

## C7 — sem atributos econômicos

Não incluir colunas de receita, custos, preços, quantidades ou valores de eventos em `CENARIOS_TRIBUTARIOS`.

---

# Schema — `FISCAL_PARAM`

Constante:

```python
TAX_PARAMETER_COLUMNS = (
    "ID_PARAM",
    "ID_VERSAO_NORMATIVA",
    "ID_REGRA",
    "TRIBUTO",
    "CHAVE_PARAM",
    "VALOR",
    "TIPO_VALOR",
    "TIPO_FONTE",
    "FONTE_TITULO",
    "FONTE_URL",
    "DISPOSITIVO",
    "VERSAO_NORMA",
    "VIG_INI",
    "VIG_FIM",
    "DATA_CONSULTA",
    "VERSAO_REGRA",
)
```

Representação:

```text
tax_parameters: DataFrame
```

---

# Invariantes — `FISCAL_PARAM`

## P1 — parâmetro único

`ID_PARAM` é chave primária.

## P2 — identificação semântica

Devem ser não vazios:

```text
ID_VERSAO_NORMATIVA
ID_REGRA
TRIBUTO
CHAVE_PARAM
VALOR
TIPO_VALOR
```

## P3 — tipo do valor

`TIPO_VALOR` deve ser válido em `ScalarValueType`.

`VALOR` é persistido como texto.

## P4 — proveniência obrigatória

Toda linha deve possuir:

```text
TIPO_FONTE
FONTE_TITULO
FONTE_URL
DISPOSITIVO
VERSAO_NORMA
VIG_INI
DATA_CONSULTA
VERSAO_REGRA
```

## P5 — vigência

`VIG_INI` é obrigatória.

`VIG_FIM` pode ser nula.

Se presente:

```text
VIG_FIM >= VIG_INI
```

## P6 — fonte

`TIPO_FONTE` pertence a `TaxSourceType`.

A validação estrutural pode exigir `FONTE_URL` não vazia, mas não deve inferir conformidade jurídica apenas pelo domínio.

## P7 — sem parâmetros reais default

A implementação default da Spec 08 deve criar `FISCAL_PARAM` vazio com schema válido.

Não preencher valores legais reais nesta spec.

---

# Schemas reservados para resultados futuros

A Spec 08 deve reservar nomes canônicos, mas não gerar resultados.

## Resultado por operação

```python
TAX_OPERATION_RESULT_COLUMNS = (
    "ID_CENARIO",
    "ID_EVENTO",
    "TRIBUTO",
    "INCIDE",
    "BASE_CENTS",
    "ALIQUOTA",
    "CREDITO_CENTS",
    "DEBITO_CENTS",
    "VERSAO_REGRA",
)
```

## Apuração por cenário e tributo

```python
TAX_ASSESSMENT_RESULT_COLUMNS = (
    "ID_CENARIO",
    "TRIBUTO",
    "S_APUR_CENTS",
    "T_RECOLHER_CENTS",
    "P_CASH_CENTS",
    "E_DRE_CENTS",
    "C_SALDO_CENTS",
    "VERSAO_REGRA",
)
```

## Comparação de cenários

```python
COUNTERFACTUAL_COMPARISON_COLUMNS = (
    "ID_CENARIO_BASE",
    "ID_CENARIO",
    "TRIBUTO",
    "DELTA_S_APUR_CENTS",
    "DELTA_T_RECOLHER_CENTS",
    "DELTA_P_CASH_CENTS",
    "DELTA_E_DRE_CENTS",
    "DELTA_C_SALDO_CENTS",
)
```

Esses schemas são somente contratos de nomes.

Não materializar as tabelas correspondentes nesta spec.

---

# Nomes de abas futuras reservadas

Não criar ainda:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

A escolha de `FISCAL_RESULTADOS_OPERACAO` evita reutilizar `FISCAL_OPERACOES` com significado ambíguo.

O Volume III usou `FISCAL_OPERACOES` como candidato para atributos fiscais consumidos pelos operadores.

Nesta spec, essa função de entrada é cumprida por `EVENTOS_FISCAIS`.

---

# `TaxContext`

Criar:

```text
src/accounting_sim/tax_context.py
```

```python
@dataclass(frozen=True)
class TaxContext:
    entity_profile: pd.DataFrame
    fiscal_event_attributes: pd.DataFrame
    tax_scenarios: pd.DataFrame
    tax_parameters: pd.DataFrame
```

O objeto agrupa entradas.

Não representa `Theta_t^eff` nem `Y_t^tax`.

---

# API mínima de `tax_context.py`

Implementar:

```python
def build_empty_tax_context() -> TaxContext:
    ...
```

```python
def validate_entity_profile(
    entity_profile: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def validate_fiscal_event_attributes(
    fiscal_event_attributes: pd.DataFrame,
    events: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def validate_tax_parameters(
    tax_parameters: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def validate_tax_scenarios(
    tax_scenarios: pd.DataFrame,
    entity_profile: pd.DataFrame,
    tax_parameters: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def validate_tax_context(
    tax_context: TaxContext,
    events: pd.DataFrame,
) -> ValidationReport:
    ...
```

---

# Não implementar na Spec 08

Não criar funções com comportamento jurídico real para:

```python
tax_regime_admissibility(...)
effective_tax_rule_selector(...)
calculate_tax_base(...)
calculate_tax_rate(...)
calculate_tax_credit(...)
calculate_tax_debit(...)
calculate_tax_assessment(...)
run_counterfactual(...)
```

Os nomes conceituais podem ser documentados na Spec 01, mas não devem ter implementações falsas.

---

# `ValidationIssue` — extensão de rastreabilidade

Estender sem quebrar campos anteriores:

```python
@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    account_code: str | None = None
    event_id: str | None = None
    entry_id: str | None = None
    posting_id: str | None = None
    entity_id: str | None = None
    scenario_id: str | None = None
    tax_param_id: str | None = None
```

Os novos campos devem ser adicionados ao final.

---

# Workbook — princípio de integração

A arquitetura passa a ser:

```text
                       +-> escrituração -> Razão -> BP/DRE
                       |
EVENTOS ---------------+
                       |
EVENTOS_FISCAIS -------+-> contexto tributário validado
ENTIDADE --------------+
CENARIOS_TRIBUTARIOS --+
FISCAL_PARAM ----------+
```

A geração do workbook continua sem cálculo tributário.

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
    tax_context: TaxContext | None = None
```

Se `tax_context is None`, usar `build_empty_tax_context()`.

---

# Workbook — nova versão física

Atualizar:

```text
WORKBOOK_SPEC_VERSION
=
spec_08_excel_workbook_v1
```

Adicionar:

```text
TAX_INTERFACE_SPEC_VERSION
=
spec_08_counterfactual_tax_interface_v1
```

---

# Workbook — ordem das abas

A ordem passa a ser exatamente:

```text
README
CONFIG
ENTIDADE
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
EVENTOS_FISCAIS
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
MAPEAMENTO_DF
BP
DRE
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
VALIDACOES
PROVENIENCIA
```

Não criar nesta spec:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
DFC
DVA
```

---

# Classes das novas abas

`ENTIDADE`: entrada factual.

`EVENTOS_FISCAIS`: entrada factual.

`CENARIOS_TRIBUTARIOS`: entrada contrafactual.

`FISCAL_PARAM`: entrada normativa governada.

Não tratar `FISCAL_PARAM` como uma aba para edição casual.

---

# Fontes de verdade do workbook

Após a Spec 08, as entradas são:

```text
CONFIG
ENTIDADE
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
EVENTOS_FISCAIS
MAPEAMENTO_DF
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
```

Derivadas contábeis permanecem:

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

Não existem saídas tributárias ainda.

---

# Tabelas Excel nomeadas

Adicionar:

```text
tbl_ENTIDADE
tbl_EVENTOS_FISCAIS
tbl_CENARIOS_TRIBUTARIOS
tbl_FISCAL_PARAM
```

Preservar todas as tabelas existentes.

---

# Schemas físicos

## `ENTIDADE`

```text
ID_ENTIDADE
ATRIBUTO
VALOR
TIPO_VALOR
ORIGEM
```

## `EVENTOS_FISCAIS`

```text
ID_EVENTO
ATRIBUTO_FISCAL
VALOR
TIPO_VALOR
ORIGEM
```

## `CENARIOS_TRIBUTARIOS`

```text
ID_CENARIO
ID_ENTIDADE
DESCRICAO
E_BASELINE
DT_REFERENCIA_NORMATIVA
REGIME_ENTIDADE
REGIME_IR
REGIME_CONSUMO
REGIME_ESPECIAL
ID_VERSAO_NORMATIVA
ATIVO
```

## `FISCAL_PARAM`

```text
ID_PARAM
ID_VERSAO_NORMATIVA
ID_REGRA
TRIBUTO
CHAVE_PARAM
VALOR
TIPO_VALOR
TIPO_FONTE
FONTE_TITULO
FONTE_URL
DISPOSITIVO
VERSAO_NORMA
VIG_INI
VIG_FIM
DATA_CONSULTA
VERSAO_REGRA
```

Datas devem persistir como `yyyy-mm-dd`.

`VALOR` permanece textual.

---

# Workbook vazio de tributação

É válido:

```text
ENTIDADE             = vazio
EVENTOS_FISCAIS      = vazio
CENARIOS_TRIBUTARIOS = vazio
FISCAL_PARAM         = vazio
```

desde que os schemas existam.

Nesse caso, `TaxContext` é vazio mas estruturalmente válido.

---

# Workbook tributário configurado

Se `CENARIOS_TRIBUTARIOS` não estiver vazio:

1. `ENTIDADE` deve conter exatamente uma entidade;
2. todos os cenários devem referenciá-la;
3. deve existir exatamente um cenário baseline ativo;
4. cada cenário deve referenciar `ID_VERSAO_NORMATIVA`;
5. a versão normativa referenciada deve existir em `FISCAL_PARAM`;
6. todos os parâmetros devem possuir proveniência estrutural completa.

Isso ainda **não significa** que o cenário é juridicamente admissível.

---

# `VALIDACOES`

Estender as colunas para:

```text
ETAPA
OK
ISSUE_CODE
MENSAGEM
ACCOUNT_CODE
EVENT_ID
ENTRY_ID
POSTING_ID
ENTITY_ID
SCENARIO_ID
TAX_PARAM_ID
```

Adicionar etapas:

```text
ENTIDADE
EVENTOS_FISCAIS
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
CONTEXTO_TRIBUTARIO
```

Manter todas as etapas existentes.

---

# `PROVENIENCIA`

Adicionar:

```text
tax_interface_spec_version
tax_context_configured
tax_normative_versions
```

A proveniência jurídica por parâmetro permanece em `FISCAL_PARAM`.

Não duplicar todas as fontes normativas em `PROVENIENCIA`.

---

# README interno do workbook

Explicar:

## Entradas factuais

```text
ENTIDADE
EVENTOS
EVENTOS_FISCAIS
```

## Entradas contábeis/configuração

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
MAPEAMENTO_DF
```

## Entradas contrafactuais

```text
CENARIOS_TRIBUTARIOS
```

## Entrada normativa governada

```text
FISCAL_PARAM
```

Incluir aviso:

```text
A Spec 08 não calcula tributos.
CENARIOS_TRIBUTARIOS e FISCAL_PARAM apenas preparam o contexto para o motor tributário das specs seguintes.
```

---

# Regeneração do workbook

O fluxo contábil permanece:

```text
inputs contábeis
    ->
post_events
    ->
journal
    ->
ledger
    ->
trial balance
    ->
BP/DRE
```

Em paralelo:

```text
ENTIDADE
EVENTOS_FISCAIS
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
    ->
validate_tax_context
```

Não existe dependência `tax context -> posting` na Spec 08.

---

# Invariante de separação contábil-tributária

Para duas entradas que diferem apenas em:

```text
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
```

deve valer:

```text
accounting_core(input_1)
=
accounting_core(input_2)
```

para:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
BP
DRE
```

Esse é um teste obrigatório.

---

# Invariante de base fixa

Para todos os cenários no mesmo workbook:

```text
entity_profile
events
fiscal_event_attributes
```

são compartilhados.

Não duplicar esses objetos por cenário.

---

# Invariante de ausência de cálculo fiscal

Após `build_workbook()` na Spec 08:

```text
não existe valor calculado de imposto
não existe base fiscal calculada
não existe alíquota efetiva calculada
não existe crédito fiscal calculado
não existe débito fiscal calculado
não existe apuração tributária
não existe ranking de regimes
```

---

# Relação futura com `chi_t`

A Spec 08 fornece:

```text
eta_t
rho_t^(s)
Theta_t^(s)
```

necessários a:

```text
chi_t(rho; eta_t, Theta_t^tax)
```

Mas não determina admissibilidade.

Na Spec 09, antes de executar qualquer cenário, deverá ser exigido `chi_t = 1` ou o cenário deverá ser rejeitado.

---

# Relação futura com `mathfrak E_t`

A Spec 08 fornece:

```text
tax_parameters
tax_scenarios
entity_profile
```

A Spec 09 implementará para o primeiro recorte:

```text
Theta_t^tax
    +
rho_t
    +
eta_t
    ->
Theta_t^eff
```

Nenhuma regra deve ser considerada efetiva nesta spec.

---

# Relação futura com `u_t^min`

Nesta spec:

```text
u_t^min
```

é uma composição lógica candidata de:

```text
EVENTOS
+
EVENTOS_FISCAIS
```

A suficiência só pode ser julgada quando o primeiro `H^tax` concreto existir.

Portanto não declarar que os campos da Spec 08 são suficientes para qualquer tributo.

---

# `x_t^min`

A Spec 08 não cria uma aba adicional para estados fiscais intertemporais.

Se a Spec 09 escolher um recorte que dependa de créditos carregados, prejuízos fiscais, base negativa ou saldo fiscal anterior, ela deverá introduzir explicitamente o estado necessário.

---

# Dados normativos concretos

A Spec 08 não deve adicionar arquivos contendo:

- alíquotas reais;
- percentuais presumidos;
- limites legais;
- tratamentos de IBS/CBS;
- regras de crédito;
- critérios reais de Lucro Real;
- critérios reais de Lucro Presumido;
- regras do Simples.

O primeiro conjunto normativo real será produto da auditoria da Spec 09.

---

# Protocolo obrigatório para a Spec 09

Antes de um parâmetro real entrar no motor:

```text
1. consultar fonte oficial vigente;
2. identificar dispositivo;
3. identificar vigência;
4. separar norma de interpretação/modelagem;
5. formalizar a regra;
6. registrar Prov(p);
7. criar caso de teste derivado da regra;
8. somente então implementar o cálculo.
```

A Spec 08 deve registrar essa política no roadmap.

---

# API pública

Exportar via `__init__.py`:

```text
ScalarValueType
TaxSourceType

ENTITY_PROFILE_COLUMNS
FISCAL_EVENT_ATTRIBUTE_COLUMNS
TAX_SCENARIO_COLUMNS
TAX_PARAMETER_COLUMNS

TAX_OPERATION_RESULT_COLUMNS
TAX_ASSESSMENT_RESULT_COLUMNS
COUNTERFACTUAL_COMPARISON_COLUMNS

TaxContext
build_empty_tax_context
validate_entity_profile
validate_fiscal_event_attributes
validate_tax_parameters
validate_tax_scenarios
validate_tax_context

TAX_INTERFACE_SPEC_VERSION
```

---

# Testes obrigatórios — `test_canonical.py`

Atualizar para verificar:

1. valores de `ScalarValueType`;
2. valores de `TaxSourceType`;
3. schemas novos são tuples;
4. ordem exata de `ENTITY_PROFILE_COLUMNS`;
5. ordem exata de `FISCAL_EVENT_ATTRIBUTE_COLUMNS`;
6. ordem exata de `TAX_SCENARIO_COLUMNS`;
7. ordem exata de `TAX_PARAMETER_COLUMNS`;
8. schemas reservados de resultados;
9. `ValidationIssue` preserva campos anteriores;
10. novos campos de rastreabilidade existem;
11. nenhuma colisão com nomes canônicos proibidos.

---

# Testes obrigatórios — `test_tax_context.py`

Criar:

```text
tests/test_tax_context.py
```

Cobrir pelo menos:

1. contexto vazio é válido;
2. `build_empty_tax_context()` retorna schemas exatos;
3. `ENTIDADE` aceita formato longo;
4. duplicidade `(ID_ENTIDADE, ATRIBUTO)` é rejeitada;
5. múltiplos `ID_ENTIDADE` são rejeitados no MVP;
6. `TIPO_VALOR` inválido é rejeitado;
7. `ORIGEM` inválida é rejeitada;
8. `EVENTOS_FISCAIS` aceita tabela vazia;
9. FK `ID_EVENTO` inexistente é rejeitada;
10. duplicidade `(ID_EVENTO, ATRIBUTO_FISCAL)` é rejeitada;
11. schema de `EVENTOS_FISCAIS` não contém `ID_CENARIO`;
12. `ID_CENARIO` é único;
13. cenário sem entidade válida é rejeitado;
14. cenário ativo sem `REGIME_ENTIDADE` é rejeitado;
15. cenário sem versão normativa é rejeitado, ainda que inativo;
16. zero baselines entre cenários ativos é rejeitado;
17. mais de um baseline ativo é rejeitado;
18. um baseline ativo é aceito;
19. versão normativa inexistente é rejeitada quando há cenários;
20. `ID_PARAM` duplicado é rejeitado;
21. parâmetro sem proveniência obrigatória é rejeitado;
22. tipo de fonte inválido é rejeitado;
23. `VIG_FIM < VIG_INI` é rejeitado;
24. `VIG_FIM = None` é aceito;
25. fixtures de valor decimal são tratadas como texto + tipo;
26. `validate_tax_context()` agrega falhas dos componentes;
27. um contexto estrutural completo de teste é aceito.

Os fixtures devem usar identificadores claramente artificiais:

```text
TRIBUTO_TESTE
REGIME_TESTE
VERSAO_TESTE
```

e não simular legislação real.

---

# Testes obrigatórios — workbook

Atualizar `tests/test_workbook.py`.

Cobrir adicionalmente:

1. versão física da Spec 08;
2. ordem exata das 20 abas;
3. novas tabelas nomeadas;
4. workbook pode ser criado com contexto tributário vazio;
5. workbook vazio pode ser reaberto pelo `openpyxl`;
6. `load_workbook_inputs()` recupera `TaxContext`;
7. round-trip de `ENTIDADE`;
8. round-trip de `EVENTOS_FISCAIS`;
9. round-trip de `CENARIOS_TRIBUTARIOS`;
10. round-trip de `FISCAL_PARAM`;
11. datas normativas retornam como `date`;
12. booleanos retornam como `bool`;
13. `VALOR` genérico volta como texto;
14. `EVENTOS` permanece com schema da Spec 03;
15. `EVENTOS_FISCAIS` não altera `EVENTOS`;
16. `VALIDACOES` contém as cinco etapas tributárias;
17. contexto vazio produz apenas validações OK;
18. contexto estrutural de teste produz apenas validações OK;
19. `PROVENIENCIA` registra versão da interface;
20. `PROVENIENCIA` indica corretamente se o contexto está configurado;
21. adulteração manual de BP/DRE continua descartada;
22. alteração de `CENARIOS_TRIBUTARIOS` não muda partidas;
23. alteração de `FISCAL_PARAM` não muda partidas;
24. alteração de `CENARIOS_TRIBUTARIOS` não muda BP/DRE;
25. alteração de `FISCAL_PARAM` não muda BP/DRE;
26. não existem abas de cálculo tributário;
27. não existem fórmulas de cálculo tributário;
28. mesmas entradas geram mesmas tabelas;
29. toda a suíte 00–07 permanece passando.

---

# Teste de separação obrigatório

Construir dois workbooks com a mesma base factual e parametrizações tributárias distintas.

Comparar:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
BP
DRE
```

e exigir igualdade em todas essas abas.

---

# Teste de base fixa obrigatório

Criar dois cenários `S0` e `S1` dentro do mesmo contexto e verificar que não existe duplicação por cenário de:

```text
ENTIDADE
EVENTOS
EVENTOS_FISCAIS
```

---

# Teste de proveniência obrigatório

Criar parâmetro de teste com todos os campos de proveniência.

Remover, um por vez:

```text
FONTE_TITULO
FONTE_URL
DISPOSITIVO
VERSAO_NORMA
VIG_INI
DATA_CONSULTA
VERSAO_REGRA
```

e verificar rejeição.

---

# Regressão do núcleo existente

Baseline esperada antes da implementação:

```text
160 passed
```

O número final naturalmente aumentará.

Nenhum teste das Specs 00–07 pode ser removido.

Preservar:

```text
5 lançamentos
10 partidas

23000000 cents de débitos
23000000 cents de créditos

15000000 cents de saldos devedores
15000000 cents de saldos credores

DRE_RESULTADO_PERIODO = 3000000 cents

BP_ATIVO = 13000000 cents
BP_TOTAL_PASSIVO_PL = 13000000 cents
```

---

# Fora de escopo

Não implementar na Spec 08:

- IBS;
- CBS;
- IRPJ;
- CSLL;
- PIS;
- Cofins;
- ICMS;
- ISS;
- IPI;
- Simples Nacional;
- Lucro Real;
- Lucro Presumido;
- Lucro Arbitrado;
- admissibilidade jurídica real de regimes;
- seletor real de regras efetivas;
- incidência;
- base tributável;
- alíquota efetiva;
- crédito tributário;
- débito tributário;
- apuração;
- obrigação a recolher;
- pagamento de caixa;
- despesa tributária;
- ranking de cenários;
- função-objetivo;
- otimização;
- recomendação de regime;
- DFC;
- DVA;
- geração sintética;
- múltiplas entidades;
- múltiplos períodos;
- banco de dados;
- API;
- ORM;
- engine genérico de regras;
- macros/VBA.

---

# Arquivos que devem permanecer congelados

Não alterar salvo conflito objetivo identificado antes da edição:

```text
src/accounting_sim/events.py
src/accounting_sim/posting.py
src/accounting_sim/ledger.py
src/accounting_sim/statements.py
src/accounting_sim/account_mapping.py
src/accounting_sim/chart_of_accounts.py

tests/test_events.py
tests/test_posting.py
tests/test_ledger.py
tests/test_statements.py
tests/test_account_mapping.py
tests/test_chart_of_accounts.py
```

---

# Arquivos esperados

Criar:

```text
specs/08_counterfactual_tax_interface.md

src/accounting_sim/tax_context.py

tests/test_tax_context.py
```

Alterar:

```text
specs/README_specs_plan.md
specs/00_mvp_scope.md
specs/01_canonical_model.md

README.md
pyproject.toml

src/accounting_sim/canonical.py
src/accounting_sim/workbook.py
src/accounting_sim/__init__.py

tests/test_canonical.py
tests/test_workbook.py
```

---

# `pyproject.toml`

Não adicionar dependência.

Atualizar apenas metadata descritiva para specs 00–08 se aplicável.

---

# README raiz

Registrar:

```text
Marcos A e B concluídos.

A fase atual é o Marco C:
interface e experimento tributário contrafactual
sobre uma base econômico-operacional fixa.
```

Também deixar explícito:

```text
Spec 08 prepara o contexto;
não executa cálculos tributários.
```

---

# Passos de implementação

1. rodar `python -m pytest -q` e registrar baseline;
2. confirmar `main` limpa;
3. atualizar `README_specs_plan.md`;
4. adicionar adendo de transição à Spec 00;
5. atualizar vocabulário da Spec 01;
6. adicionar enums/schemas em `canonical.py`;
7. estender `ValidationIssue`;
8. criar `tax_context.py`;
9. criar `test_tax_context.py`;
10. executar testes de `tax_context`;
11. integrar `TaxContext` a `WorkbookInputs`;
12. atualizar versão física do workbook;
13. adicionar as quatro novas abas;
14. implementar round-trip;
15. estender `VALIDACOES`;
16. estender `PROVENIENCIA`;
17. atualizar README interno do workbook;
18. atualizar testes do workbook;
19. confirmar separação contábil-tributária;
20. atualizar README raiz e metadata;
21. executar suíte completa.

---

# Critérios de aceitação

A Spec 08 está aceita somente se:

- [ ] roadmap foi formalmente revisado;
- [ ] Specs 00–07 continuam semanticamente preservadas;
- [ ] `eta_t` possui representação em `ENTIDADE`;
- [ ] `rho_t^(s)` possui representação em `CENARIOS_TRIBUTARIOS`;
- [ ] `Theta_t^(s)` é referenciado por `ID_VERSAO_NORMATIVA`;
- [ ] parâmetros de `Theta_t^tax` possuem schema em `FISCAL_PARAM`;
- [ ] `Prov(p)` é estruturalmente obrigatório por parâmetro;
- [ ] `EVENTOS` não foi alterado;
- [ ] `EVENTOS_FISCAIS` referencia `EVENTOS` por `ID_EVENTO`;
- [ ] `EVENTOS_FISCAIS` não contém `ID_CENARIO`;
- [ ] `ENTIDADE` não contém regime tributário;
- [ ] cenários não contêm dados econômicos;
- [ ] contexto vazio é válido;
- [ ] contexto de teste configurado é válido;
- [ ] exatamente um baseline ativo é exigido quando há cenários;
- [ ] cenário referencia entidade e versão normativa válidas;
- [ ] `FISCAL_PARAM` rejeita proveniência incompleta;
- [ ] workbook contém exatamente as 20 abas da spec;
- [ ] novas entradas fazem round-trip;
- [ ] núcleo contábil não depende do contexto tributário;
- [ ] alterar cenário não altera partidas/BP/DRE;
- [ ] alterar parâmetros fiscais não altera partidas/BP/DRE;
- [ ] não existe cálculo tributário;
- [ ] não existe parâmetro legal real default;
- [ ] não existe admissibilidade jurídica fictícia;
- [ ] não existe engine genérico de regras;
- [ ] não existe geração sintética;
- [ ] toda a suíte passa.

---

# Definition of done

Ao final da Spec 08, deve ser possível representar e validar:

```text
bar_zeta_t
=
(
u_t^min,
eta_t
)
```

no recorte sem estado fiscal intertemporal, junto de uma coleção:

```text
{
(rho_t^(s), Theta_t^(s))
}_s
```

com proveniência normativa estruturada.

Ainda não deve ser possível perguntar:

```text
"quanto de IBS/CBS/IRPJ/CSLL devo pagar?"
```

A pergunta permitida ao fim desta etapa é:

```text
"o conjunto de fatos, cenários e parâmetros normativos
necessários ao futuro cálculo está estruturalmente representado,
rastreável e separado do núcleo contábil?"
```

A resposta deve ser `sim` quando todas as validações forem satisfeitas.

---

# Ponte para a Spec 09

A Spec 09 escolherá **um primeiro recorte tributário concreto**.

Antes de escrevê-la será obrigatório:

1. consultar novamente fontes oficiais vigentes;
2. identificar o tributo/regime mínimo a implementar;
3. construir a matriz:

```text
dispositivo
    ->
condição
    ->
operador
    ->
parâmetro
    ->
Prov(p)
```

4. definir quais atributos de `ENTIDADE` e `EVENTOS_FISCAIS` são realmente exigidos;
5. implementar `chi_t` apenas no recorte escolhido;
6. implementar `mathfrak E_t` apenas no recorte escolhido;
7. só então implementar `B`, `tau`, `C`, `D` e a apuração mínima.

A Spec 09 não deve presumir que os schemas genéricos da Spec 08 já são suficientes para qualquer tributo.
