Attribute VB_Name = "modDemoCsv"
Option Explicit

Public Function CsvEscape(ByVal value As Variant) As String

    Dim text As String
    Dim quote As String

    quote = Chr$(34)

    If IsError(value) Or IsEmpty(value) Or IsNull(value) Then
        text = ""
    Else
        text = CStr(value)
    End If

    text = Replace(text, quote, quote & quote)
    If InStr(1, text, ",", vbBinaryCompare) > 0 Or _
       InStr(1, text, quote, vbBinaryCompare) > 0 Or _
       InStr(1, text, vbCr, vbBinaryCompare) > 0 Or _
       InStr(1, text, vbLf, vbBinaryCompare) > 0 Then
        text = quote & text & quote
    End If

    CsvEscape = text

End Function

Public Sub WriteUtf8CsvFile(ByVal filePath As String, ByVal lines As Variant)

    Dim stream As Object
    Dim i As Long

    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 2
    stream.Charset = "utf-8"
    stream.Open

    For i = LBound(lines) To UBound(lines)
        stream.WriteText CStr(lines(i)) & vbCrLf
    Next i

    stream.SaveToFile filePath, 2
    stream.Close
    Set stream = Nothing

End Sub

Public Function JoinCsvRow(ByVal values As Variant) As String

    Dim parts() As String
    Dim i As Long

    ReDim parts(LBound(values) To UBound(values))
    For i = LBound(values) To UBound(values)
        parts(i) = CsvEscape(values(i))
    Next i

    JoinCsvRow = Join(parts, ",")

End Function

Public Function ReadCsvToArray(ByVal filePath As String) As Variant

    Dim wbCsv As Workbook
    Dim wsCsv As Worksheet
    Dim data As Variant
    Dim oldScreenUpdating As Boolean

    oldScreenUpdating = Application.ScreenUpdating
    On Error GoTo ReadError
    Application.ScreenUpdating = False

    Application.Workbooks.OpenText _
        Filename:=filePath, _
        Origin:=65001, _
        StartRow:=1, _
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
    data = wsCsv.UsedRange.Value2
    wbCsv.Close SaveChanges:=False

    Application.ScreenUpdating = oldScreenUpdating
    ReadCsvToArray = data
    Exit Function

ReadError:
    If Not wbCsv Is Nothing Then
        wbCsv.Close SaveChanges:=False
    End If
    Application.ScreenUpdating = oldScreenUpdating
    Err.Raise vbObjectError + 1200, "ReadCsvToArray", "Falha ao ler " & filePath & ": " & Err.Description

End Function

Public Function IsBlankValue(ByVal value As Variant) As Boolean

    If IsError(value) Then
        IsBlankValue = True
    ElseIf IsEmpty(value) Or IsNull(value) Then
        IsBlankValue = True
    Else
        IsBlankValue = (Trim$(CStr(value)) = "")
    End If

End Function

Public Function FormatDecimalPoint(ByVal value As Variant) As String

    FormatDecimalPoint = Replace(CStr(value), Application.DecimalSeparator, ".")

End Function
