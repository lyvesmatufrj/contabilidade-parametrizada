# Spec 11 — Comparação tributária contrafactual e relatório auditável

**Status:** pronta para implementação  
**Prioridade:** alta  
**Depende de:** Specs 00–10 + Volumes I–III  
**Fecha:** Marco C — experimento tributário contrafactual  
**Motor tributário disponível:** CBS 2026 da Spec 09  
**Executor multi-cenário disponível:** Spec 10  
**Base de implementação auditada:** `7572dbef117a35e5e2d227b7e11b26384b482716`

---

# Objetivo

Fechar o primeiro experimento tributário contrafactual do projeto comparando, de forma puramente derivada e auditável, os resultados já produzidos pela Spec 10.

A Spec 11 deve transformar:

```text
Cbs2026CounterfactualResult
```

em:

```text
COUNTERFACTUAL_COMPARISON
```

e disponibilizar um relatório completo contendo:

```text
TAX_OPERATION_RESULT
+
TAX_ASSESSMENT_RESULT
+
COUNTERFACTUAL_COMPARISON
```

sem recalcular regras tributárias dentro da camada de comparação.

Formalmente, para cada cenário alternativo `s` e cenário baseline `0`:

```text
Delta Y_t^(s)
=
Y_t^(s) - Y_t^(0)
```

onde, no contrato atual:

```text
Y_t^(s)
=
(
    S_APUR_CENTS,
    T_RECOLHER_CENTS,
    P_CASH_CENTS,
    E_DRE_CENTS,
    C_SALDO_CENTS
)
```

A Spec 11 também deve materializar no workbook as três abas reservadas desde a Spec 08:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

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

A Spec 08 permanece autoritativa para:

```text
TaxContext
ENTIDADE
EVENTOS_FISCAIS
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
```

A Spec 09 permanece autoritativa para o cálculo CBS de um cenário:

```text
run_cbs_2026
TAX_OPERATION_RESULT_COLUMNS
TAX_ASSESSMENT_RESULT_COLUMNS
```

A Spec 10 permanece autoritativa para a execução multi-cenário:

```text
Cbs2026CounterfactualResult
run_cbs_2026_counterfactual_experiment
```

A Spec 11 deve consumir a saída da Spec 10 e não copiar nem reinterpretar sua lógica.

---

# Relação formal com o contrafactual

Para o baseline `s=0`:

```text
Y_t^(0)
=
H(
    bar_zeta_t,
    rho_t^(0);
    Theta_t^(0)
)
```

Para um cenário alternativo `s`:

```text
Y_t^(s)
=
H(
    bar_zeta_t,
    rho_t^(s);
    Theta_t^(s)
)
```

A base factual permanece:

```text
bar_zeta_t
```

fixa.

A comparação é:

```text
Delta Y_t^(s)
=
Y_t^(s) - Y_t^(0)
```

com convenção de sinal sempre:

```text
alternativo - baseline
```

Nunca usar:

```text
baseline - alternativo
```

sem alterar explicitamente a definição canônica.

---

# Semântica dos componentes comparados

Para cada cenário alternativo:

```text
DELTA_S_APUR_CENTS
=
S_APUR_CENTS^(s)
-
S_APUR_CENTS^(0)
```

```text
DELTA_T_RECOLHER_CENTS
=
T_RECOLHER_CENTS^(s)
-
T_RECOLHER_CENTS^(0)
```

```text
DELTA_P_CASH_CENTS
=
P_CASH_CENTS^(s)
-
P_CASH_CENTS^(0)
```

quando ambos os valores são conhecidos.

```text
DELTA_E_DRE_CENTS
=
E_DRE_CENTS^(s)
-
E_DRE_CENTS^(0)
```

quando ambos os valores são conhecidos.

```text
DELTA_C_SALDO_CENTS
=
C_SALDO_CENTS^(s)
-
C_SALDO_CENTS^(0)
```

