# =====================================================================
# Gagan AI (JARVIS) — Gateway & Agent Launcher
# =====================================================================

$ErrorActionPreference = "Stop"
$WorkspaceRoot = $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Gagan AI Assistant (Phase 1: Foundation)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Load .env file into current session environment
$envFile = Join-Path $WorkspaceRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $k = $parts[0].Trim()
            $v = $parts[1].Trim()
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
    Write-Host "[OK] Loaded environment variables from .env" -ForegroundColor Green
}

# 2. Set OpenClaw Sandbox Paths inside project
$env:OPENCLAW_CONFIG_PATH = Join-Path $WorkspaceRoot "config\openclaw.json"
$env:OPENCLAW_STATE_DIR = Join-Path $WorkspaceRoot "data"
$env:OPENCLAW_HOME = $WorkspaceRoot
$env:OPENCLAW_WORKSPACE_DIR = Join-Path $WorkspaceRoot "data\workspace"

# OpenClaw stages private SQLite read snapshots in its cache directory.
$cacheDir = Join-Path $WorkspaceRoot "data\cache"
if (-not (Test-Path $cacheDir)) {
    New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
}
$env:XDG_CACHE_HOME = $cacheDir

# Ensure logs directory exists
$logDir = Join-Path $WorkspaceRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# 3. Resolve Node and OpenClaw JS paths
$npmPrefix = (npm prefix -g).Trim()
$openclawMjs = Join-Path $npmPrefix "node_modules\openclaw\openclaw.mjs"

# 4. Check if Ollama is running
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "[OK] Ollama is active on http://127.0.0.1:11434" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Starting Ollama service..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 5. Clean up any stale lock files before starting
$lock1 = Join-Path $WorkspaceRoot "data\tmp\openclaw\gateway.state.lock"
$lock2 = Join-Path $WorkspaceRoot "data\state\openclaw.sqlite.cron-authority.lock"
if (Test-Path $lock1) { Remove-Item -Path $lock1 -Force -ErrorAction SilentlyContinue }
if (Test-Path $lock2) { Remove-Item -Path $lock2 -Force -ErrorAction SilentlyContinue }

# 6. Validate OpenClaw configuration
Write-Host "[INFO] Validating OpenClaw configuration..." -ForegroundColor Cyan
& node $openclawMjs config validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Configuration validation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[OK] Configuration valid!" -ForegroundColor Green

# 7. Launch Gateway with live logging to logs\gateway.log
Write-Host "[INFO] Launching OpenClaw Gateway on Telegram..." -ForegroundColor Cyan
$logFile = Join-Path $logDir "gateway.log"
& node $openclawMjs gateway run *>> $logFile
