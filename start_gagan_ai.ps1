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

# 3. Add npm global path to PATH if needed
$npmPrefix = (npm prefix -g).Trim()
if ($env:PATH -notlike "*$npmPrefix*") {
    $env:PATH = "$npmPrefix;$env:PATH"
}

# 4. Check if Ollama is running
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "[OK] Ollama is active on http://127.0.0.1:11434" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Starting Ollama service..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 5. Validate OpenClaw configuration
Write-Host "[INFO] Validating OpenClaw configuration..." -ForegroundColor Cyan
& openclaw config validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Configuration validation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[OK] Configuration valid!" -ForegroundColor Green

# 6. Show status and launch Gateway
Write-Host "[INFO] Launching OpenClaw Gateway on Telegram..." -ForegroundColor Cyan
& openclaw gateway run
