# Spec 13 — Demo operacional Excel ↔ Python

**Status da spec:** aprovada  
**Versão:** `spec_13_demo_operacional_v0_1`  
**Base do repositório:** `64676cab004efe75cf293f8de233ab1e127dc509`  
**Data:** 2026-09-02  
**Depende de:** Specs 00–12  
**Objetivo de produto:** demonstração operacional de aproximadamente 30 minutos para validação profissional  
**Artefato-alvo:** workbook `.xlsm` simples, interativo e conectado ao motor Python existente

---

# 1. Objetivo

Construir uma camada operacional mínima sobre o motor atual para que um usuário possa:

```text
informar perfil básico da empresa
+
informar operações
+
informar hipóteses analíticas permitidas
+
clicar em SIMULAR
        ↓
executar o motor Python real
        ↓
comparar Simples 2027 puro × híbrido
        ↓
entender causalmente o resultado
```

A Demo 0.1 não deve reproduzir o workbook técnico existente na superfície de uso.

O workbook técnico continua sendo objeto auditável do motor. A Demo 0.1 é uma **interface de operação e comunicação**.

---

# 2. Contexto canônico

Preservar:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

entre os cenários.

A interface operacional coleta fatos e hipóteses; um adaptador Python os converte nos objetos canônicos já definidos.

Fluxo:

```text
Excel .xlsm
    ↓
entradas operacionais
    ↓
VBA exporta payload
    ↓
Python adapta para objetos canônicos
    ↓
motor Spec 12
    ↓
resultados estruturados
    ↓
VBA importa
    ↓
painel + memória
```

Princípio arquitetural:

```text
VBA = controlador de interface
Python = único motor de cálculo
Excel = entrada + apresentação + auditoria legível
```

Não implementar lógica tributária substantiva em VBA ou em fórmulas Excel.

---

# 3. Escopo

## 3.1 Regime e recorte

A Demo 0.1 cobre somente:

```text
empresa comercial
optante pelo Simples Nacional
Anexo I
janeiro / 1º semestre de 2027
operações domésticas com mercadorias
Simples puro × Simples híbrido
```

Reutilizar integralmente a lógica tributária congelada da Spec 12.

## 3.2 Interação mínima

O usuário deve conseguir:

1. informar `RBT12`;
2. inserir/remover operações em uma tabela;
3. classificar cada operação dentro do recorte suportado;
4. informar hipóteses analíticas permitidas;
5. clicar em `SIMULAR`;
6. receber resultado ou mensagem de inadmissibilidade;
7. abrir uma memória de cálculo legível.

---

# 4. Fora de escopo

Não implementar nesta spec:

- Lucro Presumido;
- Lucro Real;
- outros anexos do Simples;
- serviços;
- importação/exportação;
- NFS-e;
- motor fiscal completo;
- ERP;
- integração com sistema externo;
- banco de dados;
- API web;
- atualização automática de legislação;
- otimização automática de regime;
- recomendação de “melhor regime”;
- reimplementação do motor Spec 12;
- fórmulas Excel que dupliquem cálculos do Python;
- `pywin32`;
- automação COM do Excel por Python;
- distribuição standalone para máquinas sem ambiente Python nesta primeira versão.

---

# 5. Workbook de produto

## 5.1 Abas visíveis

A superfície inicial deve ter somente três abas visíveis.

### `SIMULADOR`

Objetivo: entrada resumida + comparação imediata.

Blocos:

```text
EMPRESA
HIPÓTESES
STATUS DA EXECUÇÃO
SIMPL​ES PURO
SIMPL​ES HÍBRIDO
DIFERENÇAS
```

Entradas mínimas:

```text
RBT12
CBS_2027_ANALYSIS_RATE_FRACTION
REGULAR_CREDIT_REALIZATION_FRACTION
```

Os campos analíticos devem ser visualmente identificados como:

```text
HIPÓTESE ANALÍTICA
```

O workbook não deve apresentar a taxa CBS analítica como norma.

### `OPERACOES`

Tabela editável pelo usuário.

Schema operacional mínimo:

| Coluna | Tipo | Papel |
|---|---|---|
| `ID_OPERACAO` | texto | chave estável local |
| `DATA` | data | data da operação |
| `TIPO_OPERACAO` | enum | `compra_revenda`, `venda_b2b`, `venda_b2c` |
| `VALOR` | moeda | valor da operação |
| `REGIME_CONTRAPARTE` | enum | regime factual da contraparte |
| `OBSERVACAO` | texto opcional | anotação humana |

Coerências mínimas:

```text
compra_revenda -> REGIME_CONTRAPARTE = ibs_cbs_regime_regular
venda_b2b -> REGIME_CONTRAPARTE = ibs_cbs_regime_regular
venda_b2c -> REGIME_CONTRAPARTE = consumidor_final
```

A interface pode usar dropdowns.

