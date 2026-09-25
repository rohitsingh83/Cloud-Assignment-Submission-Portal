@echo off
echo ======================================================================
echo   Starting Cloud Assignment Submission & Feedback Portal
echo ======================================================================
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Starting application server on http://127.0.0.1:8000
python start_server.py
pause
