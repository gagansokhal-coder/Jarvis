@echo off
echo Stopping Gagan AI background processes...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*conversation_loop*' -or $_.CommandLine -like '*email_watcher*' -or $_.CommandLine -like '*web_voice_call*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo All background services stopped cleanly.
timeout /t 2 > nul
