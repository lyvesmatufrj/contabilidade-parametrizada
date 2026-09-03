# Estado de implementação do projeto

**Repositório:** `lyvesmatufrj/contabilidade-parametrizada`  
**Snapshot de referência:** `main@001a1d0b15a9ed1aa191e5f1bad6934f9ced00cf`  
**Data:** 2026-09-03

Este arquivo registra o estado operacional do projeto e separa explicitamente:

```text
SPEC
    o que foi decidido e contratado
IMPLEMENTAÇÃO
    o que o código efetivamente materializa
EVIDÊNCIA
    testes, auditorias e artefatos que sustentam o estado
WORKBENCH
    protótipos e experimentos ainda fora do source of truth
```

Ele não substitui Volumes, specs, código ou fontes normativas. Serve como índice de reconciliação entre esses objetos.

---

## 1. Precedência

Para objetos internos:

```text
Volumes I–III > Specs > Código
```

Para afirmações jurídicas e parâmetros tributários:

```text
Constituição / EC / LC
> atos normativos infralegais
> documentos técnicos oficiais
> manuais/orientações oficiais
> materiais didáticos oficiais
> interpretação do projeto
```

`FISCAL_PARAM` e `ANALISE_PARAM` permanecem semanticamente distintos.

---

## 2. Estados permitidos

### Estado da spec

- `rascunho`: ainda em exploração;
- `aprovada`: contrato aceito, ainda pode receber correções antes do freeze;
- `congelada`: contrato funcional estabilizado; só reabrir por bug, conflito superior ou mudança explícita de escopo;
- `substituída`: preservada apenas para histórico.

### Estado da implementação

- `não iniciada`;
- `parcial`;
- `implementada`;
- `verificada`: implementada e auditada contra a spec;
- `regressão`: preservada como caso estável de referência.

### Estado do artefato

- `workbench`: provisório, não é source of truth;
- `candidato`;
- `validado`;
- `regressão`.

---

## 3. Snapshot atual

| Spec | Objeto | Estado da spec | Implementação | Evidência atual | Artefato / observação |
|---|---|---|---|---|---|
| 00–05 | núcleo contábil mínimo | congelada | verificada | suíte corrente; invariantes contábeis | base do motor |
| 06–07 | workbook, BP e DRE | congelada | verificada | workbook gerado e testes | `artifacts/contabilidade_parametrizada.xlsx` |
| 08 | interface tributária contrafactual | congelada | verificada | `TaxContext`, validações e schemas em uso | infraestrutura tributária |
| 09 | CBS 2026 regular / NF-e 55 | congelada | regressão | regressão preservada no patch da Spec 12 | caso canônico CBS 2026 |
| 10 | executor contrafactual | congelada | verificada | testes integrados | executor multi-cenário |
| 11 | comparação tributária | congelada | verificada | testes integrados | comparação/relatório |
| 12 | Simples 2027 puro × híbrido | **congelada funcionalmente** | **verificada** | patch `64676ca`; testes focados + regressão + full suite local reportada com `331 passed`; abertura manual no Excel 2013 sem reparo | `artifacts/demo_simples_2027_puro_vs_hibrido.xlsx` |
| 13 | demo operacional Excel ↔ Python | **aprovada** | **implementada** | hardening automatizado da interface Excel ↔ Python; testes Python/VBA estáticos; stress Excel 2013 ainda pendente | .xlsm permanece em workbench |

### Nota sobre a Spec 12

O cabeçalho de `specs/12_simples_2027_puro_hibrido.md` ainda registra `Status: pronta para implementação`. Isso ficou defasado em relação ao estado real do projeto.

Até que o cabeçalho seja reconciliado, este registro documenta a decisão operacional de 2026-09-02:

```text
Spec 12 = implementada, auditada e congelada funcionalmente
```

A correção documental do cabeçalho não deve alterar a semântica da Spec 12.

---

## 4. Baseline técnico atual

Commit de referência:

```text
001a1d0b15a9ed1aa191e5f1bad6934f9ced00cf
update2-spec-13
```

Nesse baseline:

- a admissibilidade B2B/B2C considera `REGIME_ADQUIRENTE`;
- `ANALISE_PARAM` é exigido pela Spec 12 apenas conforme as dependências efetivas;
- CBS analítica permanece separada de parâmetros normativos;
- o cenário híbrido permanece analítico enquanto consumir hipótese analítica de realização de créditos;
- proveniência/vigência corrigidas no fixture Simples 2027;
- abas tabulares vazias não recebem `Table` de uma única linha;
- CBS 2026 permanece regressão;
- Excel 2013 foi validado manualmente após o patch.

## 4.1 Baseline de hardening da Spec 13

Base de início:

```text
001a1d0b15a9ed1aa191e5f1bad6934f9ced00cf
```

Estado após a rodada automatizada:

- Spec 13 aprovada;
- implementação automatizada do hardening implementada quando a suíte passa;
- `.xlsm` permanece como workbench;
- stress manual Excel 2013 pendente;
- a Spec 13 não está congelada/verificada até a conclusão do protocolo manual.

---

## 5. Workbench

Objetos provisórios podem permanecer fora do repositório, inclusive em Google Drive.

Exemplos:

```text
*.xlsm de protótipo
mockups
screenshots
rascunhos de VBA
exemplos de reunião
arquivos temporários de execução
```

Regra:

```text
WORKBENCH != SPEC
WORKBENCH != IMPLEMENTAÇÃO VERIFICADA
```

O protótipo só entra no repositório quando o contrato de interface estiver suficientemente estável para ser testado e preservado.

---

## 6. Próximo marco

O caminho crítico passa a ser:

```text
Spec 13
    ↓
interface operacional mínima
    ↓
Excel .xlsm como frontend
    ↓
VBA como controlador
    ↓
Python existente como motor
    ↓
reunião de validação com usuário profissional
    ↓
backlog baseado em demanda observada
```

Não expandir o domínio tributário antes da validação da Demo Operacional 0.1, salvo blocker jurídico/material do recorte corrente.

---

## 7. Regra de atualização deste arquivo

Atualizar este registro quando ocorrer pelo menos um dos seguintes eventos:

1. aprovação/congelamento/reabertura de uma spec;
2. implementação material de uma spec;
3. auditoria que mude o estado de implementação;
4. novo artefato promovido de workbench para candidato/validado;
5. mudança de baseline/commit de referência;
6. regressão funcional comprovada em objeto congelado.

Atualizações puramente visuais de protótipos de workbench não exigem commit neste arquivo.
