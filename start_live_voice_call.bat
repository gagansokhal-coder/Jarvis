@echo off
title GAGAN AI // Live Voice Call Web Server
cd /d "%~dp0"
echo ============================================================
echo   GAGAN AI - LIVE PHONE VOICE CALL (CHATGPT VOICE MODE)
echo ============================================================
echo.
echo Local Wi-Fi URL:  http://10.155.207.59:8080
echo Local PC URL:    http://localhost:8080
echo.
echo Starting Voice Call Server...
.\venv\Scripts\python.exe voice\web_voice_call.py
pause
