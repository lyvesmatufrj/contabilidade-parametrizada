# Spec 10 — Experimento tributário contrafactual: execução multi-cenário sobre base factual fixa

**Status:** pronta para implementação  
**Prioridade:** alta  
**Depende de:** Specs 00–09 + Volumes I–III  
**Bloqueia:** Spec 11  
**Motor tributário disponível:** CBS 2026 da Spec 09  
**Base de implementação auditada:** `28dfa20404a221071d9ab29be4751ad928c994e4`

---

# Objetivo

Implementar a primeira execução contrafactual multi-cenário do projeto sem alterar a base econômico-factual e sem reimplementar regras tributárias.

A Spec 10 deve transformar:

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

em resultados tributários organizados por cenário:

```text
TAX_OPERATION_RESULT
+
TAX_ASSESSMENT_RESULT
```

para todos os cenários ativos admissíveis pelo motor CBS 2026 já implementado na Spec 09.

O objetivo desta spec é provar computacionalmente a estrutura:

```text
bar_zeta_t
+
(rho_t^(s), Theta_t^(s))
    ->
Y_t^(s)
```

mantendo `bar_zeta_t` fixo entre cenários.

Esta spec **não compara os resultados** e **não calcula deltas**. A comparação pertence à Spec 11.

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

A Spec 08 é autoritativa para:

```text
ENTIDADE
EVENTOS_FISCAIS
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
TaxContext
```

A Spec 09 é autoritativa para:

```text
validate_cbs_2026_admissibility
select_effective_cbs_2026_rules
calculate_cbs_2026_operations
assess_cbs_2026
run_cbs_2026
TAX_OPERATION_RESULT_COLUMNS
TAX_ASSESSMENT_RESULT_COLUMNS
```

A Spec 10 deve **orquestrar** esses objetos, não redefini-los.

---

# Relação formal com o experimento contrafactual

O Volume II fixa:

```text
bar_zeta_t = (x_t^min, u_t^min, eta_t)
```

e, para cada cenário `s`:

```text
zeta_t^(s) = (bar_zeta_t, rho_t^(s))
Y_t^(s) = H(bar_zeta_t, rho_t^(s); Theta_t^(s))
```

No contrato computacional atual:

```text
u_t^min <- EVENTOS + EVENTOS_FISCAIS
eta_t <- ENTIDADE
rho_t^(s) <- linha s de CENARIOS_TRIBUTARIOS
Theta_t^(s) <- FISCAL_PARAM selecionado pelo ID_VERSAO_NORMATIVA do cenário
```

Logo, a execução multi-cenário deve reutilizar a mesma instância lógica de `EVENTOS`, `EVENTOS_FISCAIS` e `ENTIDADE`, variando apenas a seleção de cenário/regra.

---

# Invariante central — base factual fixa

Para todos os cenários ativos `s`:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

A implementação não deve criar versões scenario-specific desses objetos com valores diferentes.

É permitido fazer cópias defensivas internas apenas para impedir mutação acidental.

Não é permitido alterar por cenário:

- valor da operação;
- data do fato;
- contraparte;
- documento;
- atributos factuais da entidade;
- `VBC_CENTS`;
- `PCBS_PERCENT`;
- `VCBS_CENTS`.

A diferença entre cenários deve entrar somente por `rho_t^(s)` e `Theta_t^(s)` selecionados em `CENARIOS_TRIBUTARIOS` e `FISCAL_PARAM`.

---

# Limitação metodológica explícita do primeiro experimento

A Spec 09 valida campos documentais fixos como:

```text
PCBS_PERCENT
VCBS_CENTS
CST_IBS_CBS
CCLASSTRIB
```

contra a regra efetiva do cenário.

Consequentemente, o motor atual **não deve ser usado para inventar um contrafactual jurídico não trivial** no qual uma nova legislação alteraria esses próprios campos documentais.

Por exemplo, esta spec não deve criar artificialmente:

```text
CBS_RATE_FRACTION = 0.010
```

