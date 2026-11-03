# remove_scheduled_tasks.ps1 - Removes JARVIS routines from Windows Task Scheduler
$tasks = @("JARVIS-Morning-Briefing", "JARVIS-Email-Digest-Morning", "JARVIS-Email-Digest-Evening")
foreach ($t in $tasks) {
    try {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "Removed task: $t"
    } catch {}
}
Write-Host "All JARVIS scheduled tasks removed."