---

# Ausência de informação não é zero

A Spec 09 fixou no primeiro recorte:

```text
P_CASH_CENTS = None
E_DRE_CENTS = None
```

Logo, nesta spec:

```text
DELTA_P_CASH_CENTS = None
DELTA_E_DRE_CENTS = None
```

quando baseline ou cenário alternativo não possuem o componente observado/calculado.

Não fazer:

```text
None -> 0
```

Não fazer:

```text
DELTA_P_CASH_CENTS = 0
DELTA_E_DRE_CENTS = 0
```

apenas porque ambos os lados são `None`.

A igualdade:

```text
desconhecido == desconhecido
```

não implica diferença econômica observada igual a zero.

---

# Interpretação de sinal

A comparação deve ser descritiva.

Por exemplo:

```text
DELTA_T_RECOLHER_CENTS > 0
```

significa apenas:

```text
o cenário alternativo apresenta maior T_RECOLHER que o baseline
```

e não:

```text
o cenário é necessariamente pior
```

Analogamente:

```text
DELTA_C_SALDO_CENTS > 0
```

significa maior saldo credor no cenário alternativo, mas nenhuma preferência normativa/econômica deve ser inferida automaticamente.

---

# Não implementar escolha automática de cenário

O vetor:

```text
Y_t^tax
=
(
    S_apur,
    T_recolher,
    P_cash,
    E_DRE,
    C_saldo
)
```

não possui uma ordem total natural.

Para produzir automaticamente algo como:

```text
melhor cenário
```

seria necessário definir explicitamente:

```text
função de perda
função utilidade
pesos
critério de preferência
restrições da decisão
```

Nenhum desses objetos foi definido nos Volumes ou nas Specs 08–10 para esta etapa.

Portanto, a Spec 11 deve produzir:

```text
suporte auditável à decisão
```

e não:

```text
decisão automática
```

Não criar ranking, score, semáforo ou recomendação de regime.

---

# Limitação metodológica do primeiro relatório

A Spec 10 utiliza inicialmente um cenário-controle estrutural com a mesma regra do baseline.

Logo, é esperado e correto obter:

```text
Delta S_APUR = 0
Delta T_RECOLHER = 0
Delta C_SALDO = 0
Delta P_CASH = None
Delta E_DRE = None
```

Esse resultado valida a camada de comparação, mas não constitui ainda um contrafactual tributário substantivo.

Não inventar:

```text
alíquota fictícia
nova legislação
novo regime
novo documento fiscal
```

para forçar deltas não nulos.

Um contrafactual substantivo será introduzido apenas quando existir um segundo operador/regra juridicamente especificado.

---

# Escopo

Implementar somente:

1. comparação de apurações já produzidas pela Spec 10;
2. deltas cenário alternativo menos baseline;
3. preservação de valores desconhecidos como `None`;
4. validação mínima da estrutura recebida;
5. relatório consolidado imutável;
6. materialização das três abas fiscais reservadas;
7. atualização da proveniência e README do workbook;
8. regeneração determinística dessas abas;
9. atualização do roadmap.

---

# Fora de escopo

Não implementar:

- nova legislação;
- nova regra CBS;
- IBS;
- PIS/Cofins;
- ICMS/ISS;
- Simples Nacional;
- Lucro Real;
- Lucro Presumido;
- nova alíquota;
- reconstrução de documento fiscal;
- comparação por item da NF-e;
- reconciliação contábil da CBS;
- pagamento real;
- DRE tributária;
- função de utilidade;
- função de perda;
- ranking de cenários;
- recomendação automática;
- otimização;
- análise de sensibilidade;
- geração sintética;
- banco;
- API;
- dashboard;
- engine tributário genérico;
- plugin/registry;
- nova auditoria normativa da Spec 09.

Não alterar `docs/tax_sources/**`.

---

# Entrada da camada de comparação

A função pura de comparação recebe:

