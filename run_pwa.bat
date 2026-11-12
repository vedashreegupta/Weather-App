@echo off
title SkyPulse Mobile PWA Server
echo Launching Zero-Flicker Mobile PWA at http://localhost:8000 ...
start "" http://localhost:8000
"C:\Users\Vedashree\AppData\Local\Programs\Python\Python314\python.exe" "%~dp0pwa_app.py"
pause
