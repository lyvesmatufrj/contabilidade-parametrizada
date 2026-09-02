# Spec 00 — Escopo do MVP contábil

**Status:** implementação inicial  
**Prioridade:** bloqueadora  
**Depende de:** Volumes I–III da parametrização canônica  
**Bloqueia:** specs 01–11

## Objetivo

Congelar a fronteira da primeira implementação prática do sistema contábil parametrizado.

O MVP deve provar que a arquitetura canônica pode ser convertida em um objeto computacional simples e auditável, sem tentar construir um software contábil completo.

O alvo final do MVP é:

```text
configuração
    -> P_t            plano de contas
    -> u_t            eventos
    -> Lambda_t       lançamentos + partidas
    -> Dia_t/Raz_t    visões da escrituração
    -> b_t            balancete
    -> BP + DRE
    -> Wb_t (.xlsx)
```

## Contexto canônico

A implementação deve preservar as seguintes identidades:

```text
x_{t+1} = F(x_t, u_t; vartheta_t)

vartheta_t = (theta_t^acct, Theta_t^tax)

E_t : (x_t, u_t, P_t; theta_t^acct) -> Lambda_t

Lambda_t -> (Dia_t, Raz_t, b_t) -> G^S -> S_t
```

Nesta rodada, a camada tributária existe apenas como **fronteira futura**. `rho_t`, `eta_t`, `zeta_t` e `Theta_t^eff` devem ter nomes reservados, mas não precisam ser calculados.

## Escopo

### Cenário empresarial

Usar inicialmente **uma empresa comercial simples** de compra e revenda de mercadorias.

Motivação prática: esse arquétipo permite exercitar, com poucos conceitos, os principais ramos necessários às specs futuras:

```text
compras
 -> estoque
 -> fornecedores
 -> pagamentos
 -> vendas
 -> clientes/caixa
 -> receita
 -> CMV
 -> despesas operacionais
```

### Horizonte

- uma única entidade;
- um único período contábil por execução;
- o período é definido por `start_date` e `end_date`;
- exemplos e testes podem usar um mês civil.

### Cobertura contábil mínima do MVP completo

Ao final das specs 00–10, o sistema deve suportar pelo menos:

1. plano de contas hierárquico;
2. eventos determinísticos;
3. lançamentos e partidas;
4. partida dobrada;
5. Diário;
6. Livro Razão;
7. balancete;
8. BP;
9. DRE;
10. workbook Excel;
11. validações explícitas;
12. reprodução determinística de um cenário.

### Primeira fase de implementação

Até a conclusão das specs 00–02, implementar apenas:

- scaffold do projeto;
- convenções canônicas de nomes e tipos;
- plano de contas e seus validadores;
- template de plano de contas de uma empresa comercial simples.

Não implementar ainda eventos, lançamentos ou Excel.

## Fora de escopo

Não implementar nesta primeira versão:

- cálculo de IBS, CBS, IRPJ, CSLL ou qualquer outro tributo;
- escolha/otimização de regime tributário;
- geração de ECD ou ECF textual;
- todos os registros do SPED;
- todos os CPCs;
- DFC e DVA com cobertura completa;
- consolidação de empresas;
- múltiplas moedas;
- inflação/correção monetária;
- estoque por SKU detalhado;
- custo médio/FIFO completos;
- folha de pagamento completa;
- ativo imobilizado completo;
- banco de dados;
- ORM;
- API REST/GraphQL;
- aplicação web/desktop;
- autenticação/usuários;
- filas, workers, serviços ou plugins;
- arquitetura de microserviços;
- otimizações prematuras de performance.

## Stack mínima

### Linguagem

- Python 3.12+.

### Dependências permitidas no primeiro ciclo

- `pandas` — tabelas e transformações;
- `openpyxl` — workbook Excel, apenas a partir da spec 06;
- `pytest` — testes;
- biblioteca padrão (`dataclasses`, `enum`, `datetime`, `decimal`, `pathlib`, `json`, `uuid` quando necessário).

### Dependências não necessárias inicialmente

Não adicionar sem justificativa em uma spec:

- Pydantic;
- SQLAlchemy;
- FastAPI/Django/Flask;
- NumPy diretamente se `pandas` já resolver o uso;
- frameworks de configuração;
- engines de regras genéricas.

## Estrutura mínima do repositório

```text
repo/
├── specs/
│   ├── README_specs_plan.md
│   ├── 00_mvp_scope.md
│   ├── 01_canonical_model.md
│   └── 02_chart_of_accounts.md
├── src/
│   └── accounting_sim/
│       ├── __init__.py
│       ├── canonical.py
│       └── chart_of_accounts.py
├── data/
│   └── templates/
│       └── chart_of_accounts_commercial.csv
├── tests/
│   ├── test_canonical.py
│   └── test_chart_of_accounts.py
├── output/
├── pyproject.toml
└── README.md
```

