# Nota corretiva — Spec 12: auditoria pós-implementação

**Status:** correção obrigatória antes do congelamento da Spec 12  
**Natureza:** nota corretiva; não é nova spec numerada  
**Base auditada:** `main@1400b16550af12a678a7fdf44e1096cff93bd072`  
**Commit:** `spec-12-simples-2027-puro-hibrido`  
**Data da auditoria:** 2026-09-02  
**Escopo:** patch estreito sobre a implementação existente, sem reabrir a arquitetura das Specs 08–12 e sem alterar o caso CBS 2026 salvo regressão funcional comprovada.

---

# 1. Decisão da auditoria

A implementação da Spec 12 está conceitualmente correta, mas **ainda não deve ser congelada**.

Foram identificados:

1. dois defeitos funcionais que podem alterar a admissibilidade ou o resultado lógico do recorte;
2. três correções de governança/proveniência normativa;
3. um defeito semântico no status epistemológico do resultado híbrido;
4. um defeito de compatibilidade do workbook com Excel 2013.

A correção deve ser feita em **um único patch pequeno**, preservando o desenho atual.

Não criar nova arquitetura tributária, novo registry, nova engine genérica ou nova spec numerada.

---

# 2. Invariantes que não devem ser reabertos

Preservar:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

Preservar também:

```text
FISCAL_PARAM != ANALISE_PARAM
```

e a separação:

```text
núcleo contábil
||
ramo tributário
```

Não alterar a semântica já aprovada de:

- Simples 2027 puro;
- Simples 2027 híbrido;
- DAS;
- parcelas CBS/IBS no DAS;
- DAS residual;
- débitos/créditos regulares;
- encargo tributário comparável;
- crédito potencial na cadeia B2B;
- break-even da CBS;
- caso regressivo CBS 2026.

---

# 3. Correção funcional 1 — validar o regime do adquirente B2B

## Defeito

A fixture possui:

```text
TIPO_CLIENTE = b2b
REGIME_ADQUIRENTE = ibs_cbs_regime_regular
```

mas o motor atual classifica vendas B2B apenas por:

```text
TIPO_CLIENTE
```

e não lê `REGIME_ADQUIRENTE`.

Consequentemente, uma venda com:

```text
TIPO_CLIENTE = b2b
REGIME_ADQUIRENTE = simples_nacional
```

pode ser tratada como venda que disponibiliza crédito potencial ao adquirente regular.

## Contrato corretivo

No recorte da Spec 12, exigir:

```text
TIPO_CLIENTE = b2b
    -> REGIME_ADQUIRENTE = ibs_cbs_regime_regular
```

e:

```text
TIPO_CLIENTE = b2c
    -> REGIME_ADQUIRENTE = consumidor_final
```

A mensuração de:

```text
CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS
CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS
```

deve considerar como receita B2B elegível somente a venda que satisfaça simultaneamente o tipo de cliente e o regime do adquirente.

## Testes mínimos

Adicionar testes negativos para:

```text
b2b + REGIME_ADQUIRENTE != ibs_cbs_regime_regular
b2c + REGIME_ADQUIRENTE != consumidor_final
REGIME_ADQUIRENTE ausente em venda suportada
```

e confirmar que a fixture canônica permanece aceita.

---

# 4. Correção funcional 2 — admissibilidade não pode aceitar `ANALISE_PARAM` vazio

## Defeito

`validate_tax_analysis_parameters()` aceita legitimamente um DataFrame vazio porque o workbook genérico pode não usar análise.

Entretanto, a Spec 12 depende atualmente de:

```text
CBS_2027_ANALYSIS_RATE_FRACTION
REGULAR_CREDIT_REALIZATION_FRACTION
```

quando não existe taxa normativa de CBS 2027 no bundle.

Assim, a admissibilidade específica pode retornar `ok=True` para um contexto que falha depois no runner.

Isso viola o contrato:

```text
chi_t = 1
<=> contexto executável no recorte.
```

## Contrato corretivo

Não alterar a semântica genérica de:

