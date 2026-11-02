# =====================================================================
# Gagan AI (JARVIS) — Stop Background Service
# =====================================================================

$WorkspaceRoot = $PSScriptRoot

Write-Host "Stopping Gagan AI Gateway..." -ForegroundColor Cyan

# 1. Find OpenClaw gateway node processes
$procs = Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" | Where-Object {
    $_.CommandLine -and ($_.CommandLine -like "*openclaw.mjs*gateway*" -or $_.CommandLine -like "*openclaw*gateway*run*")
}

if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Stopping process PID: $($p.ProcessId)" -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Gagan AI Gateway stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] No running Gagan AI Gateway process found." -ForegroundColor Yellow
}

# 2. Clean up any stale lock files
$lock1 = Join-Path $WorkspaceRoot "data\tmp\openclaw\gateway.state.lock"
$lock2 = Join-Path $WorkspaceRoot "data\state\openclaw.sqlite.cron-authority.lock"

if (Test-Path $lock1) { Remove-Item -Path $lock1 -Force -ErrorAction SilentlyContinue }
if (Test-Path $lock2) { Remove-Item -Path $lock2 -Force -ErrorAction SilentlyContinue }

Write-Host "[OK] Locks cleared." -ForegroundColor Green
