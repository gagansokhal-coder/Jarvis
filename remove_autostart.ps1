# =====================================================================
# Gagan AI — Disable Autostart on Windows Login
# =====================================================================

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Gagan AI Assistant.lnk"

if (Test-Path $shortcutPath) {
    Remove-Item -Path $shortcutPath -Force
    Write-Host "[OK] Autostart shortcut removed from Windows Startup." -ForegroundColor Green
} else {
    Write-Host "[INFO] No autostart shortcut found in Windows Startup." -ForegroundColor Yellow
}

