# =====================================================================
# Gagan AI (JARVIS) — Enable 24/7 Autostart on Windows Login
# =====================================================================

$WorkspaceRoot = $PSScriptRoot
$vbsPath = Join-Path $WorkspaceRoot "start_background.vbs"
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Gagan AI Assistant.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsPath`""
$Shortcut.WorkingDirectory = $WorkspaceRoot
$Shortcut.Description = "Gagan AI Personal Assistant (24/7 Background Service)"
$Shortcut.Save()

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [OK] Autostart successfully configured!" -ForegroundColor Green
Write-Host " Gagan AI will now automatically start in the background" -ForegroundColor Green
Write-Host " whenever you boot your laptop or log in to Windows." -ForegroundColor Green
Write-Host " Shortcut: $shortcutPath" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

