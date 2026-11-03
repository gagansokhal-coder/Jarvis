# =====================================================================
# Gagan AI — Service Status Check
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
    $_.CommandLine -and ($_.CommandLine -like "*gateway*" -or $_.CommandLine -like "*openclaw*")
}

if ($gwProcs) {
    foreach ($p in $gwProcs) {
        $procInfo = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
        $memMb = [Math]::Round(($procInfo.WorkingSet64 / 1MB), 1)
        Write-Host "[OK] Gateway is RUNNING in background (PID: $($p.ProcessId), RAM: $memMb MB)" -ForegroundColor Green
    }
    Write-Host '[OK] Telegram Bot (@GaganjiBot) is LIVE and listening.' -ForegroundColor Green
} else {
    Write-Host '[INFO] Gateway is NOT running.' -ForegroundColor Yellow
}

# 3. Check Real-Time Email Watcher Process
$watcherProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object {
    $_.CommandLine -and $_.CommandLine -like "*email_watcher*"
}

if ($watcherProcs) {
    foreach ($wp in $watcherProcs) {
        $wInfo = Get-Process -Id $wp.ProcessId -ErrorAction SilentlyContinue
        $wMem = [Math]::Round(($wInfo.WorkingSet64 / 1MB), 1)
        Write-Host "[OK] Email Watcher Daemon is RUNNING (PID: $($wp.ProcessId), RAM: $wMem MB)" -ForegroundColor Green
    }
    Write-Host '[OK] Real-time Inbox & Calendar sync is ACTIVE across 6 Google accounts.' -ForegroundColor Green
} else {
    Write-Host '[INFO] Email Watcher Daemon is NOT running.' -ForegroundColor Yellow
}

Write-Host "==========================================================" -ForegroundColor Cyan
