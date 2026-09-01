# Plano de trabalho das specs — implementação prática do sistema contábil parametrizado

## 1. Objetivo

Este diretório traduz os **Volumes I, II e III da camada de parametrização canônica** em uma sequência de especificações pequenas, verificáveis e orientadas à implementação com Codex.

Os volumes continuam sendo a referência conceitual e notacional. As specs não os reescrevem: elas fixam decisões de engenharia suficientes para produzir rapidamente um primeiro sistema executável.

O alvo inicial é uma **fatia vertical mínima**:

```text
configuração
    -> plano de contas (\mathcal P_t)
    -> eventos (u_t)
    -> lançamentos/partidas (Lambda_t)
    -> Livro Razão (Raz_t)
    -> balancete (b_t)
    -> BP + DRE
    -> workbook .xlsx
```

Critério de sucesso da primeira rodada:

> gerar uma escrituração contabilmente consistente, estruturalmente plausível, auditável em Excel e fácil de modificar.

## 2. Princípios de engenharia

1. **Implementação prática antes de generalidade.** O primeiro alvo é um protótipo reproduzível, não uma plataforma contábil completa.
2. **Vertical slice antes de cobertura.** Primeiro uma empresa, um período e poucos tipos de evento; depois ampliamos o espaço de simulação.
3. **Determinístico antes de estocástico.** Regras manuais e casos fixos devem fechar antes de introduzir distribuições aleatórias.
4. **Validade antes de verossimilhança.** Primeiro impedir estados contabilmente inválidos; depois calibrar se os dados parecem uma empresa real.
5. **Excel como interface; Python como motor.** O workbook é inspecionável e manipulável; cálculos, validações e regeneração pertencem ao motor Python.
6. **Objetos derivados não são editados manualmente.** A regra geral será `editar entradas -> regenerar núcleo -> recalcular saídas`.
7. **Rastreabilidade obrigatória.** IDs, chaves e proveniência devem permitir seguir um valor de uma saída até as partidas e, quando aplicável, até o evento de origem.
8. **Sem sobrearquitetura.** Não introduzir banco de dados, serviços, API, ORM, plugin system ou abstrações extensíveis sem uma necessidade demonstrada por uma spec posterior.

## 3. Fronteira do primeiro MVP

O MVP completo, quando as specs 00–10 estiverem implementadas, deve conter:

- uma empresa comercial simples;
- um plano de contas plausível e hierárquico;
- 10–20 tipos de evento econômico;
- um período simulado;
- escrituração por partidas dobradas;
- Livro Diário e Livro Razão derivados;
- balancete;
- BP e DRE;
- workbook Excel auditável;
- testes de integridade;
- reprodução determinística dada a mesma configuração/semente.

Não fazem parte desse MVP:

- motor tributário completo;
- ECD/ECF completa;
- todos os CPCs;
- DFC e DVA com cobertura completa;
- múltiplos setores ou entidades complexas;
- banco de dados;
- API ou aplicação web;
- ERP sintético completo;
- calibração empírica fina antes de existir corpus real.

## 4. Sequência de specs

| Spec | Arquivo | Questão | Produto esperado |
|---|---|---|---|
| 00 | `00_mvp_scope.md` | O que estamos construindo agora? | fronteira do MVP, stack mínima e definition of done |
| 01 | `01_canonical_model.md` | Como a notação vira nomes e tipos computacionais? | dicionário canônico matemática ↔ Python ↔ Excel |
| 02 | `02_chart_of_accounts.md` | Como representar `\mathcal P_t`? | schema, invariantes e template inicial de plano de contas |
| 03 | `03_events.md` | Como representar `u_t`? | tipos mínimos de eventos e campos necessários |
| 04 | `04_posting_engine.md` | Como `u_t` vira `Lambda_t`? | regras determinísticas de escrituração e partida dobrada |
| 05 | `05_ledger_trial_balance.md` | Como `Lambda_t` vira Razão e balancete? | saldos, movimentos, Diário/Razão e fechamento |
| 06 | `06_excel_workbook.md` | Como o modelo lógico aparece no Excel? | contrato de abas, tabelas nomeadas, editabilidade e geração `.xlsx` |
| 07 | `07_financial_statements.md` | Como contas viram BP/DRE? | mapeamento das contas e demonstrações mínimas |
| 08 | `08_synthetic_generation.md` | Como substituir eventos manuais por geração controlada? | gerador paramétrico com semente explícita |
| 09 | `09_validation_realism.md` | Como testar validade e plausibilidade? | invariantes + critérios de verossimilhança |
| 10 | `10_end_to_end_demo.md` | O sistema funciona de ponta a ponta? | cenário reproduzível e workbook de demonstração |
| 11 | `11_tax_interface.md` | Como conectar depois os Volumes I/II? | contrato da futura interface tributária, sem implementá-la |