apenas para produzir um delta diferente de zero enquanto mantém `PCBS_PERCENT=0.9` e `VCBS_CENTS` fixos.

Isso produziria uma inconsistência entre documento factual e regra do cenário e deve continuar sendo rejeitado pela Spec 09.

Portanto, a Spec 10 prova:

1. a infraestrutura multi-cenário;
2. a invariância da base factual;
3. a seleção independente de `rho`/`Theta` por cenário;
4. a organização determinística dos resultados;
5. a propagação correta de falhas de admissibilidade.

Ela **não precisa produzir resultados numericamente diferentes entre cenários**.

Um cenário-controle estrutural pode produzir exatamente o mesmo resultado do baseline. Isso não é falha: significa que o orquestrador não introduziu diferenças artificiais.

Contrafactuais que exigirem reconstrução de valores documentais ou novo motor tributário pertencem a uma extensão posterior.

---

# Escopo

Implementar somente:

- execução dos cenários tributários ativos;
- identificação do cenário baseline;
- validação conjunta do experimento;
- delegação de cada cenário ao motor `run_cbs_2026`;
- concatenação determinística dos resultados por operação;
- concatenação determinística das apurações;
- metadados mínimos do experimento;
- garantia de invariância e não mutação dos fatos;
- erros legíveis associados ao cenário inválido.

---

# Fora de escopo

Não implementar:

- nova regra de CBS;
- nova alíquota;
- IBS, PIS, Cofins, ICMS ou ISS;
- Simples Nacional, Lucro Real ou Lucro Presumido;
- engine tributário genérico;
- registry/plugin de motores fiscais;
- DSL normativa;
- overrides ad hoc de parâmetro;
- `rate_override`;
- alteração de fatos por cenário;
- reconstrução de NF-e contrafactual;
- arredondamento de tributo contrafactual;
- cálculo de `DELTA_*`;
- `COUNTERFACTUAL_COMPARISON_COLUMNS`;
- decisão sobre cenário melhor/pior;
- materialização no workbook;
- reabertura da auditoria jurídica da Spec 09;
- alteração de `docs/tax_sources`.

A Spec 11 será responsável pela comparação de resultados.

A materialização no workbook será tratada junto com a Spec 11, evitando acoplar o workbook genérico ao único motor CBS existente hoje.

---

# Entradas

A API principal recebe:

```python
events: pd.DataFrame
tax_context: TaxContext
```

Não receber `scenario_id` na API principal do experimento.

O conjunto de cenários é determinado por:

```text
CENARIOS_TRIBUTARIOS.ATIVO == true
```

Não receber lista externa de cenários e não criar override paralelo à tabela canônica.

---

# Cenários participantes

Participam apenas linhas de `CENARIOS_TRIBUTARIOS` com `ATIVO=true`.

A execução contrafactual exige:

```text
n_active >= 2
```

e exatamente um baseline ativo:

```text
sum(E_BASELINE among active scenarios) = 1
```

A unicidade de IDs e a existência de uma única entidade continuam sendo validadas pela Spec 08.

Cenários inativos não são executados e não geram resultados. Eles não precisam ser admissíveis pela regra jurídica da Spec 09 além das validações estruturais já exigidas pelo `TaxContext`.

---

# Ordenação determinística dos cenários

A ordem física das linhas de `CENARIOS_TRIBUTARIOS` não deve controlar a execução.

Definir a ordem canônica:

```text
1. baseline ativo
2. demais cenários ativos ordenados por ID_CENARIO
```

O resultado deve expor essa ordem em:

```python
scenario_ids: tuple[str, ...]
```

O primeiro elemento deve ser sempre `baseline_scenario_id`.

---

# Validação do experimento

Implementar:

```python
def validate_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> ValidationReport:
    ...
```

A função deve:

1. validar `TaxContext` pela Spec 08;
2. selecionar cenários ativos;
3. exigir pelo menos dois cenários ativos;
4. exigir exatamente um baseline ativo;
5. determinar a ordem canônica;
6. executar `validate_cbs_2026_admissibility()` para cada cenário ativo;
7. agregar issues com `scenario_id` preservado;
8. rejeitar o experimento se qualquer cenário ativo estiver fora do recorte da Spec 09.

