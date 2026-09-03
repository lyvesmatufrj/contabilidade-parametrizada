# Spec 13 — Demo operacional Excel ↔ Python

**Status da spec:** aprovada — hardening para congelamento  
**Versão de interface:** `spec_13_demo_operacional_v0_1`  
**Revisão documental:** `hardening_r1`  
**Base do repositório:** `001a1d0b15a9ed1aa191e5f1bad6934f9ced00cf`  
**Data da revisão:** 2026-09-03  
**Depende de:** Specs 00–12  
**Artefato-alvo:** workbook `.xlsm` simples, interativo e conectado ao motor Python existente.

---

# 1. Objetivo

Estabilizar a Demo Operacional 0.1 já funcional:

```text
Excel
→ VBA
→ CSVs de entrada
→ adaptador Python
→ motor Spec 12
→ CSVs de saída
→ VBA
→ SIMULADOR + MEMORIA
```

O hardening desta revisão deve:

1. modularizar o VBA;
2. endurecer o contrato CSV Excel ↔ Python;
3. tornar a importação de resultados segura e atômica;
4. ampliar testes automatizados;
5. executar stress manual no Excel 2013;
6. preservar integralmente a regressão da Spec 12.

---

# 2. Princípios

Entre cenários, preservar sempre que possível:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

Arquitetura:

```text
VBA = controlador de interface
Python = único motor de cálculo
Excel = entrada + apresentação + auditoria legível
```

É proibido reimplementar no VBA ou em fórmulas Excel:

```text
fórmula do Simples
repartição CBS/IBS
débitos
créditos
break-even
admissibilidade tributária
```

---

# 3. Escopo

A Demo 0.1 cobre somente:

```text
empresa comercial
optante pelo Simples Nacional
Anexo I
janeiro / 1º semestre de 2027
operações domésticas com mercadorias
Simples puro × Simples híbrido
```

A interface permite:

- informar `RBT12`;
- inserir/remover operações;
- classificar operações suportadas;
- informar hipóteses analíticas;
- clicar `SIMULAR`;
- receber resultado ou erro legível;
- consultar memória de cálculo.

Fora de escopo:

- Lucro Presumido/Real;
- outros anexos;
- serviços;
- importação/exportação;
- NFS-e;
- ERP/API/banco;
- otimização/recomendação de “melhor regime”;
- trajetória temporal 2027–2033;
- atualização automática de legislação;
- `pywin32`;
- Python controlando Excel por COM.

A trajetória temporal da RTC fica para spec posterior ao freeze desta etapa.

---

# 4. Workbook

Abas visíveis:

```text
SIMULADOR
OPERACOES
MEMORIA
```

Abas técnicas ocultas:

```text
_CONFIG
_RESULTADOS_RAW
```

`_CONFIG`:

```text
REPO_ROOT
PYTHON_EXE
INTERFACE_VERSION
```

Nenhuma lógica tributária ou alíquota normativa deve ser hard-coded nessa aba.

---

# 5. Schema de operações

| Coluna | Papel |
|---|---|
| `ID_OPERACAO` | chave estável local |
| `DATA` | data |
| `TIPO_OPERACAO` | enum |
| `VALOR` | moeda |
| `REGIME_CONTRAPARTE` | fato fiscal |
| `OBSERVACAO` | texto opcional |

Tipos:

```text
compra_revenda
venda_b2b
venda_b2c
```

Coerência:

```text
compra_revenda -> ibs_cbs_regime_regular
venda_b2b      -> ibs_cbs_regime_regular
venda_b2c      -> consumidor_final
```

Linha totalmente vazia pode ser ignorada. Linha parcialmente preenchida deve ser rejeitada com mensagem legível.

---

# 6. Entradas e saídas

Entradas:

```text
RBT12
CBS_2027_ANALYSIS_RATE_FRACTION
REGULAR_CREDIT_REALIZATION_FRACTION
```

CBS e realização de créditos são `HIPÓTESE ANALÍTICA`.

Saídas mínimas:

