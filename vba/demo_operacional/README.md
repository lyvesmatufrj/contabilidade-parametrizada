# Demo Operacional VBA

Estes módulos são a fonte textual da camada VBA da Spec 13. O arquivo `.xlsm` permanece em workbench nesta rodada; não há injeção automática de macro pelo repositório.

## Encoding

Os arquivos `.bas` devem ser salvos como:

- Windows-1252;
- CRLF;
- sem caminhos locais fixos.

O transporte CSV Excel -> Python e Python -> Excel é sempre UTF-8 com BOM, delimitador vírgula, decimal com ponto e datas ISO `YYYY-MM-DD`.

## Ordem de importação

Importar no VBA Editor:

1. `modDemoConfig.bas`
2. `modDemoRuntime.bas`
3. `modDemoCsv.bas`
4. `modDemoPayload.bas`
5. `modDemoResults.bas`
6. `modDemoMain.bas`

O módulo legado `legacy/modDemoOperacional.bas` deve ser removido do `.xlsm` depois da importação dos módulos novos.

## Botão

Atribuir o botão de execução da aba `SIMULADOR` à macro:

```text
modDemoMain.Simular
```

## Responsabilidades

- `modDemoMain`: orquestração, reentrância, cleanup e mensagem de alto nível.
- `modDemoConfig`: constantes, named ranges e validação estrutural/ambiente.
- `modDemoRuntime`: `RUN_ID`, pasta runtime única, quoting e execução síncrona via `WScript.Shell`.
- `modDemoCsv`: writer UTF-8 BOM com `ADODB.Stream`, escape CSV e reader com `DecimalSeparator:="."`.
- `modDemoPayload`: validação e export dos quatro arquivos de entrada.
- `modDemoResults`: validação atômica dos outputs, atualização de `_RESULTADOS_RAW`, `MEMORIA` e `SIMULADOR`, estado stale.

Nenhum módulo VBA calcula Simples, CBS, IBS, créditos ou break-even. Esses resultados vêm do Python.