```python
counterfactual_result: Cbs2026CounterfactualResult
```

Ela não recebe:

```text
events
tax_context
FISCAL_PARAM
```

porque a execução fiscal já aconteceu.

Esse desenho garante a separação:

```text
Spec 09 -> calcular
Spec 10 -> executar cenários
Spec 11 -> comparar
```

---

# Schema canônico de comparação

Usar exatamente o objeto já reservado em `canonical.py`:

```python
COUNTERFACTUAL_COMPARISON_COLUMNS
```

com:

```text
ID_CENARIO_BASE
ID_CENARIO
TRIBUTO
DELTA_S_APUR_CENTS
DELTA_T_RECOLHER_CENTS
DELTA_P_CASH_CENTS
DELTA_E_DRE_CENTS
DELTA_C_SALDO_CENTS
```

Não alterar esse schema nesta spec.

---

# Granularidade da comparação

Produzir:

```text
uma linha por
(cenário alternativo ativo, tributo)
```

O baseline não gera linha de comparação contra si próprio.

Portanto, se:

```text
scenario_ids = (S0, S1, S2)
```

e existe apenas CBS:

```text
COMPARATIVO
=
[
    S0 vs S1 / CBS,
    S0 vs S2 / CBS
]
```

Não produzir:

```text
S0 vs S0
```

---

# Correspondência entre tributos

Para cada cenário alternativo, o conjunto de tributos em `assessment_results` deve coincidir com o conjunto do baseline.

Se houver:

```text
tributo ausente
tributo duplicado
tributo extra
```

a comparação deve ser rejeitada com `SchemaValidationError`.

No primeiro recorte, o conjunto esperado de fato será:

```text
{"CBS"}
```

mas a função de comparação não deve hard-code `"CBS"` para realizar a subtração.

A especificidade CBS permanece no nome da API/relatório porque o executor atual é CBS 2026.

---

# Validação estrutural do resultado da Spec 10

Antes de comparar, verificar no mínimo:

1. `operation_results` possui exatamente `TAX_OPERATION_RESULT_COLUMNS`;
2. `assessment_results` possui exatamente `TAX_ASSESSMENT_RESULT_COLUMNS`;
3. `baseline_scenario_id` pertence a `scenario_ids`;
4. baseline é o primeiro elemento de `scenario_ids`;
5. `scenario_ids` não possui duplicatas;
6. existe exatamente uma linha por `(ID_CENARIO, TRIBUTO)` em `assessment_results`;
7. todos os `scenario_ids` aparecem em `assessment_results`;
8. `assessment_results` não contém cenário fora de `scenario_ids`;
9. cada cenário possui o mesmo conjunto de tributos do baseline;
10. campos monetários comparáveis são `int`/`None`, nunca `float`;
11. `ID_CENARIO_BASE` não é obtido de texto externo; vem de `baseline_scenario_id`.

Não construir um framework genérico de validação.

---

# Semântica de valores monetários

Para:

```text
S_APUR_CENTS
T_RECOLHER_CENTS
C_SALDO_CENTS
```

o resultado atual da Spec 09 deve ser inteiro.

Para:

```text
P_CASH_CENTS
E_DRE_CENTS
```

aceitar:

```text
int
None
```

Nunca aceitar `float` como fonte de verdade monetária.

---

# Função pura de comparação

Criar:

```python
def compare_cbs_2026_counterfactual_result(
    counterfactual_result: Cbs2026CounterfactualResult,
) -> pd.DataFrame:
    ...
```

A função deve:

1. validar a estrutura mínima da entrada;
2. localizar as linhas do baseline;
3. iterar pelos cenários alternativos na ordem de `scenario_ids`;
4. comparar tributo a tributo;
5. calcular deltas com sinal `alternativo - baseline`;
6. preservar `None`;
7. devolver exatamente `COUNTERFACTUAL_COMPARISON_COLUMNS`;
8. ser determinística;
9. não mutar a entrada.

