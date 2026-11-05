@echo off
cd /d "%~dp0"

:: 1. Clean stale locks
del /q /f data\agents\gagan\agent\*lock* 2>nul
del /q /f data\state\*lock* 2>nul

:: 2. Start Gateway in background if not already running
tasklist /fi "imagename eq node.exe" | findstr /i "node.exe" >nul
if errorlevel 1 (
    start /b powershell.exe -ExecutionPolicy Bypass -File .\start_gagan_ai.ps1
)

:: 3. Start Voice Sentinel silently using pythonw.exe
set PYTHONW=.\venv\Scripts\pythonw.exe
if not exist %PYTHONW% set PYTHONW=pythonw.exe
start %PYTHONW% voice\conversation_loop.py

:: 4. Start Email Watcher silently
start %PYTHONW% scripts\email_watcher.py
