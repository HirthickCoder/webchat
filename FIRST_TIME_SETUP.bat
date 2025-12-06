@echo off
REM ============================================================
REM  First Time Setup - Run this ONCE
REM  This will install everything needed
REM ============================================================

echo.
echo ========================================
echo  FIRST TIME SETUP
echo  AI Chatbot Lead Generator
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo     OK - Python found

REM Check if .env exists
echo.
echo [2/5] Checking environment file...
if not exist ".env" (
    if exist ".env.example" (
        echo     WARNING - .env file not found
        echo     Copying from .env.example...
        copy .env.example .env
        echo.
        echo     IMPORTANT: Edit .env file with your credentials!
        echo     - MySQL password
        echo     - OpenRouter API key
        echo.
    ) else (
        echo     [ERROR] .env.example not found!
        pause
        exit /b 1
    )
) else (
    echo     OK - .env file exists
)

REM Create virtual environment
echo.
echo [3/5] Creating virtual environment...
if exist "venv\" (
    echo     Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo     [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo     OK - Virtual environment created
)

REM Activate virtual environment
echo.
echo [4/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo     [ERROR] Failed to activate
    echo     Try: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    pause
    exit /b 1
)
echo     OK - Activated

REM Install dependencies
echo.
echo [5/5] Installing Python packages...
echo     This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo     [ERROR] Failed to install packages
    pause
    exit /b 1
)
echo     OK - All packages installed

REM Test database connection
echo.
echo ========================================
echo  Testing Database Connection...
echo ========================================
python test_db_connection.py

echo.
echo ========================================
echo  SETUP COMPLETE!
echo ========================================
echo.
echo  Next steps:
echo  1. Make sure MySQL is running
echo  2. Edit .env file if needed
echo  3. Double-click RUN_APP.bat to start
echo.
pause