---

# Helper de delta anulável

É permitida uma função local pequena com semântica equivalente a:

```python
def _nullable_delta(
    alternative: int | None,
    baseline: int | None,
) -> int | None:
    if alternative is None or baseline is None:
        return None
    return alternative - baseline
```

Tratar `pd.NA`/`NaN` de objeto como ausência apenas quando vier de leitura tabular compatível.

Não tratar ausência como zero.

---

# Relatório consolidado

Criar:

```python
@dataclass(frozen=True)
class Cbs2026CounterfactualReport:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame
    comparison_results: pd.DataFrame
```

Criar também:

```python
def run_cbs_2026_counterfactual_report(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualReport:
    ...
```

Fluxo:

```text
run_cbs_2026_counterfactual_experiment
    ->
compare_cbs_2026_counterfactual_result
    ->
Cbs2026CounterfactualReport
```

Não chamar `run_cbs_2026()` diretamente na Spec 11.

Isso é importante:

```text
Spec 11 deve depender da Spec 10,
não contornar a Spec 10.
```

---

# Não mutação

A comparação e o relatório não devem mutar:

```text
Cbs2026CounterfactualResult
events
TaxContext
```

Devolver cópias defensivas dos DataFrames no relatório.

---

# Exemplo canônico — cenário-controle estrutural

Suponha:

```text
baseline:
S_APUR_CENTS      = 900
T_RECOLHER_CENTS  = 0
P_CASH_CENTS      = None
E_DRE_CENTS       = None
C_SALDO_CENTS     = 0
```

e o controle estrutural:

```text
S_APUR_CENTS      = 900
T_RECOLHER_CENTS  = 0
P_CASH_CENTS      = None
E_DRE_CENTS       = None
C_SALDO_CENTS     = 0
```

Então:

```text
DELTA_S_APUR_CENTS      = 0
DELTA_T_RECOLHER_CENTS  = 0
DELTA_P_CASH_CENTS      = None
DELTA_E_DRE_CENTS       = None
DELTA_C_SALDO_CENTS     = 0
```

---

# Exemplo unitário de sinal — sem criar legislação fictícia

Para testar somente a aritmética da comparação, é permitido construir diretamente um `Cbs2026CounterfactualResult` sintético de teste.

Exemplo:

```text
baseline:
S_APUR_CENTS = 900

alternativo:
S_APUR_CENTS = 1200
```

Resultado:

```text
DELTA_S_APUR_CENTS = +300
```

Isso testa:

```text
alternativo - baseline
```

sem criar parâmetros fiscais, normas ou cenários jurídicos fictícios no corpus.

Analogamente:

```text
baseline C_SALDO = 500
alternativo C_SALDO = 200
```

produz:

```text
DELTA_C_SALDO = -300
```

---

# Workbook — objetivo

A partir desta spec o workbook passa a materializar as saídas tributárias derivadas.

Adicionar às abas canônicas:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

na ordem:

```text
...
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
VALIDACOES
PROVENIENCIA
```

As três novas abas são:

```text
DERIVADAS
NÃO EDITÁVEIS
```

Não adicionar a `EDITABLE_SHEETS`.

---

# Workbook — nomes de tabela

Adicionar a `TABLE_NAMES`:

```text
FISCAL_RESULTADOS_OPERACAO -> tbl_FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO            -> tbl_FISCAL_APURACAO
COMPARATIVO_CENARIOS       -> tbl_COMPARATIVO_CENARIOS
```

---

# Workbook — colunas de resultados por operação

No Excel usar unidades monetárias em reais, seguindo o padrão das demais abas.

Definir:

```python
FISCAL_OPERATION_WORKBOOK_COLUMNS = (
    "ID_CENARIO",
    "ID_EVENTO",
    "TRIBUTO",
    "INCIDE",
    "BASE",
    "ALIQUOTA",
    "CREDITO",
    "DEBITO",
    "VERSAO_REGRA",
)
```

