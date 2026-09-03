Attribute VB_Name = "modDemoConfig"
Option Explicit

Public Const DEMO_INTERFACE_VERSION As String = "spec_13_demo_operacional_v0_1"
Public Const SHEET_SIMULADOR As String = "SIMULADOR"
Public Const SHEET_OPERACOES As String = "OPERACOES"
Public Const SHEET_MEMORIA As String = "MEMORIA"
Public Const SHEET_CONFIG As String = "_CONFIG"
Public Const SHEET_RAW As String = "_RESULTADOS_RAW"
Public Const TABLE_OPERACOES As String = "tb1Operacoes"

Public Function GetConfigValue(ByVal configKey As String) As String

    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long

    Set ws = ThisWorkbook.Worksheets(SHEET_CONFIG)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row

    For i = 2 To lastRow
        If Trim$(CStr(ws.Cells(i, 1).Value)) = configKey Then
            GetConfigValue = Trim$(CStr(ws.Cells(i, 2).Value))
            Exit Function
        End If
    Next i

    Err.Raise vbObjectError + 1000, "GetConfigValue", "Configuração ausente: " & configKey

End Function

Public Sub ValidateEnvironment()

    Dim repoRoot As String
    Dim pythonExe As String
    Dim entryPoint As String

    repoRoot = GetConfigValue("REPO_ROOT")
    pythonExe = GetConfigValue("PYTHON_EXE")
    entryPoint = repoRoot & "\scripts\run_demo_operacional.py"

    If Dir(repoRoot, vbDirectory) = "" Then
        Err.Raise vbObjectError + 1001, "ValidateEnvironment", "REPO_ROOT não encontrado: " & repoRoot
    End If

    If Dir(pythonExe) = "" Then
        Err.Raise vbObjectError + 1002, "ValidateEnvironment", "Python não encontrado: " & pythonExe
    End If

    If Dir(entryPoint) = "" Then
        Err.Raise vbObjectError + 1003, "ValidateEnvironment", "Entrypoint Python não encontrado: " & entryPoint
    End If

    If GetConfigValue("INTERFACE_VERSION") <> DEMO_INTERFACE_VERSION Then
        Err.Raise vbObjectError + 1004, "ValidateEnvironment", "INTERFACE_VERSION incompatível."
    End If

End Sub

Public Sub ValidateWorkbookStructure()

    Dim ws As Worksheet
    Dim tbl As ListObject

    Set ws = ThisWorkbook.Worksheets(SHEET_OPERACOES)
    Set tbl = ws.ListObjects(TABLE_OPERACOES)

    ValidateRequiredName "inpRBT12"
    ValidateRequiredName "inpCBS2027"
    ValidateRequiredName "inpCreditRealization"
    ValidateOutputNamedRanges

End Sub

Public Sub ValidateRequiredName(ByVal rangeName As String)

    Dim testRange As Range

    On Error GoTo MissingName
    Set testRange = ThisWorkbook.Names(rangeName).RefersToRange
    Exit Sub

MissingName:
    Err.Raise vbObjectError + 1010, "ValidateRequiredName", "Named range ausente: " & rangeName

End Sub
