# =====================================================================
# Gagan AI (JARVIS) — Stop Background Services
# =====================================================================

$WorkspaceRoot = $PSScriptRoot

Write-Host "Stopping Gagan AI Services..." -ForegroundColor Cyan

# 1. Stop OpenClaw gateway node processes
$gwProcs = Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" | Where-Object {
    $_.CommandLine -and ($_.CommandLine -like "*gateway*" -or $_.CommandLine -like "*openclaw*")
}

if ($gwProcs) {
    foreach ($p in $gwProcs) {
        Write-Host "Stopping Gateway PID: $($p.ProcessId)" -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Gateway stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] No running Gateway process found." -ForegroundColor Yellow
}

# 2. Stop Email Watcher python processes
$watcherProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object {
    $_.CommandLine -and $_.CommandLine -like "*email_watcher*"
}

if ($watcherProcs) {
    foreach ($wp in $watcherProcs) {
        Write-Host "Stopping Email Watcher PID: $($wp.ProcessId)" -ForegroundColor Yellow
        Stop-Process -Id $wp.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Email Watcher stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] No running Email Watcher process found." -ForegroundColor Yellow
}

# 3. Clean up any stale lock files
$lock1 = Join-Path $WorkspaceRoot "data\tmp\openclaw\gateway.state.lock"
$lock2 = Join-Path $WorkspaceRoot "data\state\openclaw.sqlite.cron-authority.lock"

if (Test-Path $lock1) { Remove-Item -Path $lock1 -Force -ErrorAction SilentlyContinue }
if (Test-Path $lock2) { Remove-Item -Path $lock2 -Force -ErrorAction SilentlyContinue }

Write-Host "[OK] Locks cleared." -ForegroundColor Green
