Attribute VB_Name = "modDemoOperacional"
Public Sub Simular()

    On Error GoTo UnexpectedError

    Dim rbt12 As Double
    Dim cbsRate As Double
    Dim creditRealization As Double

    Dim runId As String
    Dim runtimePath As String
    Dim exitCode As Long
    
    Dim runOk As Boolean
    Dim statusCode As Long
    Dim statusMessage As String
    Dim engineVersion As String
    
    rbt12 = Range("inpRBT12").value
    cbsRate = Range("inpCBS2027").value
    creditRealization = Range("inpCreditRealization").value

    ' -------------------------
    ' 1. Validação da interface
    ' -------------------------

    If rbt12 <= 0 Then
        MsgBox "Informe um RBT12 válido.", vbExclamation
        Exit Sub
    End If

    If cbsRate <= 0 Or cbsRate >= 1 Then
        MsgBox "Informe uma hipótese CBS válida.", vbExclamation
        Exit Sub
    End If

    If creditRealization < 0 Or creditRealization > 1 Then
        MsgBox "Informe uma realização de crédito válida.", vbExclamation
        Exit Sub
    End If

    ' -------------------------
    ' 2. Ambiente
    ' -------------------------

    ValidateEnvironment

    ' -------------------------
    ' 3. Runtime
    ' -------------------------

    runId = CreateRunId()
    runtimePath = CreateRuntimeFolder(runId)

    ' -------------------------
    ' 4. Exportar payload
    ' -------------------------

    ExportEntityInput runtimePath & "\entity_input.csv"
    ExportAnalysisInput runtimePath & "\analysis_input.csv"
    ExportOperations runtimePath & "\operations_input.csv"
    ExportRunRequest runtimePath & "\run_request.csv", runId

    ' -------------------------
    ' 5. Executar Python
    ' -------------------------

    Application.StatusBar = "Executando simulação tributária..."
    DoEvents

    exitCode = RunPython(runtimePath)

    Application.StatusBar = False

    ' -------------------------
    ' 6. Verificar execução
    ' -------------------------

    If Dir(runtimePath & "\run_status.csv") = "" Then

        MsgBox _
            "O processo Python terminou sem produzir run_status.csv.", _
            vbCritical

        Exit Sub

    End If

    ReadRunStatus _
    runtimePath & "\run_status.csv", _
    runOk, _
    statusCode, _
    statusMessage, _
    engineVersion


    If Not runOk Or statusCode <> 0 Then
    
        MarkResultsStale
    
        MsgBox _
            "A simulação foi rejeitada pelo motor." & vbCrLf & vbCrLf & _
            "Mensagem:" & vbCrLf & _
            statusMessage & vbCrLf & vbCrLf & _
            "Código: " & statusCode & vbCrLf & _
            "Engine: " & engineVersion, _
            vbExclamation, _
            "Simulação não concluída"
    
        Exit Sub
    
    End If

    ' -------------------------
    ' 7. Importar resultados
    ' -------------------------
    
    Application.StatusBar = "Atualizando resultados..."
    DoEvents
    
    ImportSuccessfulRun runtimePath
    
    Application.StatusBar = False
    
    MsgBox _
        "Simulação concluída e resultados atualizados.", _
        vbInformation, _
        "Demo RTC"
    
    Exit Sub


UnexpectedError:

    Application.StatusBar = False

    MarkResultsStale

    MsgBox _
        "Falha operacional:" & vbCrLf & _
        Err.Description, _
        vbCritical

End Sub


Private Function CreateRunId() As String

    CreateRunId = Format(Now, "yyyymmdd_hhnnss")

End Function

Private Function CreateRuntimeFolder(ByVal runId As String) As String

    Dim basePath As String
    Dim runtimePath As String

    basePath = Environ$("TEMP") & "\contabilidade_parametrizada"

    If Dir(basePath, vbDirectory) = "" Then
        MkDir basePath
    End If

    basePath = basePath & "\demo13"

    If Dir(basePath, vbDirectory) = "" Then
        MkDir basePath
    End If

    runtimePath = basePath & "\" & runId

    If Dir(runtimePath, vbDirectory) = "" Then
        MkDir runtimePath
    End If

    CreateRuntimeFolder = runtimePath

End Function

Private Sub ExportEntityInput(ByVal filePath As String)

    Dim fileNum As Integer

    fileNum = FreeFile

    Open filePath For Output As #fileNum

    Print #fileNum, "CHAVE,VALOR"
    Print #fileNum, "RBT12," & CStr(Range("inpRBT12").value)

    Close #fileNum

