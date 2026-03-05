@echo off
REM SarvaSahay Platform - Local Development Startup Script (Windows)

echo ============================================================
echo   SarvaSahay Platform - Local Development Server
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [2/3] Virtual environment not found. Creating one...
    python -m venv .venv
    echo Virtual environment created.
    echo.
) else (
    echo [2/3] Virtual environment found.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies if needed
echo [3/3] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements-dev.txt
    echo.
) else (
    echo Dependencies already installed.
    echo.
)

REM Start the server
echo ============================================================
echo   Starting SarvaSahay Platform...
echo ============================================================
echo.
echo Server will be available at:
echo   - http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo.
echo Press CTRL+C to stop the server
echo ============================================================
echo.

python start_local.py

pause
