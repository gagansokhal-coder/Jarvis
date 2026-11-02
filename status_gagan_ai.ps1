# =====================================================================
# Gagan AI (JARVIS) — Service Status Check
# =====================================================================

$WorkspaceRoot = $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Gagan AI Assistant -- Status Check" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Ollama
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Ollama is RUNNING on http://127.0.0.1:11434" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Ollama is NOT running!" -ForegroundColor Red
}

# 2. Check Gateway Process
$gwProcs = Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" | Where-Object {
    $_.CommandLine -and ($_.CommandLine -like "*openclaw.mjs*gateway*" -or $_.CommandLine -like "*openclaw*gateway*run*")
}

if ($gwProcs) {
    foreach ($p in $gwProcs) {
        $procInfo = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
        $memMb = [Math]::Round(($procInfo.WorkingSet64 / 1MB), 1)
        Write-Host "[OK] Gateway is RUNNING in background (PID: $($p.ProcessId), RAM: $memMb MB)" -ForegroundColor Green
    }
    Write-Host '[OK] Telegram Bot (@GaganjiBot) is LIVE and listening.' -ForegroundColor Green
} else {
    Write-Host '[INFO] Gateway is NOT running. Run .\start_gagan_ai.bat to start in background.' -ForegroundColor Yellow
}
Write-Host "==========================================================" -ForegroundColor Cyan
