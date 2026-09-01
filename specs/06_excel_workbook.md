# Spec 06 — Workbook Excel e parametrização operacional das contas

**Status:** abertura do Marco B — interface física do modelo  
**Prioridade:** bloqueadora  
**Depende de:** specs 00–05 + Volumes I–III  
**Bloqueia:** specs 07–11

## Objetivo

Materializar o núcleo contábil já validado do Marco A em um workbook Excel `.xlsx` auditável e editável nas entradas, preservando a separação canônica entre:

```text
modelo lógico
!=
interface física
```

A Spec 06 deve entregar duas capacidades simultâneas:

1. **parametrização operacional real do plano de contas**, removendo a dependência runtime de códigos de conta hard-coded no motor de escrituração;
2. **workbook Excel utilizável**, no qual o usuário edita somente as entradas declaradas e o Python regenera lançamentos, partidas, Diário, Razão, balancete e validações.

O fluxo desta etapa é:

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
        |
        v
      Python
        |
        +--> LANCAMENTOS
        +--> PARTIDAS
        +--> VINCULO_EVENTO_LCTO
        +--> DIARIO
        +--> RAZAO
        +--> BALANCETE
        +--> VALIDACOES
        +--> PROVENIENCIA
```

A cadeia matemática permanece:

```text
P_t + u_t
    -> E_t
    -> Lambda_t
    -> (Dia_t, Raz_t)
    -> b_t
```

O workbook `Wb_t` não altera essa cadeia. Ele apenas materializa seus objetos em tabelas para inspeção humana e edição controlada.

---

## Contexto canônico

### Source of truth

Consultar, nesta ordem:

```text
docs/volume_I/contabilidade_parametrizada.tex
docs/volume_II/contabilidade_parametrizada_volume_II.tex
docs/volume_III/contabilidade_parametrizada_volume_III.tex

specs/README_specs_plan.md
specs/00_mvp_scope.md
specs/01_canonical_model.md
specs/02_chart_of_accounts.md
specs/03_events.md
specs/04_posting_engine.md
specs/05_ledger_trial_balance.md
```

A política de precedência continua:

```text
semântica dos Volumes I–III
    >
contrato das specs
    >
implementação
```

Se o código atual divergir desta spec, alterar o código.  
Se esta spec divergir dos volumes, corrigir a spec, não reinterpretar silenciosamente os volumes.

### Volume I — granularidade antes de agregação

O Volume I fixa:

```text
u_t
    -> reconhecimento/mensuração
    -> Lambda_t
    -> classificação/agregação
    -> S_t
```

e trata `u_t` como família granular de eventos, não como balancete pronto.

Logo, o workbook não pode eliminar `EVENTOS` depois de gerar a escrituração.

### Volume II — agregados podem ser insuficientes

O Volume II mostra que dois conjuntos de eventos podem produzir o mesmo agregado contábil e resultados tributários diferentes.

Portanto:

```text
BALANCETE
RAZAO
```

não substituem:

```text
EVENTOS
```

como fonte granular para a futura camada tributária.

A Spec 06 deve manter `EVENTOS` como entrada persistida e preservar `ID_ORIGEM`, `DOC_REF` e vínculos de rastreabilidade.

### Volume III — workbook como interface física

O Volume III define:

```text
Wb_t =
(
    T_cfg,
    T_ent,
    T_pc,
    T_ev,
    T_lct,
    T_part,
    T_raz,
    T_bal,
    T_map,
    ...
)
```

e fixa a regra operacional:

```text
editar entradas
    -> regenerar núcleo
    -> recalcular saídas
```

Também estabelece:

- Python como motor de geração, validação e reconciliação;
- Excel como interface de inspeção e manipulação controlada;
- `.xlsx` sem macros no MVP;
- tabelas nomeadas;
- chaves estáveis;
- objetos derivados não editados independentemente.

A Spec 06 implementa essa camada sem antecipar BP/DRE.

---

# Decisão arquitetural central desta spec

## Problema atual

No Marco A, o motor usa um mapeamento fixo equivalente a:

```text
caixa                   -> 1.1.01.01
banco                   -> 1.1.01.02
clientes                -> 1.1.02.01
estoques                -> 1.1.03.01
fornecedores            -> 2.1.01.01
capital_social          -> 3.1.01.01
receita_vendas          -> 4.1.01.01
cmv                     -> 4.2.01.01
...
```

Esse desenho foi deliberadamente aceitável no Marco A.

Ele deixa de ser suficiente quando `PLANO_CONTAS` se torna entrada editável, pois a regra econômica:

```text
D Caixa
C Capital Social
```

não deve depender de o código físico de Caixa ser necessariamente:

```text
1.1.01.01
```

## Solução mínima

Introduzir uma configuração tabular:

```text
MAPEAMENTO_CONTAS
```

com contrato:

```text
PAPEL_CONTABIL -> COD_CTA
```

Exemplo:

| PAPEL_CONTABIL | COD_CTA |
|---|---|
| `caixa` | `1.1.01.01` |
| `banco` | `1.1.01.02` |
| `clientes` | `1.1.02.01` |
| `estoques` | `1.1.03.01` |
| `fornecedores` | `2.1.01.01` |
| `capital_social` | `3.1.01.01` |
| `receita_vendas` | `4.1.01.01` |
| `cmv` | `4.2.01.01` |

Assim:

```text
regra de escrituração
    + papel contábil
    + MAPEAMENTO_CONTAS
    -> COD_CTA