End Sub

Private Sub ExportAnalysisInput(ByVal filePath As String)

    Dim fileNum As Integer

    fileNum = FreeFile

    Open filePath For Output As #fileNum

    Print #fileNum, "CHAVE_PARAM,VALOR"
    Print #fileNum, _
        "CBS_2027_ANALYSIS_RATE_FRACTION," & _
        Replace(CStr(Range("inpCBS2027").value), ",", ".")

    Print #fileNum, _
        "REGULAR_CREDIT_REALIZATION_FRACTION," & _
        Replace(CStr(Range("inpCreditRealization").value), ",", ".")

    Close #fileNum

End Sub

Private Sub ExportOperations(ByVal filePath As String)

    Dim ws As Worksheet
    Dim tbl As ListObject
    Dim row As ListRow
    Dim fileNum As Integer

    Set ws = ThisWorkbook.Worksheets("OPERACOES")
    Set tbl = ws.ListObjects("tb1Operacoes")

    fileNum = FreeFile

    Open filePath For Output As #fileNum

    Print #fileNum, _
        "ID_OPERACAO,DATA,TIPO_OPERACAO,VALOR,REGIME_CONTRAPARTE,OBSERVACAO"

    For Each row In tbl.ListRows

        Print #fileNum, _
            row.Range.Cells(1, 1).value & "," & _
            Format(row.Range.Cells(1, 2).value, "yyyy-mm-dd") & "," & _
            row.Range.Cells(1, 3).value & "," & _
            Replace(CStr(row.Range.Cells(1, 4).value), ",", ".") & "," & _
            row.Range.Cells(1, 5).value & "," & _
            row.Range.Cells(1, 6).value

    Next row

    Close #fileNum

End Sub

Private Sub ExportRunRequest(ByVal filePath As String, ByVal runId As String)

    Dim fileNum As Integer
    Dim interfaceVersion As String

    interfaceVersion = GetConfigValue("INTERFACE_VERSION")

    fileNum = FreeFile

    Open filePath For Output As #fileNum

    Print #fileNum, "RUN_ID,INTERFACE_VERSION"
    Print #fileNum, runId & "," & interfaceVersion

    Close #fileNum

End Sub

Private Function GetConfigValue(ByVal configKey As String) As String

    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long

    Set ws = ThisWorkbook.Worksheets("_CONFIG")

    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).row

    For i = 2 To lastRow

        If Trim$(CStr(ws.Cells(i, 1).value)) = configKey Then

            GetConfigValue = Trim$(CStr(ws.Cells(i, 2).value))
            Exit Function

        End If

    Next i

    Err.Raise vbObjectError + 1000, _
              "GetConfigValue", _
              "Configuração ausente: " & configKey

End Function

Private Sub ValidateEnvironment()

    Dim repoRoot As String
    Dim pythonExe As String
    Dim entryPoint As String

    repoRoot = GetConfigValue("REPO_ROOT")
    pythonExe = GetConfigValue("PYTHON_EXE")
    entryPoint = repoRoot & "\scripts\run_demo_operacional.py"

    If Dir(repoRoot, vbDirectory) = "" Then
        Err.Raise vbObjectError + 1001, _
                  "ValidateEnvironment", _
                  "REPO_ROOT não encontrado: " & repoRoot
    End If

    If Dir(pythonExe) = "" Then
        Err.Raise vbObjectError + 1002, _
                  "ValidateEnvironment", _
                  "Python não encontrado: " & pythonExe
    End If

    If Dir(entryPoint) = "" Then
        Err.Raise vbObjectError + 1003, _
                  "ValidateEnvironment", _
                  "Entrypoint Python não encontrado: " & entryPoint
    End If

End Sub

Private Function QuoteArg(ByVal value As String) As String

    QuoteArg = Chr$(34) & value & Chr$(34)

End Function

Private Function RunPython(ByVal runtimePath As String) As Long

    Dim repoRoot As String
    Dim pythonExe As String
    Dim entryPoint As String

    Dim command As String
    Dim shell As Object

    repoRoot = GetConfigValue("REPO_ROOT")
    pythonExe = GetConfigValue("PYTHON_EXE")
    entryPoint = repoRoot & "\scripts\run_demo_operacional.py"

    command = _
        QuoteArg(pythonExe) & " " & _
        QuoteArg(entryPoint) & " " & _
        "--input-dir " & QuoteArg(runtimePath) & " " & _
        "--output-dir " & QuoteArg(runtimePath)

    Set shell = CreateObject("WScript.Shell")

    RunPython = shell.Run(command, 0, True)

    Set shell = Nothing

