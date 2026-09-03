Attribute VB_Name = "modDemoResults"
Option Explicit

Public Sub ReadRunStatus( _
    ByVal filePath As String, _
    ByRef runOk As Boolean, _
    ByRef statusCode As Long, _
    ByRef statusMessage As String, _
    ByRef engineVersion As String)

    Dim statusData As Variant
    Dim rawOkText As String

    statusData = ReadCsvToArray(filePath)
    ValidateHeader statusData, Array("RUN_ID", "OK", "STATUS_CODE", "MESSAGE", "ENGINE_SPEC_VERSION")

    rawOkText = LCase$(Trim$(CStr(GetTableValue(statusData, "RUN_ID", CStr(statusData(2, 1)), "OK"))))
    runOk = (rawOkText = "true") Or (rawOkText = "1") Or (rawOkText = "verdadeiro")
    statusCode = CLng(GetTableValue(statusData, "RUN_ID", CStr(statusData(2, 1)), "STATUS_CODE"))
    statusMessage = CStr(GetTableValue(statusData, "RUN_ID", CStr(statusData(2, 1)), "MESSAGE"))
    engineVersion = CStr(GetTableValue(statusData, "RUN_ID", CStr(statusData(2, 1)), "ENGINE_SPEC_VERSION"))

End Sub

