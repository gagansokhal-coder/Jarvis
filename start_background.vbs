Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & currentDir & "\start_gagan_ai.ps1"""
WshShell.Run cmd, 0, False
Set WshShell = Nothing