A spec 11 deve preservar desde cedo a possibilidade de calcular no futuro

```text
(Raz_t, u_t, rho_t, eta_t, Theta_t^eff) -> Y_t^tax
```

mas **não** deve implementar IBS, CBS, IRPJ, CSLL ou regimes tributários no primeiro ciclo.

## 5. Marcos de desenvolvimento

### Marco A — núcleo contábil mínimo

Specs 00–05.

```text
\mathcal P_t + u_t -> Lambda_t -> Raz_t -> b_t
```

Critério: regras determinísticas, partidas dobradas, integridade referencial e testes passando.

### Marco B — workbook utilizável

Specs 06–07.

Critério: abrir o `.xlsx` e auditar visualmente

```text
evento <-> lançamento <-> partida <-> Razão <-> BP/DRE
```

### Marco C — simulação

Specs 08–10.

```text
Omega^sim -> u_t^(Omega^sim) -> workbook
```

`Omega^sim` é o objeto canônico do Volume III para a configuração computacional da simulação.

### Marco D — tributação

Spec 11 como contrato; implementação tributária em um ciclo separado.

A camada tributária reutilizará `rho_t`, `eta_t`, `zeta_t`, `Theta_t^eff` e os operadores dos Volumes I/II depois que o núcleo contábil estiver validado.

## 6. Estrutura obrigatória de cada spec

Cada arquivo de spec deve seguir, salvo justificativa explícita, esta estrutura:

```text
# Objetivo
# Contexto canônico
# Escopo
# Fora de escopo
# Entradas
# Saídas
# Schema de dados
# Regras / invariantes
# Passos de implementação
# Casos de exemplo
# Testes obrigatórios
# Critérios de aceitação
# Arquivos esperados
# Dependências de outras specs
```

As seções **Fora de escopo**, **Testes obrigatórios** e **Critérios de aceitação** são mandatórias. Elas impedem que um agente amplie o problema sem necessidade.

## 7. Relação com os três volumes canônicos

### Volume I

Preserva:

- `I_t = (t,t+1]`;
- estado `x_t`;
- eventos `u_t` e operação `T_{k,t}`;
- regras `vartheta_t = (theta_t^acct, Theta_t^tax)`;
- operadores contábeis `G^S`;
- camada abstrata `Lambda_t`;
- operadores tributários e notação de demonstrações.

### Volume II

Preserva:

- configuração tributária `rho_t`;
- perfil factual `eta_t`;
- entrada mínima `zeta_t`;
- seletor de regras efetivas `\mathfrak E_{j,t}`;
- proveniência `Prov`;
- pacote de fontes `Q_t`;
- balancete/agregado `b_t`;
- princípio de suficiência funcional da informação.

### Volume III

Abre a camada `Lambda_t` em objetos implementáveis:

- plano de contas `\mathcal P_t`;
- lançamento `lambda_{ell,t}`;
- cabeçalho `H^lambda_{ell,t}`;
- partida `psi_{ell r,t}`;
- vínculo evento–lançamento `V_t`;
- Diário `Dia_t`;
- Razão `Raz_t`;
- balancete `b_t`;
- workbook `Wb_t`;
- configuração computacional `Omega^sim`;
- calibração futura `Gamma`.

## 8. Política de precedência

Se houver conflito:

1. a **semântica matemática** dos Volumes I–III prevalece;
2. as specs fixam a **tradução computacional** dessa semântica;
3. o código deve obedecer às specs;
4. se uma spec contrariar um volume, a spec deve ser corrigida, não o volume reinterpretado silenciosamente.

## 9. Specs desta primeira entrega

Esta primeira rodada contém:

- `00_mvp_scope.md`;
- `01_canonical_model.md`;
- `02_chart_of_accounts.md`.

Esses três arquivos devem ser implementados antes de `03_events.md`, porque congelam a fronteira do projeto, os nomes e tipos básicos e o schema do plano de contas usado por todo o restante.