Public Sub ValidateOutputFiles(ByVal runtimePath As String)

    Dim files As Variant
    Dim i As Long

    files = Array("run_status.csv", "scenario_results.csv", "comparison_results.csv", "memory_results.csv")
    For i = LBound(files) To UBound(files)
        If Dir(runtimePath & "\" & files(i)) = "" Then
            Err.Raise vbObjectError + 1210, "ValidateOutputFiles", "Arquivo de saída ausente: " & files(i)
        End If
    Next i

End Sub

Public Sub ValidateOutputNamedRanges()

    Dim names As Variant
    Dim i As Long

    names = Array( _
        "outPuroDAS", "outHibridoDAS", "outPuroCBS", "outHibridoCBS", _
        "outPuroIBS", "outHibridoIBS", "outPuroEncargo", "outHibridoEncargo", _
        "outPuroCreditoB2B", "outHibridoCreditoB2B", "outDeltaEncargo", _
        "outCBSBreakEven", "outCBSRateSource", "outLastValidRun", "outStatus")

    For i = LBound(names) To UBound(names)
        ValidateRequiredName CStr(names(i))
    Next i

End Sub

Public Sub ValidateOutputPayload( _
    ByVal scenarioData As Variant, _
    ByVal comparisonData As Variant, _
    ByVal memoryData As Variant, _
    ByVal statusData As Variant)

    ValidateHeader scenarioData, Array("ID_CENARIO", "REGIME_CONSUMO", "RECEITA_MES_CENTS", "RBT12_CENTS", "ALIQUOTA_EFETIVA_SIMPLES", "DAS_TOTAL_CENTS", "DAS_CBS_CENTS", "DAS_IBS_CENTS", "DAS_OUTROS_CENTS", "CBS_REGULAR_RATE_FRACTION", "CBS_RATE_SOURCE", "CBS_DEBITO_REGULAR_CENTS", "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS", "CBS_CREDITO_EMPRESA_MODELADO_CENTS", "CBS_VALOR_LIQUIDO_MODELADO_CENTS", "CBS_SALDO_CREDOR_MODELADO_CENTS", "IBS_REGULAR_RATE_FRACTION", "IBS_DEBITO_REGULAR_CENTS", "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS", "IBS_CREDITO_EMPRESA_MODELADO_CENTS", "IBS_VALOR_LIQUIDO_MODELADO_CENTS", "IBS_SALDO_CREDOR_MODELADO_CENTS", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS", "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS", "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS", "STATUS_RESULTADO", "VERSAO_REGRA")
    ValidateHeader comparisonData, Array("ID_CENARIO_BASE", "ID_CENARIO", "METRICA", "BASELINE_CENTS", "ALTERNATIVO_CENTS", "DELTA_CENTS", "STATUS_BASELINE", "STATUS_ALTERNATIVO")
    ValidateHeader memoryData, Array("SECAO", "CHAVE", "VALOR", "UNIDADE", "STATUS", "FONTE")
    ValidateHeader statusData, Array("RUN_ID", "OK", "STATUS_CODE", "MESSAGE", "ENGINE_SPEC_VERSION")

    RequireTableValue scenarioData, "ID_CENARIO", "SIMPLES_2027_PURO", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"
    RequireTableValue scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS"
    RequireTableValue comparisonData, "METRICA", "ENCARGO_TRIBUTARIO_COMPARAVEL", "DELTA_CENTS"
    RequireTableValue memoryData, "CHAVE", "CBS_BREAK_EVEN", "VALOR"
    RequireTableValue memoryData, "CHAVE", "CBS_RATE_SOURCE", "VALOR"
    ValidateOutputNamedRanges

End Sub

Public Sub ImportSuccessfulRun(ByVal runtimePath As String)

    Dim scenarioData As Variant
    Dim comparisonData As Variant
    Dim memoryData As Variant
    Dim statusData As Variant

    ValidateOutputFiles runtimePath

    scenarioData = ReadCsvToArray(runtimePath & "\scenario_results.csv")
    comparisonData = ReadCsvToArray(runtimePath & "\comparison_results.csv")
    memoryData = ReadCsvToArray(runtimePath & "\memory_results.csv")
    statusData = ReadCsvToArray(runtimePath & "\run_status.csv")

    ValidateOutputPayload scenarioData, comparisonData, memoryData, statusData

    UpdateRawResults scenarioData, comparisonData, memoryData, statusData
    UpdateMemory memoryData
    UpdateSimulator scenarioData, comparisonData, memoryData

End Sub

Public Sub UpdateRawResults( _
    ByVal scenarioData As Variant, _
    ByVal comparisonData As Variant, _
    ByVal memoryData As Variant, _
    ByVal statusData As Variant)

    Dim ws As Worksheet
    Dim nextRow As Long

    Set ws = ThisWorkbook.Worksheets(SHEET_RAW)
    ws.Cells.ClearContents

    nextRow = 1
    nextRow = WriteRawBlock(ws, nextRow, "SCENARIO_RESULTS", scenarioData)
    nextRow = WriteRawBlock(ws, nextRow, "COMPARISON_RESULTS", comparisonData)
    nextRow = WriteRawBlock(ws, nextRow, "MEMORY_RESULTS", memoryData)
    nextRow = WriteRawBlock(ws, nextRow, "RUN_STATUS", statusData)

End Sub

Private Function WriteRawBlock(ByVal ws As Worksheet, ByVal startRow As Long, ByVal label As String, ByVal data As Variant) As Long

    ws.Cells(startRow, 1).Value = label
    WriteArrayToSheet ws, startRow + 1, 1, data
    WriteRawBlock = startRow + UBound(data, 1) + 3

End Function

Public Sub UpdateMemory(ByVal memoryData As Variant)

    Dim ws As Worksheet

    Set ws = ThisWorkbook.Worksheets(SHEET_MEMORIA)
    ws.Range("A3:F1000").ClearContents
    WriteArrayToSheet ws, 3, 1, memoryData
    ws.Columns("A:F").AutoFit

End Sub

Public Sub UpdateSimulator( _
    ByVal scenarioData As Variant, _
    ByVal comparisonData As Variant, _
    ByVal memoryData As Variant)

    Dim puroDas As Variant
    Dim hibridoDas As Variant
    Dim hibridoCBS As Variant
    Dim hibridoIBS As Variant
    Dim puroEncargo As Variant
    Dim hibridoEncargo As Variant
    Dim puroB2BCBS As Variant
    Dim puroB2BIBS As Variant
    Dim hibridoB2BCBS As Variant
    Dim hibridoB2BIBS As Variant
    Dim deltaEncargo As Variant
    Dim breakEven As Variant
    Dim cbsRateSource As Variant

    puroDas = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_PURO", "DAS_TOTAL_CENTS")
    puroEncargo = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_PURO", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS")
    puroB2BCBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_PURO", "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS")
    puroB2BIBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_PURO", "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS")
    hibridoDas = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "DAS_OUTROS_CENTS")
    hibridoCBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "CBS_VALOR_LIQUIDO_MODELADO_CENTS")
    hibridoIBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "IBS_VALOR_LIQUIDO_MODELADO_CENTS")
    hibridoEncargo = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS")
    hibridoB2BCBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS")
    hibridoB2BIBS = GetTableValue(scenarioData, "ID_CENARIO", "SIMPLES_2027_HIBRIDO", "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS")
    deltaEncargo = GetTableValue(comparisonData, "METRICA", "ENCARGO_TRIBUTARIO_COMPARAVEL", "DELTA_CENTS")
    breakEven = GetTableValue(memoryData, "CHAVE", "CBS_BREAK_EVEN", "VALOR")
    cbsRateSource = GetTableValue(memoryData, "CHAVE", "CBS_RATE_SOURCE", "VALOR")

    SetMoneyOutput ThisWorkbook.Names("outPuroDAS").RefersToRange, puroDas
    SetMoneyOutput ThisWorkbook.Names("outHibridoDAS").RefersToRange, hibridoDas
    ThisWorkbook.Names("outPuroCBS").RefersToRange.Value = "n/a"
    SetMoneyOutput ThisWorkbook.Names("outHibridoCBS").RefersToRange, hibridoCBS
    ThisWorkbook.Names("outPuroIBS").RefersToRange.Value = "n/a"
    SetMoneyOutput ThisWorkbook.Names("outHibridoIBS").RefersToRange, hibridoIBS
    SetMoneyOutput ThisWorkbook.Names("outPuroEncargo").RefersToRange, puroEncargo
    SetMoneyOutput ThisWorkbook.Names("outHibridoEncargo").RefersToRange, hibridoEncargo
    SetMoneyOutput ThisWorkbook.Names("outPuroCreditoB2B").RefersToRange, SumCents(puroB2BCBS, puroB2BIBS)
    SetMoneyOutput ThisWorkbook.Names("outHibridoCreditoB2B").RefersToRange, SumCents(hibridoB2BCBS, hibridoB2BIBS)
    SetMoneyOutput ThisWorkbook.Names("outDeltaEncargo").RefersToRange, deltaEncargo
    SetPercentOutput ThisWorkbook.Names("outCBSBreakEven").RefersToRange, breakEven
    ThisWorkbook.Names("outCBSRateSource").RefersToRange.Value = CStr(cbsRateSource)
    ThisWorkbook.Names("outLastValidRun").RefersToRange.Value = Now
    ThisWorkbook.Names("outLastValidRun").RefersToRange.NumberFormat = "dd/mm/yyyy hh:mm:ss"
    ThisWorkbook.Names("outStatus").RefersToRange.Value = "SIMULAÇÃO VÁLIDA"

