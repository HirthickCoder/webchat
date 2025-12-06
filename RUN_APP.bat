@echo off
REM ============================================================
REM  AI Chatbot Lead Generator - Easy Launcher
REM  Double-click this file to run the app
REM ============================================================

echo.
echo ========================================
echo  AI Chatbot Lead Generator
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run FIRST_TIME_SETUP.bat first
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activated
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Starting Streamlit app...
echo.
echo ========================================
echo  Opening browser at http://localhost:8501
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

REM Run the app
streamlit run app.py

REM If app stops
echo.
echo App stopped
pause