### `MEMORIA`

Deve apresentar, em linguagem profissional:

```text
receita considerada
compras elegíveis
RBT12
alíquota efetiva do Simples
DAS total
CBS/IBS dentro do DAS
DAS residual
CBS/IBS regulares
créditos potenciais
créditos modelados
encargo tributário comparável
crédito potencial B2B
CBS de equilíbrio
status normativo/analítico
proveniência normativa essencial
```

Não expor IDs técnicos desnecessários na primeira leitura.

## 5.2 Abas técnicas

Podem existir ocultas:

```text
_CONFIG
_RESULTADOS_RAW
```

`_CONFIG` contém apenas configuração operacional, por exemplo:

```text
REPO_ROOT
PYTHON_EXE
INTERFACE_VERSION
```

Nenhuma alíquota normativa ou lógica tributária deve ser hard-coded nessa aba.

`_RESULTADOS_RAW` recebe a saída estruturada do Python para renderização.

---

# 6. Contrato Excel ↔ Python

## 6.1 Transporte

Não usar `pywin32`.

A comunicação deve ocorrer via arquivos temporários.

Diretório sugerido:

```text
%TEMP%\contabilidade_parametrizada\demo13\<RUN_ID>\
```

Arquivos de entrada:

```text
entity_input.csv
operations_input.csv
analysis_input.csv
run_request.csv
```

Arquivos de saída:

```text
run_status.csv
scenario_results.csv
comparison_results.csv
memory_results.csv
```

Arquivos temporários não pertencem ao repositório.

## 6.2 Execução

O VBA chama um entrypoint Python por processo externo.

Forma conceitual:

```text
<python_exe> <repo>\scripts\run_demo_operacional.py
    --input-dir <runtime>
    --output-dir <runtime>
```

O VBA deve esperar o processo terminar e então ler `run_status.csv`.

Não depender de Excel controlado por Python.

## 6.3 Exit status

Contrato mínimo:

```text
0 = sucesso
2 = entrada/admissibilidade inválida
3 = erro de configuração do ambiente
4 = erro interno inesperado
```

`run_status.csv` deve conter, no mínimo:

```text
RUN_ID
OK
STATUS_CODE
MESSAGE
ENGINE_SPEC_VERSION
```

---

# 7. Adaptador operacional Python

Criar uma camada estreita que converta o schema da aba `OPERACOES` nos objetos canônicos.

Exemplos:

```text
compra_revenda
    ->
EVENTO de compra de mercadoria
+
AMBITO_OPERACAO=domestica
REGIME_FORNECEDOR=ibs_cbs_regime_regular
DESTINACAO_AQUISICAO=revenda
```

```text
venda_b2b
    ->
EVENTO de venda
+
AMBITO_OPERACAO=domestica
TIPO_CLIENTE=b2b
REGIME_ADQUIRENTE=ibs_cbs_regime_regular
```

```text
venda_b2c
    ->
EVENTO de venda
+
AMBITO_OPERACAO=domestica
TIPO_CLIENTE=b2c
REGIME_ADQUIRENTE=consumidor_final
```

Para campos técnicos não expostos na interface, a Demo 0.1 pode usar defaults explícitos e documentados, desde que não alterem o significado tributário do recorte.

Esses defaults são **decisões operacionais da demo**, não fatos universais nem normas.

---

# 8. Uso do motor existente

O entrypoint deve reutilizar:

```python
run_simples_2027_counterfactual_report(...)
```

e os validadores já existentes.

Não copiar para o adaptador:

```text
fórmula do Simples
repartição CBS/IBS
débitos
créditos
break-even
admissibilidade tributária
```

A regra é:

```text
adapter -> canonical objects -> existing engine
```

e nunca:

```text
adapter -> second tax engine
```

---

# 9. Comportamento do botão `SIMULAR`

Sequência:

```text
1. validar campos mínimos de interface;
2. gerar RUN_ID;
3. exportar entradas;
4. chamar Python;
5. aguardar término;
6. ler status;
7. se OK:
       importar resultados
       atualizar SIMULADOR
       atualizar MEMORIA
       registrar horário da execução
   senão:
       preservar último resultado válido
       marcar resultado anterior como desatualizado
       mostrar mensagem legível.
```

Não apagar o último resultado válido em caso de falha.

O painel deve deixar explícito:

```text
ÚLTIMA SIMULAÇÃO VÁLIDA: <timestamp>
```

---

# 10. Configuração do ambiente

Não hard-code caminho local no VBA.

`_CONFIG` deve permitir configurar:

```text
REPO_ROOT
PYTHON_EXE
```

Para o ambiente de desenvolvimento, pode-se apontar para:

```text
<repo>\.venv\Scripts\python.exe
```

ou outro interpretador configurado.

O botão deve detectar:

```text
repo inexistente
python inexistente
entrypoint inexistente
```

