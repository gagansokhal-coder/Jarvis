@echo off
title Gagan AI - Connect Google Accounts
cd /d "%~dp0"
echo ========================================================
echo   Gagan AI Multi-Account Google Connection
echo ========================================================
echo.
echo Current connected accounts:
python scripts\auth_google.py list
echo.
echo Connecting new Google account...
python scripts\auth_google.py add
echo.
echo Press any key to exit...
pause >nul
