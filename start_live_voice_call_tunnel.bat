@echo off
title GAGAN AI // Mobile Live Voice Call with HTTPS Tunnel
cd /d "%~dp0"
echo ============================================================
echo   GAGAN AI - MOBILE LIVE VOICE CALL (SECURE CLOUDFLARE TUNNEL)
echo ============================================================
echo.
echo 1. Starting Web Voice Server in background...
start /b .\venv\Scripts\python.exe voice\web_voice_call.py
timeout /t 2 /nobreak > nul

echo 2. Launching Cloudflare Tunnel for secure mobile HTTPS link...
echo (Open the https://*.trycloudflare.com link on your phone)
echo.
.\bin\cloudflared.exe tunnel --url http://127.0.0.1:8080
pause