End Function

Private Sub ReadRunStatus( _
    ByVal filePath As String, _
    ByRef runOk As Boolean, _
    ByRef statusCode As Long, _
    ByRef statusMessage As String, _
    ByRef engineVersion As String)

    Dim wbCsv As Workbook
    Dim wsCsv As Worksheet
    Dim rawOk As Variant
    Dim rawOkText As String
    Dim oldScreenUpdating As Boolean

    oldScreenUpdating = Application.ScreenUpdating

    On Error GoTo ReadError

    Application.ScreenUpdating = False

    Workbooks.OpenText _
        Filename:=filePath, _
        Origin:=65001, _
        startRow:=1, _
        DataType:=xlDelimited, _
        TextQualifier:=xlTextQualifierDoubleQuote, _
        ConsecutiveDelimiter:=False, _
        Tab:=False, _
        Semicolon:=False, _
        Comma:=True, _
        Space:=False, _
        Other:=False, _
        DecimalSeparator:=".", _
        ThousandsSeparator:=",", _
        Local:=False

    Set wbCsv = ActiveWorkbook
    Set wsCsv = wbCsv.Worksheets(1)

    rawOk = wsCsv.Cells(2, 2).value

    If VarType(rawOk) = vbBoolean Then

        runOk = CBool(rawOk)

    Else

        rawOkText = LCase$(Trim$(CStr(rawOk)))

        runOk = _
            (rawOkText = "true") Or _
            (rawOkText = "1") Or _
            (rawOkText = "verdadeiro")

    End If

    statusCode = CLng(wsCsv.Cells(2, 3).value)
    statusMessage = CStr(wsCsv.Cells(2, 4).value)
    engineVersion = CStr(wsCsv.Cells(2, 5).value)

    wbCsv.Close SaveChanges:=False

    Application.ScreenUpdating = oldScreenUpdating

    Exit Sub


ReadError:

    If Not wbCsv Is Nothing Then
        wbCsv.Close SaveChanges:=False
    End If

    Application.ScreenUpdating = oldScreenUpdating

    Err.Raise vbObjectError + 1100, _
              "ReadRunStatus", _
              "Não foi possível ler run_status.csv: " & Err.Description

End Sub

Private Function ReadCsvToArray(ByVal filePath As String) As Variant

    Dim wbCsv As Workbook
    Dim wsCsv As Worksheet
    Dim data As Variant
    Dim oldScreenUpdating As Boolean

    oldScreenUpdating = Application.ScreenUpdating

    On Error GoTo ReadError

    Application.ScreenUpdating = False

    Workbooks.OpenText _
        Filename:=filePath, _
        Origin:=65001, _
        startRow:=1, _
        DataType:=xlDelimited, _
        TextQualifier:=xlTextQualifierDoubleQuote, _
        ConsecutiveDelimiter:=False, _
        Tab:=False, _
        Semicolon:=False, _
        Comma:=True, _
        Space:=False, _
        Other:=False, _
        DecimalSeparator:=".", _
        ThousandsSeparator:=",", _
        Local:=False

    Set wbCsv = ActiveWorkbook
    Set wsCsv = wbCsv.Worksheets(1)

    data = wsCsv.UsedRange.value2

    wbCsv.Close SaveChanges:=False

    Application.ScreenUpdating = oldScreenUpdating

    ReadCsvToArray = data

    Exit Function


ReadError:

    If Not wbCsv Is Nothing Then
        wbCsv.Close SaveChanges:=False
    End If

    Application.ScreenUpdating = oldScreenUpdating

    Err.Raise vbObjectError + 1200, _
              "ReadCsvToArray", _
              "Falha ao ler " & filePath & ": " & Err.Description

End Function

Private Sub WriteArrayToSheet( _
    ByVal ws As Worksheet, _
    ByVal startRow As Long, _
    ByVal startColumn As Long, _
    ByVal data As Variant)

    ws.Cells(startRow, startColumn) _
        .Resize(UBound(data, 1), UBound(data, 2)) _
        .value = data

End Sub

