# =====================================================================
# Gagan AI — Gateway & Agent Launcher
# =====================================================================

$WorkspaceRoot = $PSScriptRoot

$logDir = Join-Path $WorkspaceRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = Join-Path $logDir "gateway.log"

function Log-Message($msg, $color="Cyan") {
    $time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$time] $msg"
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
}

Log-Message "=========================================================="
Log-Message " Starting Gagan AI Assistant (Phase 1: Foundation)"
Log-Message "=========================================================="

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
    Log-Message "[OK] Loaded environment variables from .env" "Green"
}

# 2. Set OpenClaw Sandbox Paths inside project
$env:OPENCLAW_CONFIG_PATH = Join-Path $WorkspaceRoot "config\openclaw.json"
$env:OPENCLAW_STATE_DIR = Join-Path $WorkspaceRoot "data"
$env:OPENCLAW_HOME = $WorkspaceRoot
$env:OPENCLAW_WORKSPACE_DIR = Join-Path $WorkspaceRoot "data\workspace"

$cacheDir = Join-Path $WorkspaceRoot "data\cache"
if (-not (Test-Path $cacheDir)) {
    New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
}
$env:XDG_CACHE_HOME = $cacheDir

# 3. Resolve Node and OpenClaw JS paths
$nodeExe = "node"
$defaultNode = "C:\Program Files\nodejs\node.exe"
if (Test-Path $defaultNode) { $nodeExe = $defaultNode }

$openclawMjs = "C:\Users\gaganrajput\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs"
if (-not (Test-Path $openclawMjs)) {
    try {
        $npmPrefix = (npm prefix -g).Trim()
        $openclawMjs = Join-Path $npmPrefix "node_modules\openclaw\openclaw.mjs"
    } catch {}
}

# Add node and npm to PATH if needed
$nodeDir = Split-Path $nodeExe
if ($env:PATH -notlike "*$nodeDir*") { $env:PATH = "$nodeDir;$env:PATH" }
$npmBin = "C:\Users\gaganrajput\AppData\Roaming\npm"
if ($env:PATH -notlike "*$npmBin*") { $env:PATH = "$npmBin;$env:PATH" }

# 4. Check if Ollama is running
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Log-Message "[OK] Ollama is active on http://127.0.0.1:11434" "Green"
} catch {
    Log-Message "[INFO] Starting Ollama service..." "Yellow"
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 5. Clean up any stale lock files before starting
$lock1 = Join-Path $WorkspaceRoot "data\tmp\openclaw\gateway.state.lock"
$lock2 = Join-Path $WorkspaceRoot "data\state\openclaw.sqlite.cron-authority.lock"
if (Test-Path $lock1) { Remove-Item -Path $lock1 -Force -ErrorAction SilentlyContinue }
if (Test-Path $lock2) { Remove-Item -Path $lock2 -Force -ErrorAction SilentlyContinue }

# 6. Validate OpenClaw configuration
Log-Message "[INFO] Validating OpenClaw configuration..."
& $nodeExe $openclawMjs config validate 2>&1 | Out-Null
Log-Message "[OK] Configuration valid!" "Green"

# 7. Start Real-time Email & Calendar Watcher Daemon if not already running
$existingWatcher = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*email_watcher*" }
if (-not $existingWatcher) {
    Log-Message "[INFO] Starting Real-time Email & Calendar Watcher Daemon..." "Cyan"
    $pythonPath = (Get-Command python.exe).Source
    $watcherScript = Join-Path $WorkspaceRoot "scripts\email_watcher.py"
    Start-Process -FilePath $pythonPath -ArgumentList $watcherScript -WindowStyle Hidden
    Log-Message "[OK] Real-time Email Watcher started in background!" "Green"
}

# 8. Launch Gateway with live output logging
Log-Message "[INFO] Launching OpenClaw Gateway on Telegram..."
& $nodeExe $openclawMjs gateway run *>> $logFile