```

em vez de:

```text
regra de escrituração
    -> código hard-coded
```

---

## Distinção obrigatória: `MAPEAMENTO_CONTAS` != `MAPEAMENTO_DF`

Esta spec introduz `MAPEAMENTO_CONTAS` como **objeto de engenharia do MVP**.

Ele não substitui nem redefine:

```text
map_t^S
MAPEAMENTO_DF
```

do Volume III.

Os objetos têm funções diferentes:

| Objeto | Pergunta | Implementação |
|---|---|---|
| `MAPEAMENTO_CONTAS` | qual `COD_CTA` desempenha o papel `caixa`, `estoques`, `clientes`, etc.? | Spec 06 |
| `MAPEAMENTO_DF` / `map_t^S` | em qual linha de BP/DRE/etc. uma conta deve ser agregada? | Spec 07 |

Portanto:

```text
PAPEL_CONTABIL -> COD_CTA
```

é anterior a:

```text
COD_CTA -> linha da demonstração S
```

Não introduzir um novo símbolo matemático canônico para `MAPEAMENTO_CONTAS` nesta etapa. O nome Python reservado será:

```text
account_role_mapping
```

e o nome físico Excel será:

```text
MAPEAMENTO_CONTAS
```

---

# Escopo

Implementar nesta spec:

1. `openpyxl` como única nova dependência de runtime;
2. `account_role_mapping` como `DataFrame` validado;
3. remoção da dependência runtime de códigos hard-coded no `posting.py`;
4. default mapping compatível com o template comercial existente;
5. workbook `.xlsx`;
6. leitura das abas de entrada;
7. geração das abas derivadas;
8. tabelas Excel nomeadas;
9. filtros e congelamento de cabeçalhos;
10. formatos de data e moeda legíveis;
11. validações de dados simples em campos de enum das abas editáveis;
12. aba `VALIDACOES`;
13. aba `PROVENIENCIA`;
14. round-trip das entradas:
    `Python -> Excel -> Python`;
15. regeneração:
    `Excel editado -> Python -> novo Excel`;
16. teste explícito de recodificação de conta sem alterar a regra econômica.

---

# Fora de escopo

Não implementar nesta spec:

- BP;
- DRE;
- DFC;
- DVA;
- `MAPEAMENTO_DF` como tabela independente;
- `ENTIDADE` com `rho_t`/`eta_t`;
- tributação;
- `FISCAL_*`;
- centros de custo;
- cadastro separado de participantes;
- histórico padronizado;
- ECD textual;
- ECF;
- macros;
- VBA;
- `.xlsm`;
- fórmulas contábeis como fonte de verdade;
- proteção sofisticada por senha;
- dashboards;
- gráficos;
- Power Query;
- Power Pivot;
- banco de dados;
- CLI completa;
- interface web;
- geração aleatória;
- múltiplos períodos;
- múltiplas entidades;
- engine genérico de regras;
- importação de workbook arbitrário de terceiros.

As abas canônicas futuras:

```text
ENTIDADE
CENTROS_CUSTO
PARTICIPANTES
HISTORICOS
MAPEAMENTO_DF
BP
DRE
DFC
DVA
FISCAL_*
```

permanecem reservadas, mas **não devem ser criadas vazias** nesta etapa.

---

# Entradas

A fonte de verdade lógica desta etapa é:

```python
simulation_config: SimulationConfig
chart_of_accounts: pd.DataFrame
account_role_mapping: pd.DataFrame
events: pd.DataFrame
```

Correspondência:

| Objeto | Aba editável |
|---|---|
| `SimulationConfig` / `Omega^sim` parcial | `CONFIG` |
| `P_t` | `PLANO_CONTAS` |
| configuração papel -> conta | `MAPEAMENTO_CONTAS` |
| `u_t` | `EVENTOS` |

## Fonte de verdade operacional

O workbook pode ser usado como persistência das entradas, mas apenas estas quatro abas devem ser lidas para regenerar o modelo:

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
```

As demais abas são derivadas.

