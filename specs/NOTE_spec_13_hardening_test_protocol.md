# Protocolo manual — Spec 13 hardening

**Natureza:** checklist manual complementar aos testes automatizados.  
**Objeto:** Demo Operacional Excel ↔ Python, workbook `.xlsm` de workbench.  
**Status:** pendente até execução real no Excel 2013.

## Preparação

- Importar os módulos VBA nesta ordem:
  1. `modDemoConfig.bas`
  2. `modDemoRuntime.bas`
  3. `modDemoCsv.bas`
  4. `modDemoPayload.bas`
  5. `modDemoResults.bas`
  6. `modDemoMain.bas`
- Remover o módulo monolítico legado `modDemoOperacional`.
- Atribuir o botão da aba `SIMULADOR` a `modDemoMain.Simular`.
- Configurar `_CONFIG.REPO_ROOT`.
- Configurar `_CONFIG.PYTHON_EXE`.
- Confirmar `_CONFIG.INTERFACE_VERSION = spec_13_demo_operacional_v0_1`.

## Casos válidos

- Caso canônico CBS 9%.
- CBS 10%.
- `REGULAR_CREDIT_REALIZATION_FRACTION = 0%`.
- `REGULAR_CREDIT_REALIZATION_FRACTION = 50%`.
- `REGULAR_CREDIT_REALIZATION_FRACTION = 100%`.
- RBT12 alternativo dentro do recorte.
- Operações divididas mantendo os mesmos totais econômicos.
- 100 operações.
- 1.000 operações.
- Valores com centavos.
- Observação com acentos, vírgula, aspas e quebra de linha.
- 20 execuções consecutivas.
- Execuções rápidas no mesmo segundo para verificar `RUN_ID`/runtime único.

## Falhas esperadas

- Venda B2B com `REGIME_CONTRAPARTE = consumidor_final`.
- Venda B2C com `REGIME_CONTRAPARTE = ibs_cbs_regime_regular`.
- Valor negativo.
- Valor zero.
- CBS vazia.
- CBS fora de `(0,1)`.
- Alpha fora de `[0,1]`.
- RBT12 inválido.
- Data fora de H1/2027.
- `PYTHON_EXE` inválido.
- `REPO_ROOT` inválido.
- `INTERFACE_VERSION` incompatível.
- Linha de operação parcialmente preenchida.
- Schema operacional alterado.

## Critérios de cada falha

- Mensagem legível.
- Nenhum resultado válido anterior apagado.
- Timestamp da última simulação válida preservado.
- Status coerente:
  - sem resultado anterior: `SEM SIMULAÇÃO VÁLIDA`;
  - com resultado anterior: `DESATUALIZADO - última tentativa falhou`.
- `Application.StatusBar` restaurada.
- `Application.ScreenUpdating` restaurado.

## Excel 2013

- Abrir o `.xlsm` sem mensagem de reparo.
- Compilar os módulos VBA.
- Executar `SIMULAR`.
- Confirmar que `SIMULADOR` atualiza.
- Confirmar que `MEMORIA` atualiza.
- Confirmar ausência de alerta SYLK nos CSVs temporários.
- Confirmar percentuais com separador decimal correto.
- Confirmar que falhas preservam o último resultado válido.
- Confirmar 20 execuções sem degradação funcional.

## Performance observacional

Registrar tempo aproximado para:

- caso canônico;
- 100 operações;
- 1.000 operações.

Não há SLA rígido nesta versão.
