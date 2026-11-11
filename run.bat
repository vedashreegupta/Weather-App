@echo off
title Weather App with API
chcp 65001 >nul
echo.
py "%~dp0weather.py" %*
if "%~1"=="" pause
