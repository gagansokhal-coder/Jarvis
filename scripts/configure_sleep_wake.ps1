# configure_sleep_wake.ps1 - Configures Windows 11 Sleep and Network Wake for Gagan AI
# Run in PowerShell (Administrator recommended for device driver power settings)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Gagan AI - Sleep & Network Wake Configurator" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Enable Wake Timers (allows scheduled tasks and background routines to wake laptop)
Write-Host "[1/4] Enabling Wake Timers on AC Power..." -ForegroundColor Yellow
powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /setdcvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 1

# 2. Keep Network Connected during Standby (Modern Standby S0ix)
Write-Host "[2/4] Enabling Network Connectivity in Standby (Wi-Fi + Ethernet)..." -ForegroundColor Yellow
try {
    # GUID for Standby Connectivity
    powercfg /setacvalueindex SCHEME_CURRENT SUB_NONE CONNECTIVITYINSTANDBY 1
    powercfg /setdcvalueindex SCHEME_CURRENT SUB_NONE CONNECTIVITYINSTANDBY 1
} catch {}

# 3. Apply active power scheme
powercfg /setactive SCHEME_CURRENT
Write-Host "[OK] Power scheme updated with connected standby enabled!" -ForegroundColor Green

# 4. Display Network Adapters and Wake Status
Write-Host "`n[3/4] Detecting Network Hardware for Wake-on-LAN / WoWLAN..." -ForegroundColor Yellow
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -or $_.Name -match "WiFi|Ethernet" }

foreach ($a in $adapters) {
    Write-Host "  • Adapter: $($a.Name) ($($a.InterfaceDescription))" -ForegroundColor Cyan
    Write-Host "    MAC Address: $($a.MacAddress)" -ForegroundColor White
    Write-Host "    Status:      $($a.Status)" -ForegroundColor Gray
}

Write-Host "`n[4/4] Hardware Instructions to Enable Wake in Device Manager:" -ForegroundColor Yellow
Write-Host "  1. Press Win + X -> Click 'Device Manager'" -ForegroundColor White
Write-Host "  2. Expand 'Network adapters'" -ForegroundColor White
Write-Host "  3. Right-click 'Intel(R) Wi-Fi 6 AX201' -> Properties -> 'Power Management'" -ForegroundColor White
Write-Host "     -> Check: 'Allow this device to wake the computer'" -ForegroundColor Green
Write-Host "     -> Check: 'Only allow a magic packet to wake the computer'" -ForegroundColor Green
Write-Host "  4. Right-click 'Intel(R) Ethernet Connection I219-LM' -> Properties -> 'Power Management'" -ForegroundColor White
Write-Host "     -> Check: 'Allow this device to wake the computer'" -ForegroundColor Green
Write-Host "     -> Check: 'Only allow a magic packet to wake the computer'" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "✅ Sleep & Wake configuration completed!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

