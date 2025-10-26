' ============================================
'   Silent wrapper for Task Scheduler
'   Runs the batch file without showing a window
' ============================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Build path to the batch file
batchFile = scriptDir & "\RUN_Strategy_Internal.bat"

' Run the batch file hidden (0 = hidden, False = don't wait)
WshShell.Run """" & batchFile & """", 0, False