End Sub

Public Sub MarkResultsStale()

    On Error Resume Next
    If IsBlankValue(ThisWorkbook.Names("outLastValidRun").RefersToRange.Value) Then
        ThisWorkbook.Names("outStatus").RefersToRange.Value = "SEM SIMULAÇÃO VÁLIDA"
    Else
        ThisWorkbook.Names("outStatus").RefersToRange.Value = "DESATUALIZADO - última tentativa falhou"
    End If
    On Error GoTo 0

End Sub

Public Sub WriteArrayToSheet(ByVal ws As Worksheet, ByVal startRow As Long, ByVal startColumn As Long, ByVal data As Variant)

    ws.Cells(startRow, startColumn).Resize(UBound(data, 1), UBound(data, 2)).Value = data

End Sub

Public Function GetTableValue(ByVal data As Variant, ByVal keyColumnName As String, ByVal keyValue As String, ByVal valueColumnName As String) As Variant

    Dim keyCol As Long
    Dim valueCol As Long
    Dim c As Long
    Dim r As Long

    For c = 1 To UBound(data, 2)
        If Trim$(CStr(data(1, c))) = keyColumnName Then keyCol = c
        If Trim$(CStr(data(1, c))) = valueColumnName Then valueCol = c
    Next c

    If keyCol = 0 Then Err.Raise vbObjectError + 1221, "GetTableValue", "Coluna não encontrada: " & keyColumnName
    If valueCol = 0 Then Err.Raise vbObjectError + 1222, "GetTableValue", "Coluna não encontrada: " & valueColumnName

    For r = 2 To UBound(data, 1)
        If Trim$(CStr(data(r, keyCol))) = keyValue Then
            GetTableValue = data(r, valueCol)
            Exit Function
        End If
    Next r

    Err.Raise vbObjectError + 1223, "GetTableValue", "Registro não encontrado: " & keyColumnName & "=" & keyValue

End Function

Public Sub RequireTableValue(ByVal data As Variant, ByVal keyColumnName As String, ByVal keyValue As String, ByVal valueColumnName As String)

    Dim value As Variant

    value = GetTableValue(data, keyColumnName, keyValue, valueColumnName)
    If IsBlankValue(value) Then
        Err.Raise vbObjectError + 1224, "RequireTableValue", "Valor obrigatório ausente: " & valueColumnName
    End If

End Sub

Public Sub ValidateHeader(ByVal data As Variant, ByVal expected As Variant)

    Dim i As Long

    If UBound(data, 2) <> UBound(expected) - LBound(expected) + 1 Then
        Err.Raise vbObjectError + 1225, "ValidateHeader", "Schema de saída com número de colunas inválido."
    End If

    For i = LBound(expected) To UBound(expected)
        If Trim$(CStr(data(1, i - LBound(expected) + 1))) <> CStr(expected(i)) Then
            Err.Raise vbObjectError + 1226, "ValidateHeader", "Schema de saída inválido: " & CStr(expected(i))
        End If
    Next i

End Sub

Public Sub SetMoneyOutput(ByVal target As Range, ByVal centsValue As Variant)

    If IsBlankValue(centsValue) Then
        target.Value = "n/a"
        target.NumberFormat = "General"
    Else
        target.Value = CDbl(centsValue) / 100#
        target.NumberFormat = """R$"" #,##0.00"
    End If

End Sub

Public Sub SetPercentOutput(ByVal target As Range, ByVal fractionValue As Variant)

    If IsBlankValue(fractionValue) Then
        target.Value = "n/a"
        target.NumberFormat = "General"
    Else
        target.Value = CDbl(fractionValue)
        target.NumberFormat = "0.000%"
    End If

End Sub

Public Function SumCents(ByVal value1 As Variant, ByVal value2 As Variant) As Double

    Dim total As Double

    total = 0#
    If Not IsBlankValue(value1) Then total = total + CDbl(value1)
    If Not IsBlankValue(value2) Then total = total + CDbl(value2)
    SumCents = total

End Function
