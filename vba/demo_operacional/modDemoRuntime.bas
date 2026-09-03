Attribute VB_Name = "modDemoRuntime"
Option Explicit

Public Function CreateRunId() As String

    CreateRunId = Format$(Now, "yyyymmdd_hhnnss") & "_" & Format$(CLng(Timer * 1000), "00000000")

End Function

Public Function CreateRuntimeFolder(ByRef runId As String) As String

    Dim basePath As String
    Dim runtimePath As String
    Dim suffix As Long

    basePath = Environ$("TEMP") & "\contabilidade_parametrizada"
    EnsureFolder basePath

    basePath = basePath & "\demo13"
    EnsureFolder basePath

    runtimePath = basePath & "\" & runId
    suffix = 0
    Do While Dir(runtimePath, vbDirectory) <> ""
        suffix = suffix + 1
        runtimePath = basePath & "\" & runId & "_" & Format$(suffix, "000")
    Loop

    If suffix > 0 Then
        runId = runId & "_" & Format$(suffix, "000")
    End If

    MkDir runtimePath
    CreateRuntimeFolder = runtimePath

End Function

Private Sub EnsureFolder(ByVal folderPath As String)

    If Dir(folderPath, vbDirectory) = "" Then
        MkDir folderPath
    End If

End Sub

Public Function QuoteArg(ByVal value As String) As String

    QuoteArg = Chr$(34) & Replace(value, Chr$(34), Chr$(34) & Chr$(34)) & Chr$(34)

End Function

Public Function RunPython(ByVal runtimePath As String) As Long

    Dim repoRoot As String
    Dim pythonExe As String
    Dim entryPoint As String
    Dim command As String
    Dim shell As Object

    repoRoot = GetConfigValue("REPO_ROOT")
    pythonExe = GetConfigValue("PYTHON_EXE")
    entryPoint = repoRoot & "\scripts\run_demo_operacional.py"

    command = QuoteArg(pythonExe) & " " & QuoteArg(entryPoint) & " " & _
              "--input-dir " & QuoteArg(runtimePath) & " " & _
              "--output-dir " & QuoteArg(runtimePath)

    Set shell = CreateObject("WScript.Shell")
    RunPython = shell.Run(command, 0, True)
    Set shell = Nothing

End Function
