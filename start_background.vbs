Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Launch Gagan AI Master System (Telegram Gateway, Email Watcher, 24/7 Voice Sentinel)
cmdMaster = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & currentDir & "\start_gagan_ai.ps1"""
WshShell.Run cmdMaster, 0, False

Set WshShell = Nothing
Set fso = Nothing
