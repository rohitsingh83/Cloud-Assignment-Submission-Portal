Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Starting Cloud Assignment Submission & Feedback Portal (PowerShell)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\python -m pip install --upgrade pip
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    .\venv\Scripts\python -m pip install -r requirements.txt
}

Write-Host "Launching server on http://127.0.0.1:8000" -ForegroundColor Green
.\venv\Scripts\python start_server.py
