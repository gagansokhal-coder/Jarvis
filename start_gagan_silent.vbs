Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
' 0 = Hide window completely, False = Do not wait for return
WshShell.Run "cmd.exe /c start_gagan_background.bat", 0, False
