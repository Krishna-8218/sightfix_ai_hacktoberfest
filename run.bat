@echo off
title SightFix AI Launcher
cd /d "%~dp0"
echo Starting SightFix AI Desktop Application...
python main.py
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