```text
DAS total/residual
CBS líquida modelada
IBS líquido modelado
encargo tributário comparável
crédito potencial B2B
DELTA_ENCARGO
CBS_BREAK_EVEN
STATUS_RESULTADO
CBS_RATE_SOURCE
ÚLTIMA SIMULAÇÃO VÁLIDA
```

Não classificar cenário como “melhor”.

A memória deve distinguir:

```text
FATO
NORMA
HIPÓTESE ANALÍTICA
RESULTADO DERIVADO
```

---

# 7. Runtime e processo externo

Diretório:

```text
%TEMP%\contabilidade_parametrizada\demo13\<RUN_ID>\
```

Entradas:

```text
entity_input.csv
operations_input.csv
analysis_input.csv
run_request.csv
```

Saídas:

```text
run_status.csv
scenario_results.csv
comparison_results.csv
memory_results.csv
```

Execução:

```text
<python_exe> <repo>\scripts\run_demo_operacional.py
    --input-dir <runtime>
    --output-dir <runtime>
```

Exit codes:

```text
0 = sucesso
2 = entrada/admissibilidade inválida
3 = configuração inválida
4 = erro interno
```

`run_status.csv`:

```text
RUN_ID
OK
STATUS_CODE
MESSAGE
ENGINE_SPEC_VERSION
```

---

# 8. Contrato CSV congelado

Ambas as direções devem usar:

```text
encoding       = UTF-8 com BOM (`utf-8-sig`)
delimiter      = vírgula
decimal        = ponto
data           = YYYY-MM-DD
text qualifier = aspas duplas
```

## Python → Excel

Todos os outputs usam `encoding="utf-8-sig"` para evitar, entre outros problemas, o falso positivo SYLK do Excel 2013 em arquivos iniciados por `ID_...`.

## Excel → Python

VBA deve escrever UTF-8 com BOM, preferencialmente com `ADODB.Stream` via late binding.

O writer final não deve usar `Open ... For Output`, pois isso depende da code page local.

Python deve ler inputs com `encoding="utf-8-sig"`.

## Escape CSV

Suportar corretamente:

```text
vírgula
aspas
acentos
CR/LF
```

Regra:

```text
" -> ""
campo com vírgula, aspas ou CR/LF -> envolver em aspas
```

`OBSERVACAO` não pode quebrar o schema.

---

# 9. Localização numérica

VBA lê CSV Python com:

```text
DecimalSeparator="."
ThousandsSeparator=","
```

Centavos do motor são convertidos para moeda apenas na apresentação.

Frações são apenas formatadas como percentual.

No caso canônico:

```text
CBS_BREAK_EVEN ≈ 9,019%
```

---

# 10. Arquitetura modular VBA

O módulo monolítico atual deixa de ser arquitetura-alvo.

Estrutura:

```text
vba/demo_operacional/
    modDemoMain.bas
    modDemoConfig.bas
    modDemoRuntime.bas
    modDemoCsv.bas
    modDemoPayload.bas
    modDemoResults.bas
    README.md
    legacy/modDemoOperacional.bas
```

## `modDemoMain.bas`

Responsável por:

```text
Public Sub Simular()
orquestração
guard de reentrância
StatusBar
erro de alto nível
cleanup
```

Não deve conter parsing CSV detalhado ou lógica tributária.

## `modDemoConfig.bas`

Responsável por:

```text
constantes de abas/tabela/named ranges
GetConfigValue
ValidateEnvironment
validação estrutural do workbook
```

Sem caminhos locais hard-coded.

## `modDemoRuntime.bas`

Responsável por:

```text
RUN_ID
runtime folder único
QuoteArg
WScript.Shell síncrono
exit code
```

Duas execuções no mesmo segundo não podem reutilizar silenciosamente o mesmo runtime.

## `modDemoCsv.bas`

Responsável por:

```text
writer UTF-8 BOM
CsvEscape
reader CSV
decimal locale
helpers tabulares
```

Late binding para `ADODB.Stream`.

## `modDemoPayload.bas`

Responsável por:

```text
validar inputs
ExportEntityInput
ExportAnalysisInput
ExportOperations
ExportRunRequest
```

