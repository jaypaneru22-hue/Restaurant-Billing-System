@echo off
title Restaurant Billing System - BBAT104
cd /d "%~dp0"
echo ========================================================
echo  BBAT104 - Restaurant Billing System (Reg: 2410302024)
echo  Quality Goal: Q08 - Improve User Satisfaction
echo ========================================================
echo Starting application...
".venv\Scripts\python.exe" main.py
if %ERRORLEVEL% NEQ 0 (
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