Não criar subpacotes adicionais até que uma spec posterior os exija.

## Regras de implementação

### R1 — simplicidade

Preferir funções pequenas e DataFrames explícitos a hierarquias de classes extensas.

### R2 — sem classes espelhando toda a matemática

Os símbolos matemáticos identificam objetos conceituais; não existe obrigação de criar uma classe Python para cada símbolo.

Exemplo:

```text
P_t -> DataFrame validado
```

é preferível, no MVP, a uma árvore profunda de classes `Chart`, `AccountGroup`, `AccountNode`, `AnalyticAccount`, etc.

### R3 — valores monetários

Não usar `float` binário como fonte de verdade para invariantes contábeis.

No núcleo computacional, representar valores monetários em **unidades monetárias menores inteiras**:

```python
amount_cents: int
```

Na apresentação/Excel, converter para duas casas decimais.

Essa é uma decisão de engenharia, não uma alteração do formalismo `v in R_+`.

### R4 — datas

- tipo interno: `datetime.date`;
- serialização textual: ISO 8601 `YYYY-MM-DD`.

### R5 — identificadores

- IDs são strings estáveis;
- não depender do número da linha do DataFrame como chave;
- código de conta `COD_CTA` é chave de negócio do plano no MVP.

### R6 — fonte de verdade

Objetos derivados deverão, nas specs posteriores, ser regenerados a partir das entradas.

```text
editar entrada -> regenerar núcleo -> recalcular saída
```

### R7 — falhar cedo

Dados inválidos devem produzir erro descritivo no ponto mais próximo da origem, em vez de serem corrigidos silenciosamente.

## Configuração mínima reservada

A futura `Omega^sim` deverá conter pelo menos:

```text
simulation_id
start_date
end_date
currency = BRL
seed
scenario_name
spec_version
```

Nesta spec, basta reservar esses nomes; a geração estocástica vem apenas na spec 08.

## Caso de demonstração alvo

A execução final do MVP deverá conseguir representar, ao menos, uma sequência como:

```text
1. aporte inicial de capital
2. compra de mercadoria a prazo
3. pagamento parcial de fornecedor
4. venda à vista
5. venda a prazo
6. recebimento de cliente
7. reconhecimento de CMV
8. pagamento de despesa operacional
9. depreciação simples
```

A lista é referência de cobertura, não requisito de implementação das specs 00–02.

## Testes obrigatórios desta spec

Ao implementar a spec 00:

1. `pytest` deve ser executável a partir da raiz;
2. o pacote `accounting_sim` deve ser importável;
3. o diretório `output/` deve existir, mas pode estar vazio;
4. nenhum módulo tributário deve ser criado;
5. não deve existir dependência de banco de dados ou framework web;
6. o README do repositório deve apontar para `specs/README_specs_plan.md`.

## Critérios de aceitação

A spec 00 está aceita se:

- [ ] a estrutura mínima do repositório existe;
- [ ] dependências estão declaradas em `pyproject.toml`;
- [ ] `pytest` roda com sucesso;
- [ ] o escopo e o fora-de-escopo estão documentados;
- [ ] nenhuma funcionalidade além da fronteira desta fase foi introduzida;
- [ ] os nomes reservados da spec 01 não foram redefinidos ad hoc.

## Arquivos esperados

Criados ou atualizados ao implementar esta spec:

```text
pyproject.toml
README.md
src/accounting_sim/__init__.py
specs/README_specs_plan.md
specs/00_mvp_scope.md
```

As specs 01 e 02 completarão os demais arquivos do scaffold.

## Dependências de outras specs

Nenhuma spec anterior.

Esta spec é normativa para todas as seguintes.

## Adendo de transição — Spec 08

As specs 00–07 concluíram o MVP contábil inicial:

```text
P_t + u_t -> Lambda_t -> Raz_t -> b_t -> BP/DRE -> Wb_t
```

A partir da Spec 08, o caminho crítico do projeto passa a ser o MVP tributário contrafactual:

```text
base econômico-operacional fixa
    + eta_t
    + {(rho_t^(s), Theta_t^(s))}_s
    -> contexto tributário validado
```

As restrições de fora de escopo acima permanecem como histórico do MVP contábil inicial. Elas não proíbem a abertura posterior da camada tributária, desde que essa camada permaneça paralela ao núcleo contábil e não altere `EVENTOS`, `Lambda_t`, `Raz_t`, `b_t`, BP ou DRE já validados.

A geração sintética associada a `Omega^sim` foi deslocada para fase posterior. Ela não foi removida conceitualmente dos Volumes I–III.