Todos os acessos ao workbook devem ser qualificados por `ThisWorkbook`.

## `modDemoResults.bas`

Responsável por:

```text
ReadRunStatus
ValidateOutputFiles
ValidateOutputPayload
UpdateRawResults
UpdateMemory
UpdateSimulator
MarkResultsStale
```

---

# 11. Regras VBA

Todos os módulos:

```vb
Option Explicit
```

Regras obrigatórias:

1. não usar `Range`, `Cells`, `Rows` ou `Worksheets` de forma ambígua;
2. não duplicar cálculo tributário;
3. usar late binding para objetos externos;
4. restaurar `StatusBar` e `ScreenUpdating` em erro;
5. mensagens de erro legíveis;
6. compatibilidade Excel 2013;
7. não apagar resultado válido antes de validar integralmente nova saída.

Os `.bas` versionados devem ser:

```text
encoding = Windows-1252
line endings = CRLF
```

O README deve registrar encoding e ordem de importação.

---

# 12. Reentrância e unicidade

`SIMULAR` é não reentrante.

Se já houver execução ativa, nova chamada não inicia segundo processo.

`RUN_ID` deve ser único. Estratégia aceita:

```text
timestamp + sufixo incremental quando necessário
```

ou equivalente sem dependência externa.

---

# 13. Semântica de falha

Com resultado válido anterior:

```text
preservar números
preservar timestamp anterior
status = DESATUALIZADO — última tentativa falhou
```

Sem resultado válido anterior:

```text
status = SEM SIMULAÇÃO VÁLIDA
```

Erro do motor deve exibir `MESSAGE` de `run_status.csv`, e não apenas o exit code.

---

# 14. Importação atômica

Antes da primeira escrita no workbook validar:

```text
quatro outputs existem
schemas mínimos
SIMPLES_2027_PURO
SIMPLES_2027_HIBRIDO
ENCARGO_TRIBUTARIO_COMPARAVEL
CBS_BREAK_EVEN
CBS_RATE_SOURCE
named ranges obrigatórios
```

Somente depois:

```text
atualizar _RESULTADOS_RAW
atualizar MEMORIA
atualizar SIMULADOR
registrar timestamp
```

`_RESULTADOS_RAW` deve usar offsets dinâmicos; não depender de linhas fixas `A20`/`A40`.

---

# 15. Baseline de regressão

Caso:

```text
RBT12 = 1.200.000
compra = 85.000
B2B = 70.000
B2C = 30.000
CBS = 9%
realização = 100%
```

Esperado:

```text
puro     = R$ 8.825,00
híbrido  = R$ 8.822,13
delta    = -R$ 2,87
break-even ≈ 9,019%
```

Sensibilidade:

```text
CBS = 10%
```

Esperado, mantidos os demais fatos:

```text
puro     = R$ 8.825,00
híbrido  = R$ 8.972,13
delta    = R$ 147,13
```

Não hard-code esses resultados no VBA.

---

# 16. Testes Python

Expandir `tests/test_demo_operacional.py` para cobrir:

1. canonical;
2. B2B contraparte inválida;
3. B2C contraparte inválida;
4. valor zero/negativo;
5. RBT12 inválido;
6. CBS ausente;
7. alpha fora de `[0,1]`;
8. interface mismatch;
9. ID duplicado;
10. data inválida;
11. data fora do H1/2027;
12. schema de entrada inválido;
13. schemas exatos de saída;
14. exit codes;
15. outputs com BOM;
16. inputs com BOM;
17. Unicode/vírgula/aspas/quebra de linha em observação;
18. operações divididas mantendo os mesmos totais;
19. sensibilidade CBS 10%;
20. regressão Spec 12.

Ordem:

```text
testes Spec 13
→ Spec 13 + Spec 12
→ subconjunto integrado CBS 2026
→ full suite uma vez ao final
```

---

# 17. Teste estático VBA

Criar:

```text
tests/test_demo_operacional_vba_contract.py
```

Sem executar Excel.

Verificar:

