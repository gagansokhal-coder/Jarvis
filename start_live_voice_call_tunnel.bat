@echo off
title GAGAN AI // Mobile Live Voice Call with Telegram Link
cd /d "%~dp0"
echo ============================================================
echo   GAGAN AI - MOBILE LIVE VOICE CALL (CLOUDFLARE TUNNEL)
echo ============================================================
echo.
echo Launching tunnel and automatically delivering HTTPS link to your Telegram...
.\venv\Scripts\python.exe scripts\launch_tunnel_with_telegram.py
pause