Mapeamento:

```text
BASE_CENTS    -> BASE
CREDITO_CENTS -> CREDITO
DEBITO_CENTS  -> DEBITO
```

com:

```text
centavos / 100
```

`ALIQUOTA` permanece fração numérica e deve ser formatada no Excel como percentual.

Exemplo:

```text
0.009
```

deve aparecer visualmente como:

```text
0.9000%
```

sem transformar o valor armazenado em `0.9`.

---

# Workbook — colunas de apuração

Definir:

```python
FISCAL_ASSESSMENT_WORKBOOK_COLUMNS = (
    "ID_CENARIO",
    "TRIBUTO",
    "S_APUR",
    "T_RECOLHER",
    "P_CASH",
    "E_DRE",
    "C_SALDO",
    "VERSAO_REGRA",
)
```

Mapear:

```text
S_APUR_CENTS      -> S_APUR
T_RECOLHER_CENTS  -> T_RECOLHER
P_CASH_CENTS      -> P_CASH
E_DRE_CENTS       -> E_DRE
C_SALDO_CENTS     -> C_SALDO
```

Todos os valores conhecidos devem ser convertidos para reais.

Valores `None` devem produzir célula vazia.

Não escrever zero onde o DataFrame possui `None`.

---

# Workbook — colunas de comparação

Definir:

```python
COUNTERFACTUAL_COMPARISON_WORKBOOK_COLUMNS = (
    "ID_CENARIO_BASE",
    "ID_CENARIO",
    "TRIBUTO",
    "DELTA_S_APUR",
    "DELTA_T_RECOLHER",
    "DELTA_P_CASH",
    "DELTA_E_DRE",
    "DELTA_C_SALDO",
)
```

Mapear os campos `_CENTS` canônicos para valores em reais.

Deltas desconhecidos permanecem células vazias.

---

# Workbook — quando executar o relatório tributário

`build_workbook()` deve continuar funcionando para:

```text
TaxContext vazio
zero cenários ativos
um único cenário ativo
```

Nesses casos:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

devem existir com os headers/tabelas corretos, porém sem linhas.

Isso preserva compatibilidade com workbooks da camada estrutural e com a fixture isolada da Spec 09.

Se houver:

```text
>= 2 cenários ativos
```

então o workbook deve tratar o contexto como solicitação de experimento contrafactual e executar:

```text
run_cbs_2026_counterfactual_report
```

sobre os eventos normalizados e o `TaxContext` validado.

Se esse experimento for inválido:

```text
build_workbook deve falhar
```

em vez de produzir resultados fiscais parciais ou silenciosamente vazios.

---

# Workbook — não recalcular duas vezes

Dentro de uma única chamada a:

```python
build_workbook()
```

o relatório tributário deve ser executado no máximo uma vez.

Depois, reutilizar:

```text
operation_results
assessment_results
comparison_results
```

para as três abas.

Não chamar a Spec 10 separadamente para cada aba.

---

# Workbook — regeneração

`regenerate_workbook()` deve preservar o princípio existente:

```text
editar entradas
    ->
regenerar
    ->
recalcular saídas derivadas
```

Logo:

- se o workbook possui >=2 cenários ativos válidos, as três abas fiscais são recalculadas;
- alterações manuais nas abas derivadas são descartadas na regeneração;
- se houver menos de 2 cenários ativos, as três abas são regeneradas vazias.

`load_workbook_inputs()` continua lendo somente abas editáveis.

As três novas abas não são inputs.

---

# Workbook — README

Atualizar o texto da aba `README` para refletir:

```text
Spec 08: interface tributária
Spec 09: motor CBS 2026
Spec 10: execução multi-cenário
Spec 11: comparação e materialização
```

Atualizar também a lista de abas derivadas.

Não afirmar que o workbook implementa um motor tributário completo.

