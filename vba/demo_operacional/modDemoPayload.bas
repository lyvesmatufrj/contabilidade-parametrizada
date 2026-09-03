Attribute VB_Name = "modDemoPayload"
Option Explicit

Public Sub ValidatePayload()

    Dim rbt12 As Double
    Dim cbsRate As Double
    Dim creditRealization As Double

    rbt12 = CDbl(ThisWorkbook.Names("inpRBT12").RefersToRange.Value)
    cbsRate = CDbl(ThisWorkbook.Names("inpCBS2027").RefersToRange.Value)
    creditRealization = CDbl(ThisWorkbook.Names("inpCreditRealization").RefersToRange.Value)

    If rbt12 <= 0 Then
        Err.Raise vbObjectError + 1300, "ValidatePayload", "Informe um RBT12 válido."
    End If

    If cbsRate <= 0 Or cbsRate >= 1 Then
        Err.Raise vbObjectError + 1301, "ValidatePayload", "Informe uma hipótese CBS válida."
    End If

    If creditRealization < 0 Or creditRealization > 1 Then
        Err.Raise vbObjectError + 1302, "ValidatePayload", "Informe uma realização de crédito válida."
    End If

    ValidateOperationsTable

End Sub

Private Sub ValidateOperationsTable()

    Dim ws As Worksheet
    Dim tbl As ListObject
    Dim row As ListRow
    Dim blanks As Long
    Dim values As Long

    Set ws = ThisWorkbook.Worksheets(SHEET_OPERACOES)
    Set tbl = ws.ListObjects(TABLE_OPERACOES)

    For Each row In tbl.ListRows
        blanks = CountRequiredBlankCells(row)
        values = CountRequiredValueCells(row)
        If blanks > 0 And values > 0 Then
            Err.Raise vbObjectError + 1310, "ValidateOperationsTable", "Há linha de operação parcialmente preenchida."
        End If
    Next row

End Sub

Private Function CountRequiredBlankCells(ByVal row As ListRow) As Long

    Dim i As Long
    Dim count As Long

    For i = 1 To 5
        If IsBlankValue(row.Range.Cells(1, i).Value) Then
            count = count + 1
        End If
    Next i

    CountRequiredBlankCells = count

End Function

Private Function CountRequiredValueCells(ByVal row As ListRow) As Long

    Dim i As Long
    Dim count As Long

    For i = 1 To 5
        If Not IsBlankValue(row.Range.Cells(1, i).Value) Then
            count = count + 1
        End If
    Next i

    CountRequiredValueCells = count

End Function

Public Sub ExportEntityInput(ByVal filePath As String)

    Dim lines(0 To 1) As String

    lines(0) = JoinCsvRow(Array("CHAVE", "VALOR"))
    lines(1) = JoinCsvRow(Array("RBT12", FormatDecimalPoint(ThisWorkbook.Names("inpRBT12").RefersToRange.Value)))
    WriteUtf8CsvFile filePath, lines

End Sub

Public Sub ExportAnalysisInput(ByVal filePath As String)

    Dim lines(0 To 2) As String

    lines(0) = JoinCsvRow(Array("CHAVE_PARAM", "VALOR"))
    lines(1) = JoinCsvRow(Array("CBS_2027_ANALYSIS_RATE_FRACTION", FormatDecimalPoint(ThisWorkbook.Names("inpCBS2027").RefersToRange.Value)))
    lines(2) = JoinCsvRow(Array("REGULAR_CREDIT_REALIZATION_FRACTION", FormatDecimalPoint(ThisWorkbook.Names("inpCreditRealization").RefersToRange.Value)))
    WriteUtf8CsvFile filePath, lines

End Sub

Public Sub ExportOperations(ByVal filePath As String)

    Dim ws As Worksheet
    Dim tbl As ListObject
    Dim row As ListRow
    Dim lines() As String
    Dim lineCount As Long

    Set ws = ThisWorkbook.Worksheets(SHEET_OPERACOES)
    Set tbl = ws.ListObjects(TABLE_OPERACOES)

    ReDim lines(0 To tbl.ListRows.Count)
    lines(0) = JoinCsvRow(Array("ID_OPERACAO", "DATA", "TIPO_OPERACAO", "VALOR", "REGIME_CONTRAPARTE", "OBSERVACAO"))
    lineCount = 0

    For Each row In tbl.ListRows
        If CountRequiredValueCells(row) = 0 Then
            ' Linha totalmente vazia é ignorada; linha parcial já foi rejeitada.
        Else
            lineCount = lineCount + 1
            lines(lineCount) = JoinCsvRow(Array( _
                row.Range.Cells(1, 1).Value, _
                Format$(row.Range.Cells(1, 2).Value, "yyyy-mm-dd"), _
                row.Range.Cells(1, 3).Value, _
                FormatDecimalPoint(row.Range.Cells(1, 4).Value), _
                row.Range.Cells(1, 5).Value, _
                row.Range.Cells(1, 6).Value _
            ))
        End If
    Next row

    ReDim Preserve lines(0 To lineCount)
    WriteUtf8CsvFile filePath, lines

End Sub

Public Sub ExportRunRequest(ByVal filePath As String, ByVal runId As String)

    Dim lines(0 To 1) As String

    lines(0) = JoinCsvRow(Array("RUN_ID", "INTERFACE_VERSION"))
    lines(1) = JoinCsvRow(Array(runId, GetConfigValue("INTERFACE_VERSION")))
    WriteUtf8CsvFile filePath, lines

End Sub