Qualquer alteração manual em:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
VALIDACOES
PROVENIENCIA
```

deve ser ignorada na próxima regeneração e sobrescrita.

---

# Saídas

O artefato principal é:

```text
output/*.xlsx
```

O workbook deve conter, nesta ordem:

```text
README
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
VALIDACOES
PROVENIENCIA
```

Essas são as únicas abas obrigatórias da Spec 06.

---

# Schema — `MAPEAMENTO_CONTAS`

Ordem canônica:

| Coluna | Tipo interno | Obrigatória | Regra |
|---|---|---:|---|
| `PAPEL_CONTABIL` | `str` | sim | papel semântico único |
| `COD_CTA` | `str` | sim | FK para conta analítica ativa de `PLANO_CONTAS` |

Definir:

```python
ACCOUNT_ROLE_MAPPING_COLUMNS = (
    "PAPEL_CONTABIL",
    "COD_CTA",
)
```

## Papéis contábeis da política v1

Papéis obrigatórios:

```text
caixa
banco
clientes
estoques
depreciacao_acumulada
fornecedores
capital_social
receita_vendas
cmv
despesa_salarios
despesa_aluguel
despesa_utilidades
despesa_depreciacao
despesa_juros
```

Papel permitido/reservado no default, embora ainda não consumido diretamente pelas regras v1:

```text
imobilizado
```

Não criar taxonomia extensível ou plugin de papéis.

---

## Mapeamento default

O builder default deve reproduzir semanticamente o mapeamento atual:

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

Esse default preserva todos os testes econômicos do Marco A.

---

# Invariantes de `MAPEAMENTO_CONTAS`

## M1 — papel único

```text
PAPEL_CONTABIL
```

é chave primária do mapping e não pode ser duplicado.

## M2 — papéis obrigatórios

Todos os papéis consumidos pelas regras v1 devem estar presentes.

## M3 — conta existente

Todo `COD_CTA` mapeado deve existir em `PLANO_CONTAS`.

## M4 — conta analítica

Toda conta mapeada deve satisfazer:

```text
IND_CTA = A
```

## M5 — conta ativa

Toda conta mapeada deve satisfazer:

```text
ATIVA = True
```

## M6 — compatibilidade semântica mínima

Validar a natureza da conta (`COD_NAT`) e a orientação normal (`NAT_SALDO_NORMAL`) conforme o papel.

Expectativas:

| Papel | `COD_NAT` | saldo normal |
|---|---|---|
| `caixa` | `01` | `D` |
| `banco` | `01` | `D` |
| `clientes` | `01` | `D` |
| `estoques` | `01` | `D` |
| `imobilizado` | `01` | `D` |
| `depreciacao_acumulada` | `01` | `C` |
| `fornecedores` | `02` | `C` |
| `capital_social` | `03` | `C` |
| `receita_vendas` | `04` | `C` |
| `cmv` | `04` | `D` |
| `despesa_salarios` | `04` | `D` |
| `despesa_aluguel` | `04` | `D` |
| `despesa_utilidades` | `04` | `D` |
| `despesa_depreciacao` | `04` | `D` |
| `despesa_juros` | `04` | `D` |

A validação é uma restrição semântica do arquétipo comercial v1.

Não generalizar essa matriz para qualquer empresa.

## M7 — não exigir `COD_CTA` único

Dois papéis semanticamente compatíveis podem apontar para a mesma conta analítica.

Exemplo futuro admissível:

```text
despesa_aluguel
despesa_utilidades
```

podem apontar para uma conta genérica de despesas administrativas.

O que é único é `PAPEL_CONTABIL`, não necessariamente `COD_CTA`.

## M8 — recodificação suportada

Se a conta `Caixa` mudar de:

```text
1.1.01.01
```

para:

```text
1.01.001.0001
```

e:

- o plano continuar válido;
- `MAPEAMENTO_CONTAS` for atualizado;
- a conta continuar analítica, ativa e semanticamente compatível;

o posting engine deve continuar produzindo a mesma regra econômica usando o novo código.

Esse é um teste obrigatório da Spec 06.

---

# Refatoração mínima do posting engine

## Regra

`posting.py` não deve mais resolver contas consultando diretamente códigos fixos.

O fluxo deve ser:

```text
TIPO_EVENTO
    -> papel contábil
    -> account_role_mapping
    -> COD_CTA
```

## Compatibilidade com o Marco A

É permitido manter o antigo `ACCOUNT_CODE_MAP`:

- como alias temporário;
- ou renomeá-lo para algo como `DEFAULT_ACCOUNT_ROLE_MAP`;

desde que ele passe a representar **somente o default do template**, não a fonte runtime obrigatória.

A API de `post_events()` deve preservar compatibilidade razoável com as specs anteriores.

Assinatura recomendada:

```python
def post_events(
    events: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
    simulation_config: SimulationConfig,
    *,
    account_role_mapping: pd.DataFrame | None = None,
    rule_version: str = "posting_rules_v1",
) -> PostingResult:
    ...
```

Comportamento:

```text
account_role_mapping is None
    -> usar mapping default

account_role_mapping fornecido
    -> validar e usar exatamente esse mapping
```

O caminho do workbook deve sempre fornecer explicitamente o mapping lido da aba `MAPEAMENTO_CONTAS`.

---

# Contrato físico do workbook

## Classes de abas

### Entrada/configuração

Editáveis:

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
```

### Núcleo gerado

Não são fonte de verdade:

```text
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
```

### Saídas derivadas

```text
DIARIO
RAZAO
BALANCETE
VALIDACOES
PROVENIENCIA
```

### Documentação

```text
README
```

---

# Aba `README`

Conteúdo humano simples.

Deve informar pelo menos:

```text
Projeto: Contabilidade parametrizada
Workbook spec: spec_06_excel_workbook_v1
Moeda: BRL
```

e destacar:

```text
ABAS EDITÁVEIS:
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS

ABAS GERADAS:
LANCAMENTOS
PARTIDAS
VINCULO_EVENTO_LCTO
DIARIO
RAZAO
BALANCETE
VALIDACOES
PROVENIENCIA
```

Também incluir a regra:

```text
edite entradas -> execute regeneração Python -> inspecione saídas
```

e o aviso:

```text
alterações manuais em abas geradas serão sobrescritas
```

Não transformar README em documentação extensa.

---

# Aba `CONFIG`

Representar `SimulationConfig` como tabela vertical simples:

| `CHAVE` | `VALOR` |
|---|---|
| `simulation_id` | texto |
| `start_date` | data |
| `end_date` | data |
| `currency` | `BRL` |
| `seed` | inteiro |
| `scenario_name` | texto |
| `spec_version` | texto |

Ordem das chaves deve ser determinística.

Não adicionar parâmetros aleatórios novos nesta etapa.

`seed` continua sendo metadado reservado; a Spec 06 não gera eventos aleatórios.

---

# Aba `PLANO_CONTAS`

Materializar exatamente o schema lógico da Spec 02:

```text
DT_ALT
COD_NAT
IND_CTA
NIVEL
COD_CTA
COD_CTA_SUP
CTA
NAT_SALDO_NORMAL
COD_DF
ATIVA
ORIGEM
```

Não renomear campos.

A aba é editável.

Qualquer edição só passa a ter efeito depois de leitura + validação + regeneração.

---

# Aba `MAPEAMENTO_CONTAS`

Schema:

```text
PAPEL_CONTABIL
COD_CTA
```

A aba é editável.

Ela deve ser escrita imediatamente depois de `PLANO_CONTAS` para tornar visível a dependência:

```text
PAPEL_CONTABIL -> COD_CTA
```

---

# Aba `EVENTOS`

## Interface monetária

O núcleo Python continua usando:

```text
VL_EVENTO_CENTS
VL_CUSTO_CENTS
```

como `int`.

No Excel, para leitura humana, usar:

```text
VL_EVENTO
VL_CUSTO
```

em BRL com duas casas decimais.

O schema físico da aba será:

```text
ID_EVENTO
DT_EVENTO
CLASSE_EVENTO
TIPO_EVENTO
DIRECAO
NATUREZA
VL_EVENTO
VL_CUSTO
MEIO_FINANCEIRO
CATEGORIA_DESPESA
COD_PART
COND_PAGTO
DOC_REF
HIST
ORIGEM
SPEC_VERSION
```

A tradução deve ser explícita:

```text
VL_EVENTO_CENTS <-> VL_EVENTO
VL_CUSTO_CENTS  <-> VL_CUSTO
```

Não manter simultaneamente colunas em reais e centavos na mesma aba.

---

# Aba `LANCAMENTOS`

Schema físico:

```text
NUM_LCTO
DT_LCTO
VL_LCTO
IND_LCTO
DT_LCTO_EXT
ID_GERACAO
VERSAO_REGRA
```

Tradução:

```text
VL_LCTO_CENTS <-> VL_LCTO
```

A aba é gerada.

---

# Aba `PARTIDAS`

Schema físico:

```text
ID_PARTIDA
NUM_LCTO
COD_CTA
COD_CCUS
VL_DC
IND_DC
NUM_ARQ
COD_HIST_PAD
HIST
COD_PART
ID_ORIGEM
```

Tradução:

```text
VL_DC_CENTS <-> VL_DC
```

A aba é gerada.

---

# Aba `VINCULO_EVENTO_LCTO`

Manter:

```text
ID_EVENTO
NUM_LCTO
ORDEM_LCTO_EVENTO
```

Sem transformação monetária.

---

# Aba `DIARIO`

Materializar a visão atual da Spec 05, usando `VL_DC` em BRL na interface:

```text
DT_LCTO
NUM_LCTO
ID_PARTIDA
COD_CTA
CTA
IND_DC
VL_DC
HIST
COD_PART
ID_ORIGEM
```

A aba é derivada.

---

# Aba `RAZAO`

No Excel, converter as colunas monetárias do núcleo:

```text
DEBITO_CENTS
CREDITO_CENTS
MOVIMENTO_ASSINADO_CENTS
SALDO_ASSINADO_CENTS
SALDO_ABS_CENTS
```

para:

```text
DEBITO
CREDITO
MOVIMENTO_ASSINADO
SALDO_ASSINADO
SALDO_ABS
```

Schema físico:

```text
COD_CTA
CTA
DT_LCTO
NUM_LCTO
ID_PARTIDA
DEBITO
CREDITO
MOVIMENTO_ASSINADO
SALDO_ASSINADO
SALDO_ABS
IND_DC_SALDO
HIST
ID_ORIGEM
```

Uma única aba `RAZAO`.

Não criar uma aba por conta.

---

# Aba `BALANCETE`

Schema físico compatível com o Volume III:

```text
DT_INI
DT_FIN
COD_CTA
COD_CCUS
VL_SLD_INI
IND_DC_INI
VL_DEB
VL_CRED
VL_SLD_FIN
IND_DC_FIN
```

Traduções:

```text
VL_SLD_INI_CENTS <-> VL_SLD_INI
VL_DEB_CENTS     <-> VL_DEB
VL_CRED_CENTS    <-> VL_CRED
VL_SLD_FIN_CENTS <-> VL_SLD_FIN
```

A aba é derivada.

---

# Conversão monetária Python <-> Excel

## Núcleo Python

Permanece:

```python
int  # centavos
```

## Excel

Exibir valores em BRL com duas casas decimais.

Exemplo:

```text
10000000 cents
    <->
100000.00 BRL
```

## Escrita

A conversão para a interface deve ocorrer apenas no limite do workbook.

## Leitura

Ao ler valores monetários editáveis do Excel:

1. não tratar `float` binário como fonte de verdade;
2. converter o valor lido por representação decimal segura;
3. exigir no máximo duas casas decimais;
4. converter para `int` centavos;
5. rejeitar valor que não seja exatamente representável em centavos.

Implementação recomendada:

```text
valor Excel
    -> Decimal(str(valor))
    -> * 100
    -> validação de integralidade
    -> int cents
```

Não usar comparações contábeis em `float`.

---

# Aba `VALIDACOES`

Objetivo: tornar visíveis no workbook os invariantes já executados pelo Python.

Schema recomendado:

```text
ETAPA
OK
ISSUE_CODE
MENSAGEM
ACCOUNT_CODE
EVENT_ID
ENTRY_ID
POSTING_ID
```

Validadores mínimos a representar:

```text
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
LANCAMENTOS_PARTIDAS
RAZAO_BALANCETE
```

Comportamento:

### Validador sem problemas

Produzir uma linha:

```text
ETAPA = ...
OK = TRUE
ISSUE_CODE = null
MENSAGEM = "ok"
```

### Validador com problemas

Produzir uma linha por `ValidationIssue`.

O workbook final de um cenário aceito deve conter apenas `OK=TRUE`.

A aba não substitui exceções de Python. Entradas inválidas devem continuar falhando cedo no processo de regeneração.

---

# Aba `PROVENIENCIA`

A aba é de governança, não de cálculo.

Schema mínimo:

```text
CHAVE
VALOR
```

Registrar pelo menos:

```text
workbook_spec_version = spec_06_excel_workbook_v1
simulation_id
scenario_name
simulation_spec_version
posting_rule_version
currency
chart_source
event_spec_versions
```

Não inserir timestamp obrigatório no MVP.

Motivo:

```text
mesmas entradas
    -> mesmos dados materializados
```

deve permanecer facilmente testável.

Se uma data/hora de geração for adicionada depois, deve ser explicitamente excluída dos testes de determinismo.

Não introduzir proveniência tributária `Prov(p)` nesta spec; essa camada continua reservada aos Volumes II/Spec 11.

---

# Tabelas Excel nomeadas

Todas as abas tabulares, exceto `README`, devem conter uma tabela Excel nomeada.

Nomes recomendados:

```text
tbl_CONFIG
tbl_PLANO_CONTAS
tbl_MAPEAMENTO_CONTAS
tbl_EVENTOS
tbl_LANCAMENTOS
tbl_PARTIDAS
tbl_VINCULO_EVENTO_LCTO
tbl_DIARIO
tbl_RAZAO
tbl_BALANCETE
tbl_VALIDACOES
tbl_PROVENIENCIA
```

As tabelas devem:

- conter cabeçalho;
- abranger exatamente os dados materializados;
- habilitar filtro;
- possuir nomes únicos.

Não usar ranges soltos como fonte principal quando uma tabela nomeada resolver.

---

# Usabilidade mínima do workbook

Implementar apenas:

1. cabeçalhos em destaque;
2. congelamento da primeira linha nas abas tabulares;
3. filtros via tabelas Excel;
4. largura de coluna razoável;
5. datas exibidas de forma legível;
6. moeda com duas casas decimais;
7. distinção visual simples entre:
   - entradas;
   - núcleo gerado;
   - saídas;
8. README com legenda de editabilidade.

Não criar identidade visual sofisticada.

---

# Validação de dados Excel

Adicionar validações simples nas abas editáveis quando não aumentarem significativamente a complexidade.

## `PLANO_CONTAS`

Candidatos:

```text
COD_NAT
IND_CTA
NAT_SALDO_NORMAL
ATIVA
ORIGEM
```

## `EVENTOS`

Candidatos:

```text
CLASSE_EVENTO
TIPO_EVENTO
DIRECAO
NATUREZA
MEIO_FINANCEIRO
CATEGORIA_DESPESA
COND_PAGTO
ORIGEM
```

## `CONFIG`

```text
currency = BRL
```

Não tornar dropdown dinâmico de `COD_CTA` requisito obrigatório do MVP.

A integridade de `MAPEAMENTO_CONTAS.COD_CTA` deve ser garantida pelo Python mesmo que o Excel permita digitação manual.

---

# Fonte de verdade e regeneração

A implementação deve obedecer literalmente:

```text
editar entradas
    -> ler somente abas de entrada
    -> validar
    -> gerar Lambda_t
    -> derivar Dia_t / Raz_t / b_t
    -> reconstruir workbook
```

Nunca:

```text
editar BALANCETE
    -> aceitar novo saldo como verdade
```

ou:

```text
editar RAZAO
    -> preservar alteração na próxima execução
```

---

# API mínima — account mapping

Criar preferencialmente:

```text
src/accounting_sim/account_mapping.py
```

API:

```python
def build_default_account_role_mapping() -> pd.DataFrame:
    ...


def validate_account_role_mapping(
    mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> ValidationReport:
    ...


def account_role_map_as_dict(
    mapping: pd.DataFrame,
    chart_of_accounts: pd.DataFrame,
) -> dict[str, str]:
    ...
```

Não criar classe `AccountRole` por linha.

---

# API mínima — workbook

Criar:

```text
src/accounting_sim/workbook.py
```

Dataclass pequena:

```python
@dataclass(frozen=True)
class WorkbookInputs:
    simulation_config: SimulationConfig
    chart_of_accounts: pd.DataFrame
    account_role_mapping: pd.DataFrame
    events: pd.DataFrame
```

API recomendada:

```python
def build_workbook(
    inputs: WorkbookInputs,
    path: str | Path,
    *,
    rule_version: str = "posting_rules_v1",
) -> Path:
    ...


def load_workbook_inputs(
    path: str | Path,
) -> WorkbookInputs:
    ...


def regenerate_workbook(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    rule_version: str = "posting_rules_v1",
) -> Path:
    ...
```

Comportamento de `regenerate_workbook()`:

```text
1. ler CONFIG / PLANO_CONTAS / MAPEAMENTO_CONTAS / EVENTOS;
2. validar entradas;
3. executar post_events(..., account_role_mapping=...);
4. construir DIARIO;
5. construir RAZAO;
6. construir BALANCETE;
7. construir VALIDACOES;
8. construir PROVENIENCIA;
9. criar novo workbook;
10. salvar .xlsx.
```

Se `output_path is None`, é aceitável sobrescrever `input_path` **somente depois que todas as entradas tiverem sido lidas e validadas com sucesso**.

Falha de validação não deve destruir o workbook de origem.

---

# Orquestração interna

`build_workbook()` deve reutilizar, e não duplicar:

```text
validate_chart_of_accounts
validate_events
validate_account_role_mapping
post_events
validate_posting_result
build_journal
build_ledger
build_trial_balance
validate_ledger_trial_balance
```

A Spec 06 não deve recalcular:

- partida dobrada por lógica própria;
- saldo corrido por lógica própria;
- regras de evento por lógica própria.

O workbook é consumidor dos objetos já validados.

---

# Invariantes do workbook

## W1 — modelo lógico preservado

A escrita do workbook não modifica os DataFrames de entrada in-place.

## W2 — quatro fontes editáveis

Somente:

```text
CONFIG
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
```

são lidas na regeneração.

## W3 — núcleo derivado

`LANCAMENTOS`, `PARTIDAS` e `VINCULO_EVENTO_LCTO` são sempre regenerados por `post_events()`.

## W4 — views derivadas

`DIARIO`, `RAZAO` e `BALANCETE` são sempre reconstruídos a partir da escrituração.

## W5 — integridade do mapeamento

Toda conta usada pelo posting engine é resolvida via `account_role_mapping`.

## W6 — round-trip de entradas

Para um workbook não editado:

```text
inputs
    -> build_workbook
    -> load_workbook_inputs
```

deve preservar semanticamente:

```text
SimulationConfig
PLANO_CONTAS
MAPEAMENTO_CONTAS
EVENTOS
```

Datas retornam como `date`.  
Valores monetários retornam como `int` centavos.

## W7 — alteração de código suportada

Recodificar uma conta analítica e atualizar `MAPEAMENTO_CONTAS` deve alterar apenas a chave física utilizada nas partidas, não a regra econômica.

## W8 — edição de saída é descartável

Se uma célula em `BALANCETE` ou `RAZAO` for alterada manualmente, `load_workbook_inputs()` não deve consumir essa alteração.

Após regeneração, o valor derivado correto deve reaparecer.

## W9 — formato físico válido

O arquivo final deve:

```text
abrir com openpyxl
conter todas as abas obrigatórias
conter todas as tabelas nomeadas obrigatórias
```

## W10 — valores monetários

Todas as grandezas monetárias apresentadas no workbook usam BRL com duas casas decimais.

Os invariantes contábeis continuam sendo calculados em centavos no Python.

## W11 — determinismo sem exigir ZIP idêntico

Mesmas entradas devem produzir as mesmas tabelas e valores após reabertura.

Não exigir igualdade byte-a-byte entre arquivos `.xlsx`, pois metadados internos do formato ZIP/Office podem variar.

## W12 — nenhuma demonstração antecipada

A Spec 06 não cria:

```text
BP
DRE
DFC
DVA
MAPEAMENTO_DF
```

Esses objetos pertencem à Spec 07 ou posteriores.

## W13 — nenhuma tributação antecipada

Não criar:

```text
FISCAL_PARAM
FISCAL_OPERACOES
FISCAL_APURACAO
CENARIOS
```

## W14 — eventos preservados

`EVENTOS` continua presente mesmo quando toda a escrituração já foi gerada.

## W15 — rastreabilidade

Deve continuar possível seguir:

```text
BALANCETE/RAZAO
    -> ID_PARTIDA
    -> NUM_LCTO
    -> ID_ORIGEM / VINCULO_EVENTO_LCTO
    -> ID_EVENTO
```

---

# Casos de exemplo

## Caso A — workbook canônico do Marco A

Usar o exemplo canônico:

```text
aporte de capital      100000
compra à vista          30000
venda a prazo           50000  custo 20000
recebimento cliente     30000
```

Esperar:

```text
5 lançamentos
10 partidas
230000.00 BRL de débitos
230000.00 BRL de créditos
```

Saldos não nulos:

```text
Caixa                     100000.00 D
Clientes                    20000.00 D
Estoques                    10000.00 D
Capital Social             100000.00 C
Receita de Vendas           50000.00 C
CMV                         20000.00 D
```

No workbook:

```text
saldos devedores = 150000.00
saldos credores  = 150000.00
```

Não gerar BP/DRE ainda.

---

## Caso B — recodificação de Caixa

Partir do plano default.

Alterar:

```text
PLANO_CONTAS.COD_CTA
1.1.01.01
    ->
1.01.001.0001
```

e:

```text
MAPEAMENTO_CONTAS
caixa -> 1.01.001.0001
```

Preservar:

- nome `Caixa`;
- natureza `01`;
- tipo `A`;
- saldo normal `D`;
- hierarquia válida.

O mesmo aporte de capital deve gerar:

```text
D  1.01.001.0001
C  capital_social
```

sem alteração da regra econômica.

O teste deve provar que `posting.py` não contém dependência funcional do código antigo para resolver `caixa`.

---

## Caso C — mapping inválido

Exemplo:

```text
caixa -> 1.1.01
```

onde `1.1.01` é conta sintética.

Deve falhar com issue clara, por exemplo:

```text
mapped_account_not_analytic
```

---

## Caso D — natureza incompatível

Exemplo:

```text
receita_vendas -> conta COD_NAT=01
```

Deve falhar com:

```text
account_role_nature_mismatch
```

ou código equivalente estável.

---

## Caso E — edição manual de saída

1. gerar workbook válido;
2. abrir via `openpyxl`;
3. alterar manualmente um saldo em `BALANCETE`;
4. salvar;
5. carregar com `load_workbook_inputs()`;
6. regenerar;
7. verificar que o saldo adulterado desaparece.

Isso prova:

```text
BALANCETE != fonte de verdade
```

---

# Testes obrigatórios — account mapping

Criar:

```text
tests/test_account_mapping.py
```

Cobrir pelo menos:

1. colunas na ordem canônica;
2. default mapping contém todos os papéis obrigatórios;
3. `PAPEL_CONTABIL` único;
4. conta inexistente rejeitada;
5. conta sintética rejeitada;
6. conta inativa rejeitada;
7. natureza incompatível rejeitada;
8. saldo normal incompatível rejeitado;
9. `COD_CTA` duplicado entre papéis semanticamente compatíveis é permitido;
10. default mapping reproduz comportamento econômico anterior;
11. recodificação de Caixa funciona;
12. recodificação de Estoques funciona em compra/venda;
13. mapping fornecido é realmente consumido pelo posting engine.

---

# Testes obrigatórios — workbook

Criar:

```text
tests/test_workbook.py
```

Cobrir pelo menos:

1. `openpyxl` está disponível como dependência;
2. `build_workbook()` cria `.xlsx`;
3. workbook pode ser reaberto;
4. abas existem exatamente na ordem definida;
5. abas futuras não foram antecipadas;
6. tabelas nomeadas existem;
7. cada tabela cobre o número correto de linhas;
8. `CONFIG` round-trip preserva tipos;
9. `PLANO_CONTAS` round-trip preserva chaves, datas, bools e hierarquia;
10. `MAPEAMENTO_CONTAS` round-trip preserva papéis e códigos;
11. `EVENTOS` round-trip preserva IDs, datas e valores em centavos;
12. valores monetários são apresentados em reais com duas casas;
13. `LANCAMENTOS` do caso canônico têm 5 linhas;
14. `PARTIDAS` do caso canônico têm 10 linhas;
15. totais do caso canônico aparecem como `230000.00` por lado;
16. `RAZAO` apresenta saldos esperados;
17. `BALANCETE` apresenta `150000.00` de saldos devedores e credores;
18. `VALIDACOES` não possui falha no caso canônico;
19. `PROVENIENCIA` contém versão da spec e regra;
20. edição manual de `BALANCETE` é ignorada na regeneração;
21. edição manual de `RAZAO` é ignorada na regeneração;
22. recodificação de `Caixa` + atualização do mapping propaga o novo código para `PARTIDAS`;
23. mesma entrada gera mesmos valores após duas materializações;
24. funções não modificam DataFrames de entrada;
25. nenhuma fórmula Excel é necessária para fechar a escrituração.

---

# Teste de regressão global

Antes de implementar:

```text
python -m pytest -q
```

deve registrar a baseline atual.

Após a implementação:

```text
python -m pytest -q
```

deve manter todas as specs 00–05 passando.

Em particular, preservar:

```text
5 lançamentos
10 partidas
23000000 cents de débito
23000000 cents de crédito
15000000 cents de saldos devedores
15000000 cents de saldos credores
```

no núcleo Python.

A Spec 06 muda a interface e a resolução de contas; ela não muda esses invariantes econômicos.

---

# Passos de implementação

1. executar a suíte completa e registrar baseline;
2. adicionar `openpyxl` em `pyproject.toml`;
3. adicionar `ACCOUNT_ROLE_MAPPING_COLUMNS`;
4. criar `account_mapping.py`;
5. criar builder do mapping default;
6. implementar validação do mapping;
7. adaptar `posting.py` para resolver papéis pelo mapping;
8. preservar comportamento default da Spec 04;
9. adicionar testes de recodificação;
10. criar `workbook.py`;
11. implementar `WorkbookInputs`;
12. implementar tradução `cents <-> BRL Excel`;
13. implementar `CONFIG`;
14. implementar as quatro abas editáveis;
15. reutilizar o núcleo para gerar as abas derivadas;
16. implementar `VALIDACOES`;
17. implementar `PROVENIENCIA`;
18. aplicar tabelas nomeadas;
19. aplicar filtros, freeze panes e formatação mínima;
20. adicionar validações de dados simples;
21. implementar `load_workbook_inputs()`;
22. implementar `regenerate_workbook()`;
23. testar adulteração de abas derivadas;
24. testar recodificação de conta no workbook;
25. reabrir todos os workbooks criados nos testes;
26. rodar suíte completa;
27. atualizar README do repositório para indicar Spec 06 implementada.

---

# Critérios de aceitação

A Spec 06 está aceita se:

- [ ] `openpyxl` é a única nova dependência necessária;
- [ ] existe `MAPEAMENTO_CONTAS` validado;
- [ ] `posting.py` aceita mapping parametrizado;
- [ ] comportamento default do Marco A não mudou;
- [ ] um código de conta pode ser alterado sem alterar a regra econômica;
- [ ] `build_workbook()` gera arquivo `.xlsx` válido;
- [ ] `load_workbook_inputs()` lê somente as quatro abas de entrada;
- [ ] `regenerate_workbook()` reconstrói todas as abas derivadas;
- [ ] alterações manuais em Razão/balancete não viram fonte de verdade;
- [ ] `EVENTOS` permanece preservado;
- [ ] rastreabilidade evento -> lançamento -> partida permanece íntegra;
- [ ] valores críticos continuam sendo calculados em centavos no Python;
- [ ] Excel apresenta valores em BRL com duas casas;
- [ ] workbook possui tabelas nomeadas e filtros;
- [ ] workbook possui `VALIDACOES`;
- [ ] workbook possui `PROVENIENCIA`;
- [ ] BP/DRE não foram implementados;
- [ ] tributação não foi implementada;
- [ ] geração aleatória não foi implementada;
- [ ] nenhuma arquitetura genérica de regras foi criada;
- [ ] todos os testes 00–06 passam.

---

# Arquivos esperados

Criar:

```text
src/accounting_sim/account_mapping.py
src/accounting_sim/workbook.py

tests/test_account_mapping.py
tests/test_workbook.py

specs/06_excel_workbook.md
```

Alterar apenas quando necessário:

```text
src/accounting_sim/canonical.py
src/accounting_sim/posting.py
src/accounting_sim/__init__.py
pyproject.toml
README.md
```

Não alterar a semântica dos módulos:

```text
events.py
ledger.py
chart_of_accounts.py
```

salvo correção mínima demonstravelmente necessária por teste de integração.

---

# Dependências de outras specs

## Spec 00

Preserva:

- MVP simples;
- Python como motor;
- `openpyxl` permitido somente a partir da Spec 06;
- centavos como fonte de verdade;
- `.xlsx` sem macros.

## Spec 01

Preserva:

```text
Wb_t -> workbook
P_t -> PLANO_CONTAS
u_t -> EVENTOS
Lambda_t -> LANCAMENTOS + PARTIDAS
V_t -> VINCULO_EVENTO_LCTO
Dia_t -> DIARIO
Raz_t -> RAZAO
b_t -> BALANCETE
```

Não introduz aliases conflitantes.

## Spec 02

`PLANO_CONTAS` continua sendo o único cadastro autoritativo de `COD_CTA`.

`MAPEAMENTO_CONTAS` apenas referencia suas contas.

## Spec 03

`EVENTOS` continua sendo a materialização de `u_t`.

A interface Excel converte apenas a unidade monetária de apresentação.

## Spec 04

A política de débito/crédito não muda.

Somente a resolução:

```text
papel -> COD_CTA
```

se torna parametrizada.

## Spec 05

Diário, Razão e balancete continuam derivados exclusivamente de `LANCAMENTOS` e `PARTIDAS`.

Nenhuma lógica econômica é movida para Excel.

---

# Preservação explícita dos Volumes I–III

A Spec 06 não altera:

```text
x_{t+1} = F(x_t, u_t; vartheta_t)

vartheta_t = (theta_t^acct, Theta_t^tax)

u_t = u_t^tr sqcup u_t^adj

E_t : (x_t, u_t, P_t; theta_t^acct) -> Lambda_t

Lambda_t -> Dia_t
Lambda_t -> Raz_t
Raz_t -> b_t

G^S
rho_t
eta_t
zeta_t
Theta_t^eff
Prov
```

Também não altera a distinção:

```text
plano de contas
!=
base tributária
```

nem:

```text
modelo lógico
!=
workbook Excel
```

O ganho desta spec é estritamente de interface e parametrização operacional:

```text
PAPEL_CONTABIL -> COD_CTA
```

e:

```text
(P_t, u_t, Lambda_t, Dia_t, Raz_t, b_t)
    -> Wb_t
```

sem modificar a semântica dos objetos canônicos.