Não criar validação jurídica adicional e não reinterpretar issues da Spec 09.

## Issue codes novos mínimos

```text
counterfactual_requires_two_active_scenarios
```

Como proteção local, pode ser usado também:

```text
counterfactual_invalid_active_baseline_count
```

---

# Atomicidade lógica

O experimento é tratado como uma unidade.

Se qualquer cenário ativo for inválido:

```text
nenhum resultado parcial deve ser retornado
```

A função principal deve lançar `SchemaValidationError` com mensagem que indique pelo menos `ID_CENARIO`, issue code e mensagem do erro relevante.

Como o motor é puro e não grava estado externo, isso é atomicidade lógica, não uma transação de banco de dados.

---

# Resultado do experimento

Criar:

```python
@dataclass(frozen=True)
class Cbs2026CounterfactualResult:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame
```

Sem novos schemas tabulares.

## `operation_results`

Usar exatamente `TAX_OPERATION_RESULT_COLUMNS`.

As linhas de todos os cenários ativos devem ser concatenadas na ordem canônica de cenário e, dentro de cada cenário, por `ID_EVENTO`.

Não adicionar `E_BASELINE`, `DESCRICAO` ou `DELTA` ao DataFrame.

## `assessment_results`

Usar exatamente `TAX_ASSESSMENT_RESULT_COLUMNS`.

Deve haver uma linha por cenário ativo, na ordem canônica de cenários.

Não calcular comparação entre linhas.

---

# Função principal

Implementar:

```python
def run_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualResult:
    ...
```

Fluxo obrigatório:

```text
validate TaxContext
    ->
validate multi-scenario experiment
    ->
identify baseline + deterministic order
    ->
for each active scenario:
    run_cbs_2026(events, same tax_context, scenario_id)
    ->
concatenate operation results
    ->
concatenate assessment results
    ->
return defensive copies
```

A função não deve editar nenhum DataFrame de entrada.

---

# Reutilização obrigatória da Spec 09

A Spec 10 não deve copiar para o novo módulo a lógica de:

```text
chi_t
mathfrak E_t
B_CBS
tau_CBS
C_CBS
D_CBS
S_CBS^apur
T_CBS^recolher
C_CBS^saldo
```

Ela deve chamar `validate_cbs_2026_admissibility` e `run_cbs_2026` da Spec 09.

Se o comportamento tributário precisar ser corrigido, a correção pertence à Spec 09, não à Spec 10.

---

# Cenário-controle estrutural para testes

Os testes podem construir em memória um segundo cenário ativo copiando o baseline da fixture da Spec 09 e alterando apenas:

```text
ID_CENARIO
DESCRICAO
E_BASELINE = false
```

mantendo a mesma `ID_VERSAO_NORMATIVA`, `rho` e `Theta` efetiva.

Esse cenário é um **controle de orquestração**, não uma nova legislação.

Resultado esperado:

```text
Y_baseline = Y_controle
```

exceto pelos identificadores de cenário.

Não adicionar ao corpus normativo uma alíquota sintética para forçar diferenças.

---

# Casos de exemplo

## Caso A — baseline + controle estrutural

```text
S0:
    E_BASELINE = true
    ATIVO = true
    ID_VERSAO_NORMATIVA = CBS_2026_08_31_V1

S1:
    E_BASELINE = false
    ATIVO = true
    ID_VERSAO_NORMATIVA = CBS_2026_08_31_V1
```

Saída:

```text
baseline_scenario_id = S0
scenario_ids = (S0, S1)
```

Se a base e as regras são as mesmas, as apurações também devem ser iguais, desconsiderando `ID_CENARIO`.

## Caso B — cenário ativo inválido

```text
S0 = baseline válido
S1 = REGIME_ENTIDADE fora do recorte
```

Resultado: experimento rejeitado com `SchemaValidationError` e nenhum resultado parcial.

