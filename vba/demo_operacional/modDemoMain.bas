Attribute VB_Name = "modDemoMain"
Option Explicit

Private mIsRunning As Boolean

Public Sub Simular()

    Dim oldScreenUpdating As Boolean
    Dim oldStatusBar As Variant
    Dim runId As String
    Dim runtimePath As String
    Dim exitCode As Long
    Dim runOk As Boolean
    Dim statusCode As Long
    Dim statusMessage As String
    Dim engineVersion As String

    If mIsRunning Then
        MsgBox "Já existe uma simulação em execução.", vbExclamation, "Demo RTC"
        Exit Sub
    End If

    On Error GoTo UnexpectedError

    mIsRunning = True
    oldScreenUpdating = Application.ScreenUpdating
    oldStatusBar = Application.StatusBar
    Application.ScreenUpdating = False

    ValidateWorkbookStructure
    ValidateEnvironment
    ValidatePayload

    runId = CreateRunId()
    runtimePath = CreateRuntimeFolder(runId)

    ExportEntityInput runtimePath & "\entity_input.csv"
    ExportAnalysisInput runtimePath & "\analysis_input.csv"
    ExportOperations runtimePath & "\operations_input.csv"
    ExportRunRequest runtimePath & "\run_request.csv", runId

    Application.StatusBar = "Executando simulação tributária..."
    DoEvents
    exitCode = RunPython(runtimePath)

    If Dir(runtimePath & "\run_status.csv") = "" Then
        MarkResultsStale
        MsgBox "O processo Python terminou sem produzir run_status.csv.", vbCritical, "Simulação não concluída"
        GoTo CleanExit
    End If

    ReadRunStatus runtimePath & "\run_status.csv", runOk, statusCode, statusMessage, engineVersion

    If Not runOk Or statusCode <> 0 Or exitCode <> 0 Then
        MarkResultsStale
        MsgBox "A simulação foi rejeitada pelo motor." & vbCrLf & vbCrLf & _
               "Mensagem:" & vbCrLf & statusMessage & vbCrLf & vbCrLf & _
               "Código: " & statusCode & vbCrLf & _
               "Engine: " & engineVersion, vbExclamation, "Simulação não concluída"
        GoTo CleanExit
    End If

    Application.StatusBar = "Atualizando resultados..."
    DoEvents
    ImportSuccessfulRun runtimePath

    MsgBox "Simulação concluída e resultados atualizados.", vbInformation, "Demo RTC"

CleanExit:
    Application.StatusBar = oldStatusBar
    Application.ScreenUpdating = oldScreenUpdating
    mIsRunning = False
    Exit Sub

UnexpectedError:
    On Error Resume Next
    MarkResultsStale
    Application.StatusBar = oldStatusBar
    Application.ScreenUpdating = oldScreenUpdating
    mIsRunning = False
    MsgBox "Falha operacional:" & vbCrLf & Err.Description, vbCritical, "Demo RTC"
    On Error GoTo 0

End Sub