e apresentar erro de configuração sem corromper o workbook.

---

# 11. Workbench e versionamento

Enquanto design/VBA estiverem instáveis:

```text
workbook .xlsm -> Drive / workbench
screenshots -> Drive / workbench
rascunho VBA -> Drive / workbench
```

Não fazer commit a cada alteração visual.

Entram no repositório apenas quando estabilizados:

```text
contrato de abas
schema de operações
contrato Excel ↔ Python
entrypoint Python
testes do adaptador
VBA funcional mínimo
```

Artefato final candidato:

```text
artifacts/demo_operacional_simples_2027.xlsm
```

---

# 12. Saídas mínimas

Na tela principal:

| Métrica | Puro | Híbrido |
|---|---:|---:|
| DAS total / residual | valor | valor |
| CBS líquida modelada | — | valor |
| IBS líquido modelado | — | valor |
| Encargo tributário comparável | valor | valor |
| Crédito potencial B2B | valor | valor |

Além disso:

```text
DELTA_ENCARGO
CBS_BREAK_EVEN
STATUS_RESULTADO
CBS_RATE_SOURCE
```

Não classificar automaticamente um cenário como “melhor”.

---

# 13. Proveniência e status epistemológico

A memória deve diferenciar:

```text
FATO
NORMA
HIPÓTESE ANALÍTICA
RESULTADO DERIVADO
```

Exemplo:

```text
RBT12 = FATO INFORMADO
IBS 2027 = NORMATIVO
CBS 2027 usada = HIPÓTESE ANALÍTICA
realização dos créditos = HIPÓTESE ANALÍTICA
encargo comparável = RESULTADO DERIVADO
```

Proveniência normativa deve continuar vindo de `FISCAL_PARAM`.

---

# 14. Testes obrigatórios

## 14.1 Python

Adicionar testes focados para:

1. adaptador operacional -> objetos canônicos;
2. caso de três operações equivalente ao fixture da Spec 12;
3. `venda_b2b` com contraparte incompatível -> rejeição;
4. `venda_b2c` com contraparte incompatível -> rejeição;
5. hipótese analítica ausente -> rejeição quando requerida;
6. CLI retorna exit code correto;
7. arquivos de saída obedecem ao schema;
8. nenhum cálculo tributário é reimplementado no adaptador.

## 14.2 Excel/VBA

Validação manual mínima no Excel 2013:

```text
editar RBT12
editar hipótese
adicionar/remover operação
clicar SIMULAR
resultado muda
MEMORIA muda
erro de input é legível
erro de ambiente é legível
último resultado válido é preservado
```

## 14.3 Regressão

Durante a implementação:

```text
testes focados Spec 13
+
testes focados Spec 12
```

Full suite somente ao final da implementação estabilizada.

---

# 15. Critérios de aceitação

A Demo 0.1 é aceita quando:

```text
[ ] abre no Excel 2013 sem reparo
[ ] possui no máximo três abas visíveis de uso
[ ] usuário consegue inserir operações sem editar schemas técnicos
[ ] botão SIMULAR executa Python real
[ ] Python usa o motor congelado da Spec 12
[ ] nenhuma fórmula/VBA duplica cálculo tributário
[ ] resultado é atualizado a partir da execução corrente
[ ] inadmissibilidade é apresentada de forma legível
[ ] memória distingue fato/norma/hipótese/resultado
[ ] último resultado válido é preservado em falha
[ ] caso canônico reproduz os valores de regressão da Spec 12
[ ] regressão CBS 2026 não é afetada
```

---

# 16. Arquivos esperados

Após estabilização:

```text
specs/13_demo_operacional_excel_python.md
scripts/run_demo_operacional.py
src/accounting_sim/demo_operacional.py
tests/test_demo_operacional.py
artifacts/demo_operacional_simples_2027.xlsm
```

VBA pode permanecer embutido no `.xlsm`, mas recomenda-se também exportar os módulos-fonte para revisão, por exemplo:

```text
vba/DemoOperacional.bas
```

quando o contrato estiver estável.

---

# 17. Dependências

Reutilizar:

```text
Spec 06 — workbook
Spec 08 — TaxContext
Spec 10 — cenário contrafactual
Spec 11 — comparação
Spec 12 — Simples 2027 puro × híbrido
```

A Spec 13 **não reabre** a lógica tributária congelada da Spec 12.

---

# 18. Definição da Demo 0.1

A versão 0.1 existe para demonstrar:

```text
estrutura de operações
        ↓
mesmos fatos
        ↓
regimes distintos
        ↓
efeito tributário
        ↓
efeito de créditos
        ↓
explicação rastreável
```

O sucesso da demo não é cobrir toda a RTC.

O sucesso é fazer um profissional entender a proposta, explorar um caso em poucos minutos e produzir perguntas/requisitos úteis para a próxima rodada.