```python
validate_tax_analysis_parameters(...)
```

para outros workbooks/recortes.

Corrigir:

```python
validate_simples_2027_admissibility(...)
```

para exigir explicitamente as hipóteses analíticas necessárias à execução da Spec 12.

A regra deve respeitar a precedência existente:

```text
se CBS_2027_REGULAR_RATE_FRACTION normativo estiver vigente:
    CBS_2027_ANALYSIS_RATE_FRACTION não é necessário para escolher a taxa;
senão:
    CBS_2027_ANALYSIS_RATE_FRACTION é obrigatório
```

`REGULAR_CREDIT_REALIZATION_FRACTION` continua obrigatório enquanto a modelagem do crédito realizado depender dele.

## Testes mínimos

Cobrir:

```text
ANALISE_PARAM vazio -> admissibilidade false no recorte atual
alpha ausente -> admissibilidade false
CBS analítica ausente sem CBS normativa -> admissibilidade false
CBS normativa vigente + alpha presente -> admissibilidade válida sem exigir CBS analítica
```

---

# 5. Correções de proveniência normativa

Aplicar no fixture canônico da Spec 12.

## 5.1 IBS 2027

O valor:

```text
IBS_2027_REGULAR_RATE_FRACTION = 0.001
```

permanece.

Corrigir somente a proveniência do dispositivo para:

```text
LC 214/2025, art. 344
```

Não alterar o valor numérico.

---

## 5.2 Resolução CGSN 190/2026

Substituir a URL incompleta por:

```text
https://www.in.gov.br/web/dou/-/resolucao-cgsn-n-190-de-4-de-agosto-de-2026-724454118
```

Aplicar às linhas cuja fonte é a Resolução CGSN 190/2026.

---

## 5.3 Vigência do Anexo I

As linhas do Anexo I foram registradas com:

```text
VIG_FIM = 2027-06-30
```

porque o cenário demonstrativo cobre o primeiro semestre.

Isso mistura:

```text
vigência normativa
```

com:

```text
janela temporal do cenário.
```

Para as linhas do Anexo I da Resolução CGSN 190/2026, registrar a vigência documental:

```text
VIG_INI = 2027-01-01
VIG_FIM = 2028-12-31
```

A janela do cenário continua sendo controlada por:

```text
DT_REFERENCIA_NORMATIVA
+
admissibilidade da Spec 12
```

Não estender automaticamente a mesma correção a `SIMPLES_2027_REVENUE_RECOGNITION` sem verificar o dispositivo que sustenta essa linha.

---

# 6. Status epistemológico do cenário híbrido

## Defeito

Hoje o híbrido usa lógica equivalente a:

```python
"analitico" if cbs_rate_source == "analysis" else "normativo"
```

Isso implica que, quando a taxa normativa da CBS 2027 for adicionada, o cenário inteiro poderá ser marcado como `normativo`.

Mas o resultado híbrido continuará dependendo de:

```text
REGULAR_CREDIT_REALIZATION_FRACTION
```

que é hipótese analítica.

## Contrato corretivo

O status deve refletir **todas as dependências analíticas efetivamente usadas no resultado**, e não apenas a origem da taxa CBS.

No desenho atual:

```text
cenário puro:
    normativo, se não consumir hipótese analítica

cenário híbrido:
    analitico enquanto REGULAR_CREDIT_REALIZATION_FRACTION for hipótese analítica
```

Se no futuro todas as dependências analíticas forem substituídas por regras/fatos normativos ou observados, o status poderá ser revisto.

Não converter silenciosamente hipótese em norma.

## Teste mínimo

Adicionar:

```text
CBS normativa vigente + alpha analítico
-> STATUS_RESULTADO do híbrido permanece "analitico"
```

---

# 7. Compatibilidade Excel 2013

## Evidência

No Excel 2013, o workbook demonstrativo é reparado ao abrir, com remoção de estruturas `Table`/`AutoFilter`.

O escritor atual cria `Table` para todas as abas tabulares com:

```text
ref = A1:<última coluna><max(ws.max_row, 1)>
```