## Caso C — cenário inativo fora do recorte

```text
S0 = baseline válido e ativo
S1 = controle válido e ativo
S2 = cenário fora do recorte, ATIVO=false
```

`S2` não é executado. O experimento permanece válido desde que o `TaxContext` seja estruturalmente válido pela Spec 08.

---

# Testes obrigatórios

Criar:

```text
tests/test_tax_counterfactual.py
```

Manter o conjunto enxuto.

## Grupo A — seleção e validação

1. baseline + controle ativo formam experimento válido;
2. um único cenário ativo é rejeitado;
3. zero cenário ativo é rejeitado;
4. exatamente um baseline ativo é preservado;
5. cenário ativo fora do recorte CBS torna todo o experimento inválido;
6. cenário inativo fora do recorte CBS não é executado.

## Grupo B — invariância factual

7. inputs não são modificados: `events`, `entity_profile`, `fiscal_event_attributes`, `tax_scenarios` e `tax_parameters`;
8. nenhuma tabela factual recebe `ID_CENARIO`.

## Grupo C — resultados

9. `baseline_scenario_id` é correto;
10. `scenario_ids` contém baseline primeiro e demais IDs em ordem determinística;
11. `operation_results` usa exatamente `TAX_OPERATION_RESULT_COLUMNS`;
12. `assessment_results` usa exatamente `TAX_ASSESSMENT_RESULT_COLUMNS`;
13. existe uma apuração por cenário ativo;
14. cenário inativo não aparece nos resultados;
15. baseline e controle estrutural produzem os mesmos valores tributários, exceto `ID_CENARIO`;
16. ordem física das linhas de `CENARIOS_TRIBUTARIOS` não altera o resultado;
17. execução repetida produz DataFrames equivalentes.

## Grupo D — fronteira arquitetural

18. Spec 10 não calcula `COUNTERFACTUAL_COMPARISON_COLUMNS`;
19. nenhum valor tributário novo é hard-coded;
20. `tax_cbs_2026.py` não é modificado pela implementação;
21. workbook permanece inalterado.

Não duplicar testes jurídicos já cobertos pela Spec 09.

---

# Política de erros

A API pública deve usar os tipos existentes:

```text
ValidationReport
ValidationIssue
SchemaValidationError
```

Não criar nova hierarquia de exceções.

---

# Determinismo e não mutação

Com os mesmos conteúdos lógicos, a ordem física das linhas não deve alterar:

```text
baseline_scenario_id
scenario_ids
operation_results
assessment_results
```

Ao final da execução, todos os DataFrames de entrada devem preservar igualdade de conteúdo com o estado anterior à chamada.

---

# Workbook

Não modificar:

```text
src/accounting_sim/workbook.py
WORKBOOK_SHEETS
TABLE_NAMES
```

nesta spec.

Motivo: o workbook da Spec 08 aceita contextos tributários genéricos que ainda não pertencem ao motor CBS 2026. Acoplar automaticamente o workbook ao único motor existente poderia quebrar compatibilidade com contextos estruturais anteriores.

A Spec 11 deverá materializar, em uma única etapa:

```text
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
```

quando já existir também a comparação entre cenários.

---

# Atualização do roadmap

Atualizar `specs/README_specs_plan.md` para substituir a referência genérica da Spec 10 por:

```text
10_counterfactual_tax_experiment.md
```

Preservar a questão:

```text
Como executar vários pares (rho, Theta) sobre a mesma base?
```

e o produto:

```text
experimento contrafactual
```

Não alterar o papel da Spec 11.

---

# API mínima

Criar:

```text
src/accounting_sim/tax_counterfactual.py
```

com:

```python
@dataclass(frozen=True)
class Cbs2026CounterfactualResult:
    baseline_scenario_id: str
    scenario_ids: tuple[str, ...]
    operation_results: pd.DataFrame
    assessment_results: pd.DataFrame


def validate_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> ValidationReport:
    ...


def run_cbs_2026_counterfactual_experiment(
    events: pd.DataFrame,
    tax_context: TaxContext,
) -> Cbs2026CounterfactualResult:
    ...
```

