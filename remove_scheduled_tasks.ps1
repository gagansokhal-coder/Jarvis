# remove_scheduled_tasks.ps1 - Removes Gagan AI routines from Windows Task Scheduler
$tasks = @("Gagan-Morning-Briefing", "Gagan-Email-Digest-Morning", "Gagan-Email-Digest-Evening")
foreach ($t in $tasks) {
    try {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "Removed task: $t"
    } catch {}
}
Write-Host "All Gagan AI scheduled tasks removed."

