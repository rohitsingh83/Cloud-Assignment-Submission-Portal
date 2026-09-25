@echo off
title EduCloud - Automated Pytest Runner
echo ======================================================================
echo    Running EduCloud Automated Test Suite (19/19 Tests)
echo ======================================================================

call venv\Scripts\activate.bat
pytest -v

echo.
echo ======================================================================
echo    Running End-to-End Programmatic Lifecycle Walkthrough
echo ======================================================================
python demo_walkthrough.py

pause
