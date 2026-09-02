# Nota técnica — Compatibilidade do workbook com Microsoft Excel 2013

**Status:** backlog / correção posterior  
**Prioridade:** média-alta para entrega profissional  
**Afeta:** artefatos `.xlsx` gerados após a Spec 12  
**Não altera:** regras tributárias, resultados fiscais ou arquitetura contrafactual

## Problema observado

Ao abrir:

`artifacts/demo_simples_2027_puro_vs_hibrido.xlsx`

no **Microsoft Excel 2013**, o Excel informa que encontrou conteúdo ilegível e tenta reparar o arquivo.

O log de reparo reportado pelo usuário inclui remoção de:

- `AutoFiltro` em partes `xl/tables/table*.xml`;
- estruturas `Table` associadas.

O mesmo arquivo havia sido validado estruturalmente com `openpyxl` e visualmente com LibreOffice headless, portanto essa validação não foi suficiente para garantir compatibilidade com Excel 2013.

## Hipótese técnica principal

O gerador atual cria uma `openpyxl.worksheet.table.Table` mesmo para abas tabulares sem linhas de dados.

O padrão atual é equivalente a:

```python
table_ref = f"A1:{last_column}{max(ws.max_row, 1)}"
table = Table(displayName=..., ref=table_ref)
ws.add_table(table)
```

Quando a aba contém apenas cabeçalhos, isso pode produzir uma tabela cujo `ref` abrange somente a linha 1, por exemplo:

```text
A1:I1
```

A hipótese é que o Excel 2013 rejeite ou repare esse XML de tabela/autofiltro, embora versões mais recentes do Excel ou LibreOffice possam tolerá-lo.

Essa causa deve ser **confirmada antes da correção definitiva**.

## Correção candidata

Para tabelas sem dados:

```text
DataFrame vazio
    -> escrever cabeçalhos
    -> NÃO criar Excel Table
```

Para tabelas com pelo menos uma linha:

```text
DataFrame não vazio
    -> escrever dados
    -> criar Excel Table normalmente
```

Não inserir linha fictícia apenas para satisfazer a estrutura da tabela.

## Teste de regressão recomendado

Adicionar teste garantindo que nenhum workbook gerado contenha uma `Table` cujo intervalo seja formado apenas pela linha de cabeçalho.

Também preservar testes existentes para:

- ordem e existência das abas;
- tabelas das abas não vazias;
- regeneração;
- valores fiscais;
- ausência de fórmulas de cálculo;
- ausência de VBA.

## Critério adicional de produto

A partir desta ocorrência, considerar explicitamente:

```text
Microsoft Excel 2013
```

como versão mínima de compatibilidade do produto enquanto esse for o ambiente real do usuário.

Validação via LibreOffice não deve ser tratada, isoladamente, como prova de compatibilidade com Excel 2013.

## Critério de aceite da correção

A correção poderá ser considerada concluída quando:

1. o workbook abrir no Excel 2013 sem mensagem de reparo;
2. o log do Excel não remover `AutoFilter`, `Table` ou outro conteúdo;
3. as abas vazias permanecerem semanticamente vazias;
4. as abas não vazias continuarem usando tabelas normalmente;
5. os resultados CBS 2026 e Simples 2027 permanecerem inalterados;
6. os testes focados passarem;
7. a suíte completa for executada uma única vez ao final.

## Observação

Este documento registra um problema de compatibilidade de serialização/apresentação do `.xlsx`.

Não reabrir por causa dele:

- Spec 09;
- Spec 10;
- Spec 11;
- regras da Spec 12;
- auditoria normativa;
- cálculos tributários.

A correção deve permanecer localizada na camada de workbook e respectivos testes, salvo evidência técnica em contrário.
