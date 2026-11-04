# setup_scheduled_tasks.ps1 - Registers Gagan AI routines in Windows Task Scheduler
$ErrorActionPreference = "Stop"

$workspace = "D:\Desktop\gaganAI"
$pythonPath = (Get-Command python.exe).Source
$vbsPath = Join-Path $workspace "scripts\run_silent.vbs"

# Helper VBS to run python silently without flashing command prompt window
$vbsContent = @"
Set objShell = CreateObject("WScript.Shell")
Set args = WScript.Arguments
If args.Count > 0 Then
    cmd = """" & args(0) & """"
    For i = 1 To args.Count - 1
        cmd = cmd & " """ & args(i) & """"
    Next
    objShell.Run cmd, 0, False
End If
"@
[System.IO.File]::WriteAllText($vbsPath, $vbsContent, [System.Text.Encoding]::ASCII)

function Register-GaganTask {
    param (
        [string]$TaskName,
        [string]$DailyTime,
        [string]$RoutineName
    )
    
    $scriptPath = Join-Path $workspace "scripts\run_scheduled_routine.py"
    $actionArg = "`"$vbsPath`" `"$pythonPath`" `"$scriptPath`" `"$RoutineName`""
    
    $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument $actionArg -WorkingDirectory $workspace
    $trigger = New-ScheduledTaskTrigger -Daily -At $DailyTime
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Unregister existing if present
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    } catch {}

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Gagan AI Autonomous Routine: $RoutineName" | Out-Null
    Write-Host "✅ Registered Task: $TaskName (Daily at $DailyTime -> $RoutineName)"
}

Write-Host "Registering Gagan AI Autonomous Routines in Windows Task Scheduler..."
Register-GaganTask -TaskName "Gagan-Morning-Briefing" -DailyTime "07:00" -RoutineName "morning-briefing"
Register-GaganTask -TaskName "Gagan-Email-Digest-Morning" -DailyTime "09:00" -RoutineName "email-digest"
Register-GaganTask -TaskName "Gagan-Email-Digest-Evening" -DailyTime "18:00" -RoutineName "email-digest"

Write-Host "`nAll Gagan AI scheduled routines registered successfully!"