```text
módulos esperados
Option Explicit
apenas modDemoMain expõe Public Sub Simular
sem caminhos locais
sem pywin32
sem writer Open ... For Output
writer UTF-8 presente
DecimalSeparator="." presente
sem Range("inp...") não qualificado
sem fórmulas tributárias copiadas
```

---

# 18. Stress manual Excel 2013

Casos válidos:

```text
canônico 9%
CBS 10%
alpha 0%, 50%, 100%
RBT12 alternativo
split de operações mantendo totais
100 operações
1.000 operações
valores com centavos
observação com acentos/vírgula/aspas/quebra de linha
20 execuções consecutivas
execuções rápidas verificando runtime único
```

Falhas:

```text
B2B + consumidor_final
B2C + regime regular
valor negativo
CBS vazia/fora de (0,1)
alpha fora de [0,1]
RBT12 inválido
data fora do recorte
PYTHON_EXE inválido
REPO_ROOT inválido
INTERFACE_VERSION incompatível
```

Em cada falha:

```text
mensagem legível
sem corrupção
último resultado válido preservado
status coerente
```

Após repetição:

```text
nenhum CSV aberto como workbook
nenhuma janela residual
StatusBar normal
ScreenUpdating normal
resultado exibido pertence à última execução válida
```

Registrar tempo para 100 e 1.000 operações; sem SLA rígido nesta versão.

---

# 19. Excel 2013

Antes do freeze:

```text
abre sem reparo
módulos compilam
SIMULAR executa Python
painel atualiza
MEMORIA atualiza
sem alerta SYLK
percentuais corretos
falhas preservam último resultado
20 execuções sem degradação funcional
```

---

# 20. Workbench e promoção

Durante hardening:

```text
Drive/RTC/demo_operacional_simples_2027.xlsm = workbench
```

O source VBA textual passa a ser versionado no Git.

Após testes automatizados:

```text
Spec 13 = aprovada
implementação = implementada
.xlsm = workbench
Excel 2013 manual = pendente
```

Após stress Excel 2013:

```text
Spec 13 = congelada
implementação = verificada
```

Então promover, quando efetivamente aprovado:

```text
artifacts/demo_operacional_simples_2027.xlsm
```

---

# 21. Arquivos esperados

```text
specs/13_demo_operacional_excel_python.md
specs/NOTE_spec_13_hardening_test_protocol.md
specs/IMPLEMENTATION_STATUS.md

src/accounting_sim/demo_operacional.py
scripts/run_demo_operacional.py
tests/test_demo_operacional.py
tests/test_demo_operacional_vba_contract.py

vba/demo_operacional/legacy/modDemoOperacional.bas
vba/demo_operacional/modDemoMain.bas
vba/demo_operacional/modDemoConfig.bas
vba/demo_operacional/modDemoRuntime.bas
vba/demo_operacional/modDemoCsv.bas
vba/demo_operacional/modDemoPayload.bas
vba/demo_operacional/modDemoResults.bas
vba/demo_operacional/README.md
```

Após validação:

```text
artifacts/demo_operacional_simples_2027.xlsm
```

---

# 22. Critérios de freeze

```text
[ ] regressão canônica preservada
[ ] sensibilidade 10% coerente
[ ] VBA modular
[ ] sem cálculo tributário duplicado
[ ] input/output UTF-8 BOM
[ ] escaping CSV robusto
[ ] sem SYLK
[ ] decimal locale correto
[ ] runtime não reentrante
[ ] RUN_ID sem colisão
[ ] importação validada antes de mutação
[ ] último resultado válido preservado
[ ] testes Python verdes
[ ] contrato VBA verde
[ ] Spec 12 verde
[ ] CBS 2026 preservada
[ ] full suite verde uma vez ao final
[ ] Excel 2013 sem reparo
[ ] stress manual concluído
[ ] IMPLEMENTATION_STATUS reconciliado
```

---

# 23. Definição de sucesso

A Demo 0.1 está pronta quando um profissional consegue editar operações, executar cenários, interpretar resultados e provocar erros sem comprometer a integridade do workbook.

A expansão temporal da RTC começa apenas depois desse freeze.
