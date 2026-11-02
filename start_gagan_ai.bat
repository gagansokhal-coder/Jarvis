@echo off
title Starting Gagan AI in Background
cd /d "%~dp0"
wscript.exe "%~dp0start_background.vbs"
echo [OK] Gagan AI Assistant started in background!
echo You can close this window now. The Telegram bot will keep running.
timeout /t 3 >nul