Portanto, uma aba sem dados pode receber uma tabela contendo apenas a linha de cabeçalho.

## Contrato corretivo

Manter tabelas Excel nas abas com ao menos uma linha de dados.

Para abas tabulares vazias:

```text
manter cabeçalhos
manter estilos/formatação
não criar objeto Table de uma única linha
não exigir AutoFilter/Table como invariante de aceitação
```

A solução deve ser mínima e compatível com Excel 2013.

Não substituir o workbook por outro mecanismo nem duplicar cálculos tributários em fórmulas Excel.

## Critérios de aceite

O demo deve:

1. ser gerado sem erro;
2. passar `load_workbook`;
3. abrir no Microsoft Excel 2013 sem mensagem de reparo;
4. preservar conteúdo das abas;
5. preservar `Table`/filtro nas abas não vazias nas quais isso já funciona;
6. aceitar abas tabulares vazias apenas com cabeçalhos;
7. continuar passando os validadores internos ajustados a esse contrato.

Se o ambiente do Codex não possuir Excel 2013, ele deve:

```text
implementar a correção estrutural
+
testar o XML/OOXML gerado e os testes Python disponíveis
+
registrar que a abertura final no Excel 2013 depende da validação manual do usuário
```

Não afirmar que o Excel 2013 foi validado se ele não foi realmente executado.

---

# 8. Robustez temporal — não bloqueadora

Existe um gap de robustez: a admissibilidade controla a data normativa do cenário, mas a API tributária isolada pode não proteger integralmente a fronteira temporal dos eventos do demo.

Isso **não deve expandir este patch**, salvo se a correção for trivial e local.

Caso contrário:

```text
registrar em backlog
```

e não reabrir a Spec 12.

---

# 9. Arquivos que provavelmente serão alterados

Inspecionar a `main` antes de editar. O patch deve permanecer pequeno.

Prováveis arquivos:

```text
src/accounting_sim/tax_simples_2027.py
src/accounting_sim/workbook.py
tests/test_tax_simples_2027.py
tests/test_workbook.py
data/demo_simples_2027/fiscal_event_attributes.csv
data/demo_simples_2027/tax_parameters.csv
```

Os caminhos reais devem ser confirmados no repositório; não criar duplicatas se os fixtures estiverem em outra pasta.

Pode ser necessário atualizar documentação/README apenas se um teste ou contrato versionado exigir.

---

# 10. Arquivos que não devem ser alterados sem necessidade comprovada

Preservar, em especial:

```text
src/accounting_sim/tax_cbs_2026.py
src/accounting_sim/tax_counterfactual.py
src/accounting_sim/tax_comparison.py
Specs 09–11
Volumes I–III
docs/tax_sources/**
```

Não adicionar nova fonte normativa ao corpus neste patch.

Não alterar os valores centrais já validados do demo, exceto quando a correção de admissibilidade exigir rejeitar uma entrada antes aceita incorretamente.

---

# 11. Política de testes

Para economizar créditos e tempo:

```text
1. testes focados do Simples 2027
2. testes focados de workbook
3. subconjunto integrado relevante
4. full suite uma única vez ao final
```

Se a full suite falhar:

```text
rerodar primeiro somente o teste que falhou
corrigir
executar a full suite novamente apenas após a correção
```

Não repetir a suíte completa após cada alteração.

---

# 12. Critério de fechamento

A Spec 12 pode ser congelada quando:

```text
[ ] REGIME_ADQUIRENTE é validado e usado na mensuração B2B
[ ] admissibilidade garante contexto executável
[ ] proveniência IBS aponta para art. 344
[ ] URL da Resolução CGSN 190 está correta
[ ] vigência do Anexo I não é confundida com janela do cenário
[ ] status híbrido permanece analítico enquanto consumir alpha analítico
[ ] testes focados novos passam
[ ] regressão CBS 2026 permanece verde
[ ] workbook abre no Excel 2013 sem reparo
[ ] full suite final passa
```

Até então:

```text
Spec 12 = implementada, auditada, pendente de patch corretivo
```