---

# Workbook — proveniência

Atualizar `PROVENIENCIA` com pelo menos:

```text
counterfactual_report_spec_version
```

referenciando uma constante da Spec 11.

É permitido definir:

```python
CBS_2026_COUNTERFACTUAL_REPORT_SPEC_VERSION
=
"spec_11_counterfactual_tax_comparison_report_v1"
```

Não duplicar versões normativas.

As versões normativas continuam vindo de `FISCAL_PARAM`.

---

# Versão do workbook

Como o schema físico do workbook muda, atualizar:

```python
WORKBOOK_SPEC_VERSION
```

para uma versão da Spec 11, por exemplo:

```text
spec_11_excel_workbook_v1
```

Não manter `spec_08_excel_workbook_v1` após adicionar três novas abas ao contrato físico.

---

# Formatação Excel

Adicionar às colunas monetárias:

```text
BASE
CREDITO
DEBITO
S_APUR
T_RECOLHER
P_CASH
E_DRE
C_SALDO
DELTA_S_APUR
DELTA_T_RECOLHER
DELTA_P_CASH
DELTA_E_DRE
DELTA_C_SALDO
```

o formato monetário já usado:

```text
#,##0.00
```

Para:

```text
ALIQUOTA
```

usar:

```text
0.0000%
```

As abas derivadas devem manter header visual de saída, não o estilo de aba editável.

---

# API mínima da Spec 11

Criar:

```text
src/accounting_sim/tax_comparison.py
```

com:

```python
CBS_2026_COUNTERFACTUAL_REPORT_SPEC_VERSION
```

```python
@dataclass(frozen=True)
class Cbs2026CounterfactualReport:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame
    comparison_results: pd.DataFrame
```

```python
def compare_cbs_2026_counterfactual_result(
    counterfactual_result: Cbs2026CounterfactualResult,
) -> pd.DataFrame:
    ...
```

```python
def run_cbs_2026_counterfactual_report(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualReport:
    ...
```

Não é necessário expor uma nova função de validação pública se os checks estruturais puderem permanecer locais e gerar `SchemaValidationError` legível.

---

# Exports públicos

Atualizar:

```text
src/accounting_sim/__init__.py
```

para exportar:

```text
CBS_2026_COUNTERFACTUAL_REPORT_SPEC_VERSION
Cbs2026CounterfactualReport
compare_cbs_2026_counterfactual_result
run_cbs_2026_counterfactual_report
```

Não remover exports anteriores.

---

# Atualização do roadmap

Atualizar:

```text
specs/README_specs_plan.md
```

para registrar:

```text
09 | 09_cbs_2026_regular_nfe55.md
10 | 10_counterfactual_tax_experiment.md
11 | 11_counterfactual_tax_comparison_report.md
```

Para a Spec 11 preservar:

```text
Questão:
Como comparar resultados e produzir uma decisão auditável?

Produto:
comparação/relatório de cenários
```

Interpretar `decisão auditável` como:

```text
informação estruturada e rastreável para decisão
```

e não como escolha automática.

---

# Arquivos esperados

Criar:

```text
specs/11_counterfactual_tax_comparison_report.md
src/accounting_sim/tax_comparison.py
tests/test_tax_comparison.py
```

Modificar:

```text
src/accounting_sim/__init__.py
src/accounting_sim/workbook.py
tests/test_workbook.py
specs/README_specs_plan.md
```

Modificar outros testes de workbook somente se o novo contrato físico exigir atualização explícita.

Não modificar:

```text
src/accounting_sim/tax_cbs_2026.py
src/accounting_sim/tax_counterfactual.py
src/accounting_sim/tax_context.py
src/accounting_sim/canonical.py
src/accounting_sim/events.py
src/accounting_sim/posting.py
src/accounting_sim/ledger.py
src/accounting_sim/statements.py
src/accounting_sim/account_mapping.py
src/accounting_sim/chart_of_accounts.py
docs/tax_sources/**
```