Private Function GetTableValue( _
    ByVal data As Variant, _
    ByVal keyColumnName As String, _
    ByVal keyValue As String, _
    ByVal valueColumnName As String) As Variant

    Dim keyCol As Long
    Dim valueCol As Long
    Dim c As Long
    Dim r As Long

    keyCol = 0
    valueCol = 0

    For c = 1 To UBound(data, 2)

        If Trim$(CStr(data(1, c))) = keyColumnName Then
            keyCol = c
        End If

        If Trim$(CStr(data(1, c))) = valueColumnName Then
            valueCol = c
        End If

    Next c

    If keyCol = 0 Then
        Err.Raise vbObjectError + 1201, _
                  "GetTableValue", _
                  "Coluna não encontrada: " & keyColumnName
    End If

    If valueCol = 0 Then
        Err.Raise vbObjectError + 1202, _
                  "GetTableValue", _
                  "Coluna não encontrada: " & valueColumnName
    End If

    For r = 2 To UBound(data, 1)

        If Trim$(CStr(data(r, keyCol))) = keyValue Then

            GetTableValue = data(r, valueCol)
            Exit Function

        End If

    Next r

    Err.Raise vbObjectError + 1203, _
              "GetTableValue", _
              "Registro não encontrado: " & _
              keyColumnName & "=" & keyValue

End Function

Private Function IsBlankValue(ByVal value As Variant) As Boolean

    If IsError(value) Then
        IsBlankValue = True
    ElseIf IsEmpty(value) Or IsNull(value) Then
        IsBlankValue = True
    Else
        IsBlankValue = (Trim$(CStr(value)) = "")
    End If

End Function

