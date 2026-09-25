@echo off
title EduCloud - Cloud Assignment Portal Development Runner
echo ======================================================================
echo    Starting EduCloud Development Server
echo ======================================================================

if not exist venv (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing / updating dependencies...
pip install -r requirements.txt --quiet

echo.
echo [INFO] Starting FastAPI Cloud Portal...
python start_server.py

pause