`canonical.py` já possui `COUNTERFACTUAL_COMPARISON_COLUMNS`; não há motivo para alterá-lo.

---

# Testes obrigatórios — comparação pura

Criar:

```text
tests/test_tax_comparison.py
```

Manter a suíte focada.

## Grupo A — schema e baseline

1. cenário-controle da Spec 10 produz uma linha de comparação;
2. baseline não é comparado contra si próprio;
3. `comparison_results` usa exatamente `COUNTERFACTUAL_COMPARISON_COLUMNS`;
4. `ID_CENARIO_BASE` é o baseline da Spec 10;
5. `ID_CENARIO` segue a ordem dos cenários alternativos em `scenario_ids`.

## Grupo B — aritmética

6. delta é sempre `alternativo - baseline`;
7. delta positivo é preservado;
8. delta negativo é preservado;
9. delta zero é preservado;
10. `P_CASH=None` produz `DELTA_P_CASH=None`;
11. `E_DRE=None` produz `DELTA_E_DRE=None`;
12. se apenas um dos lados for `None`, o delta também é `None`.

Os testes 6–12 podem usar `Cbs2026CounterfactualResult` sintético diretamente, sem criar legislação fictícia.

## Grupo C — integridade

13. cenário duplicado em `scenario_ids` é rejeitado;
14. baseline ausente de `scenario_ids` é rejeitado;
15. baseline não sendo o primeiro é rejeitado;
16. linha duplicada `(ID_CENARIO, TRIBUTO)` é rejeitada;
17. cenário sem linha de apuração é rejeitado;
18. tributo ausente/extra em cenário alternativo é rejeitado;
19. float em campo monetário comparado é rejeitado;
20. entrada não é mutada;
21. execução repetida é determinística.

## Grupo D — integração Specs 10–11

22. `run_cbs_2026_counterfactual_report()` reutiliza a saída da Spec 10;
23. baseline + controle estrutural produz deltas monetários conhecidos iguais a zero e deltas desconhecidos iguais a `None`;
24. `operation_results` do relatório é equivalente ao da Spec 10;
25. `assessment_results` do relatório é equivalente ao da Spec 10.

Não testar novamente toda a legislação da Spec 09.

---

# Testes obrigatórios — workbook

Atualizar `tests/test_workbook.py`.

Cobrir no mínimo:

1. `WORKBOOK_SHEETS` contém as três novas abas na ordem canônica;
2. as três novas abas possuem tabelas nomeadas;
3. as três novas abas não pertencem a `EDITABLE_SHEETS`;
4. `TaxContext` vazio produz as três abas vazias;
5. um único cenário ativo produz as três abas vazias;
6. baseline + controle estrutural produz:
   - resultados por operação para os dois cenários;
   - uma apuração por cenário;
   - uma comparação contra baseline;
7. valores em centavos são convertidos para reais;
8. `P_CASH=None` e `E_DRE=None` viram células vazias;
9. deltas `None` viram células vazias;
10. `ALIQUOTA` é armazenada como fração e formatada como percentual;
11. `regenerate_workbook()` recalcula as três abas;
12. alterações manuais nas abas derivadas não sobrevivem à regeneração;
13. `load_workbook_inputs()` ignora as abas derivadas como entrada;
14. workbook com >=2 cenários ativos mas experimento CBS inválido é rejeitado;
15. nenhuma alteração é necessária no motor contábil.

---

# Resultado esperado no workbook canônico

Para baseline e controle estrutural usando a fixture da Spec 09:

## `FISCAL_RESULTADOS_OPERACAO`

Devem existir as operações suportadas para cada um dos dois cenários.

Com duas operações tributárias por cenário:

```text
4 linhas
```

## `FISCAL_APURACAO`

```text
2 linhas
```

uma por cenário.

Exemplo de valores em reais:

```text
S_APUR = 9.00
T_RECOLHER = 0.00
P_CASH = vazio
E_DRE = vazio
C_SALDO = 0.00
```

## `COMPARATIVO_CENARIOS`

```text
1 linha
```

para o controle contra o baseline:

```text
DELTA_S_APUR = 0.00
DELTA_T_RECOLHER = 0.00
DELTA_P_CASH = vazio
DELTA_E_DRE = vazio
DELTA_C_SALDO = 0.00
```

---

# Determinismo

Com a mesma entrada lógica:

```text
comparison_results
workbook fiscal outputs
```

devem ser determinísticos.

A ordem física de:

```text
CENARIOS_TRIBUTARIOS
```

continua não podendo alterar o resultado lógico.

---

# Atomicidade

Se houver >=2 cenários ativos e o experimento for inválido:

```text
não gerar workbook parcial
```

A falha deve acontecer antes de salvar o arquivo final.

Não manter abas fiscais de uma execução anterior como se ainda fossem válidas.

---

# Política de testes

Não executar nova baseline completa no início.

A Spec 10 fechou com:

```text
277 passed
```

Durante a implementação, executar somente:

```bash
python -m pytest -q tests/test_tax_comparison.py tests/test_tax_counterfactual.py tests/test_workbook.py
```

Adicionar:

```text
tests/test_tax_cbs_2026.py
```

somente se houver motivo específico de integração; o motor CBS não deve ser alterado.

Ao final executar:

```bash
python -m pytest -q
```

uma única vez.

Se passar, não repetir.

Se falhar:

1. executar primeiro apenas o teste que falhou;
2. corrigir;
3. executar o subconjunto diretamente afetado;
4. executar a suíte completa novamente apenas para fechamento.

---

# Critérios de aceitação

A Spec 11 está concluída somente se:

- a comparação usa exclusivamente resultados da Spec 10;
- a definição de delta é `alternativo - baseline`;
- baseline não gera comparação consigo próprio;
- existe uma linha por cenário alternativo e tributo;
- o schema canônico `COUNTERFACTUAL_COMPARISON_COLUMNS` é preservado;
- ausência de `P_cash`/`E_DRE` permanece `None`;
- nenhum `None` é convertido em zero;
- nenhuma preferência entre cenários é inventada;
- nenhum ranking automático é criado;
- nenhum novo parâmetro fiscal é criado;
- nenhuma legislação é reaberta;
- o relatório consolidado contém operações, apurações e comparação;
- a camada de comparação não chama o motor CBS diretamente;
- as três abas fiscais são materializadas no workbook;
- as três abas são derivadas e não editáveis;
- workbooks sem experimento multi-cenário continuam válidos e recebem abas fiscais vazias;
- workbooks com experimento válido recalculam as três abas;
- workbooks com experimento multi-cenário inválido falham;
- valores monetários são exibidos em reais;
- alíquota é formatada como percentual sem alterar sua semântica de fração;
- regeneração recalcula as saídas derivadas;
- roadmap registra Specs 09–11 com seus nomes reais;
- testes focados passam;
- suíte completa passa uma única vez ao final.

---

# Marco C — condição de fechamento

Ao final da Spec 11, o projeto deve possuir o pipeline:

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
        |
        v
Spec 09
motor CBS por cenário
        |
        v
Spec 10
execução multi-cenário
        |
        v
Spec 11
comparação contra baseline
        |
        v
workbook auditável
```

Formalmente:

```text
bar_zeta_t
+
(rho_t^(s), Theta_t^(s))
    ->
Y_t^(s)
    ->
Delta Y_t^(s)
```

Isso fecha a infraestrutura do primeiro experimento tributário contrafactual.

O próximo avanço substantivo não deve ser outra camada de orquestração.

Deve ser uma nova capacidade econômica/tributária que produza um cenário alternativo realmente distinto e juridicamente especificado.