Private Sub SetMoneyOutput(ByVal target As Range, ByVal centsValue As Variant)

    If IsBlankValue(centsValue) Then

        target.value = "—"
        target.NumberFormat = "General"

    Else

        target.value = CDbl(centsValue) / 100#
        target.NumberFormat = """R$"" #,##0.00"

    End If

End Sub

Private Sub SetPercentOutput(ByVal target As Range, ByVal fractionValue As Variant)

    If IsBlankValue(fractionValue) Then

        target.value = "—"
        target.NumberFormat = "General"

    Else

        target.value = CDbl(fractionValue)
        target.NumberFormat = "0.000%"

    End If

End Sub

Private Function SumCents( _
    ByVal value1 As Variant, _
    ByVal value2 As Variant) As Double

    Dim total As Double

    total = 0#

    If Not IsBlankValue(value1) Then
        total = total + CDbl(value1)
    End If

    If Not IsBlankValue(value2) Then
        total = total + CDbl(value2)
    End If

    SumCents = total

End Function

Private Sub ValidateOutputFiles(ByVal runtimePath As String)

    Dim files As Variant
    Dim i As Long

    files = Array( _
        "run_status.csv", _
        "scenario_results.csv", _
        "comparison_results.csv", _
        "memory_results.csv" _
    )

    For i = LBound(files) To UBound(files)

        If Dir(runtimePath & "\" & files(i)) = "" Then

            Err.Raise vbObjectError + 1210, _
                      "ValidateOutputFiles", _
                      "Arquivo de saída ausente: " & files(i)

        End If

    Next i

End Sub

Private Sub ValidateOutputNamedRanges()

    Dim names As Variant
    Dim i As Long
    Dim testRange As Range

    names = Array( _
        "outPuroDAS", _
        "outHibridoDAS", _
        "outPuroCBS", _
        "outHibridoCBS", _
        "outPuroIBS", _
        "outHibridoIBS", _
        "outPuroEncargo", _
        "outHibridoEncargo", _
        "outPuroCreditoB2B", _
        "outHibridoCreditoB2B", _
        "outDeltaEncargo", _
        "outCBSBreakEven", _
        "outCBSRateSource", _
        "outLastValidRun", _
        "outStatus" _
    )

    On Error GoTo MissingName

    For i = LBound(names) To UBound(names)

        Set testRange = _
            ThisWorkbook.Worksheets("SIMULADOR").Range(CStr(names(i)))

    Next i

    Exit Sub


MissingName:

    Err.Raise vbObjectError + 1211, _
              "ValidateOutputNamedRanges", _
              "Nome de saída ausente no SIMULADOR: " & names(i)

End Sub

Private Sub UpdateRawResults( _
    ByVal scenarioData As Variant, _
    ByVal comparisonData As Variant, _
    ByVal statusData As Variant)

    Dim ws As Worksheet

    Set ws = ThisWorkbook.Worksheets("_RESULTADOS_RAW")

    ws.Cells.ClearContents

    ws.Range("A1").value = "SCENARIO_RESULTS"
    WriteArrayToSheet ws, 2, 1, scenarioData

    ws.Range("A20").value = "COMPARISON_RESULTS"
    WriteArrayToSheet ws, 21, 1, comparisonData

    ws.Range("A40").value = "RUN_STATUS"
    WriteArrayToSheet ws, 41, 1, statusData

End Sub

Private Sub UpdateMemory(ByVal memoryData As Variant)

    Dim ws As Worksheet

    Set ws = ThisWorkbook.Worksheets("MEMORIA")

    ws.Range("A3:F1000").ClearContents

    WriteArrayToSheet ws, 3, 1, memoryData

    ws.Columns("A:F").AutoFit

End Sub

Private Sub UpdateSimulator( _
    ByVal scenarioData As Variant, _
    ByVal comparisonData As Variant, _
    ByVal memoryData As Variant)

    Dim ws As Worksheet

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

    Set ws = ThisWorkbook.Worksheets("SIMULADOR")

    ' Simples puro
    puroDas = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_PURO", _
        "DAS_TOTAL_CENTS")

    puroEncargo = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_PURO", _
        "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS")

    puroB2BCBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_PURO", _
        "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS")

    puroB2BIBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_PURO", _
        "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS")

    ' Simples híbrido
    hibridoDas = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "DAS_OUTROS_CENTS")

    hibridoCBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "CBS_VALOR_LIQUIDO_MODELADO_CENTS")

    hibridoIBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "IBS_VALOR_LIQUIDO_MODELADO_CENTS")

    hibridoEncargo = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS")

    hibridoB2BCBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS")

    hibridoB2BIBS = GetTableValue( _
        scenarioData, _
        "ID_CENARIO", _
        "SIMPLES_2027_HIBRIDO", _
        "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS")

    ' Comparação
    deltaEncargo = GetTableValue( _
        comparisonData, _
        "METRICA", _
        "ENCARGO_TRIBUTARIO_COMPARAVEL", _
        "DELTA_CENTS")

    ' Memória
    breakEven = GetTableValue( _
        memoryData, _
        "CHAVE", _
        "CBS_BREAK_EVEN", _
        "VALOR")

    cbsRateSource = GetTableValue( _
        memoryData, _
        "CHAVE", _
        "CBS_RATE_SOURCE", _
        "VALOR")

    ' Renderização
    SetMoneyOutput ws.Range("outPuroDAS"), puroDas
    SetMoneyOutput ws.Range("outHibridoDAS"), hibridoDas

    ws.Range("outPuroCBS").value = "—"
    SetMoneyOutput ws.Range("outHibridoCBS"), hibridoCBS

    ws.Range("outPuroIBS").value = "—"
    SetMoneyOutput ws.Range("outHibridoIBS"), hibridoIBS

    SetMoneyOutput ws.Range("outPuroEncargo"), puroEncargo
    SetMoneyOutput ws.Range("outHibridoEncargo"), hibridoEncargo

    SetMoneyOutput _
        ws.Range("outPuroCreditoB2B"), _
        SumCents(puroB2BCBS, puroB2BIBS)

    SetMoneyOutput _
        ws.Range("outHibridoCreditoB2B"), _
        SumCents(hibridoB2BCBS, hibridoB2BIBS)

    SetMoneyOutput ws.Range("outDeltaEncargo"), deltaEncargo

    SetPercentOutput ws.Range("outCBSBreakEven"), breakEven

    ws.Range("outCBSRateSource").value = CStr(cbsRateSource)

    ws.Range("outLastValidRun").value = Now
    ws.Range("outLastValidRun").NumberFormat = "dd/mm/yyyy hh:mm:ss"

    ws.Range("outStatus").value = "SIMULAÇÃO VÁLIDA"

End Sub

Private Sub ImportSuccessfulRun(ByVal runtimePath As String)

    Dim scenarioData As Variant
    Dim comparisonData As Variant
    Dim memoryData As Variant
    Dim statusData As Variant

    ' Nenhum resultado anterior é alterado antes destas validações.
    ValidateOutputFiles runtimePath
    ValidateOutputNamedRanges

    ' Primeiro carregamos tudo em memória.
    scenarioData = _
        ReadCsvToArray(runtimePath & "\scenario_results.csv")

    comparisonData = _
        ReadCsvToArray(runtimePath & "\comparison_results.csv")

    memoryData = _
        ReadCsvToArray(runtimePath & "\memory_results.csv")

    statusData = _
        ReadCsvToArray(runtimePath & "\run_status.csv")

    ' Só agora alteramos o workbook.
    UpdateRawResults scenarioData, comparisonData, statusData
    UpdateMemory memoryData
    UpdateSimulator scenarioData, comparisonData, memoryData

End Sub

Private Sub MarkResultsStale()

    On Error Resume Next

    ThisWorkbook.Worksheets("SIMULADOR") _
        .Range("outStatus").value = _
        "DESATUALIZADO — última tentativa falhou"

    On Error GoTo 0

End Sub