É suficiente.

Não criar `TaxEngine`, `TaxEngineRegistry`, `ScenarioPlugin`, `RuleGraph` ou `GenericCounterfactualEngine`.

---

# Arquivos esperados

Criar:

```text
specs/10_counterfactual_tax_experiment.md
src/accounting_sim/tax_counterfactual.py
tests/test_tax_counterfactual.py
```

Modificar:

```text
src/accounting_sim/__init__.py
specs/README_specs_plan.md
```

Não modificar:

```text
src/accounting_sim/tax_cbs_2026.py
src/accounting_sim/tax_context.py
src/accounting_sim/canonical.py
src/accounting_sim/events.py
src/accounting_sim/posting.py
src/accounting_sim/ledger.py
src/accounting_sim/statements.py
src/accounting_sim/account_mapping.py
src/accounting_sim/chart_of_accounts.py
src/accounting_sim/workbook.py
docs/tax_sources/**
```

Se alguma dessas alterações se mostrar indispensável, o Codex deve reportar a incompatibilidade em vez de expandir silenciosamente o escopo.

---

# Passos de implementação

1. confirmar `main` em `28dfa20404a221071d9ab29be4751ad928c994e4` ou descendente direto sem mudanças concorrentes relevantes;
2. ler Specs 08–10 e `README_specs_plan.md`;
3. inspecionar apenas os contratos necessários em `canonical.py`, `tax_context.py` e `tax_cbs_2026.py`;
4. criar `tax_counterfactual.py`;
5. implementar seleção determinística dos cenários ativos;
6. implementar validação agregada;
7. implementar o executor multi-cenário;
8. criar testes focados com baseline + cenário-controle estrutural em memória;
9. atualizar exports em `__init__.py`;
10. atualizar o roadmap;
11. executar testes focados;
12. executar a suíte completa uma única vez ao final.

---

# Política de testes

Não executar nova baseline completa: a implementação anterior fechou com:

```text
259 passed
```

Durante a implementação, executar somente:

```text
tests/test_tax_counterfactual.py
tests/test_tax_cbs_2026.py
```

Adicionar `tests/test_tax_context.py` somente se alguma alteração realmente tocar os contratos da Spec 08, o que não é esperado.

Ao final:

```bash
python -m pytest -q
```

uma única vez.

Se passar, não repetir.

---

# Critérios de aceitação

A Spec 10 está concluída somente se:

- existe uma API única que executa todos os cenários ativos;
- pelo menos dois cenários ativos são exigidos;
- exatamente um baseline ativo é identificado;
- baseline é executado primeiro;
- demais cenários são ordenados deterministamente;
- cada cenário é validado pelo motor CBS da Spec 09;
- qualquer cenário ativo inválido invalida o experimento inteiro;
- cenários inativos não são executados;
- a mesma base factual é usada para todos os cenários;
- nenhum objeto factual é mutado;
- nenhuma regra tributária nova é implementada;
- nenhum parâmetro sintético é adicionado ao corpus normativo;
- `operation_results` preserva o schema canônico;
- `assessment_results` preserva o schema canônico;
- nenhuma comparação/delta é calculada;
- um cenário-controle idêntico ao baseline produz resultado idêntico;
- workbook permanece inalterado;
- testes focados passam;
- suíte completa passa uma única vez ao final.

---

# Dependência para a Spec 11

A saída desta spec deve permitir diretamente:

```text
Cbs2026CounterfactualResult
    ->
Spec 11
    ->
comparação entre cenário baseline e cenários alternativos
```

A Spec 11 poderá consumir:

```text
baseline_scenario_id
scenario_ids
operation_results
assessment_results
```

e produzir `COUNTERFACTUAL_COMPARISON_COLUMNS` sem recalcular CBS e sem alterar a base factual.

A Spec 10 termina exatamente na fronteira:

```text
executar e organizar cenários
```

A Spec 11 começa em:

```text
comparar os resultados
```
