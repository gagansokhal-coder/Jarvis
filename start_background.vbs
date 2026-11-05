Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Launch OpenClaw Gateway on Telegram
cmdGateway = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & currentDir & "\start_gagan_ai.ps1"""
WshShell.Run cmdGateway, 0, False

' 2. Launch Real-time Email & Calendar Watcher Daemon
pythonExe = "python.exe"
watcherScript = currentDir & "\scripts\email_watcher.py"
runSilent = currentDir & "\scripts\run_silent.vbs"
cmdWatcher = "wscript.exe """ & runSilent & """ """ & pythonExe & """ """ & watcherScript & """"
WshShell.Run cmdWatcher, 0, False

' 3. Launch 24/7 Voice Sentinel & Auto-Unlock Daemon
pythonwExe = currentDir & "\venv\Scripts\pythonw.exe"
voiceScript = currentDir & "\voice\conversation_loop.py"
cmdVoice = """" & pythonwExe & """ """ & voiceScript & """"
WshShell.Run cmdVoice, 0, False

Set WshShell = Nothing
Set fso = Nothing
