@echo off
title Restaurant Billing System - BBAT104 (Q08)
cd /d "%~dp0"

echo ====================================================================
echo  BBAT104 - Restaurant Billing System
echo  Student: Jay Paneru ^| Reg No: 2410302024
echo  Quality Goal: Q08 - Improve User Satisfaction
echo ====================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment Python executable not found at:
    echo         "%~dp0.venv\Scripts\python.exe"
    echo.
    echo Please ensure Python 3.10-3.12 is installed and create the environment:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [INFO] Launching Desktop GUI via virtual environment Python...
".venv\Scripts\python.exe" main.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
