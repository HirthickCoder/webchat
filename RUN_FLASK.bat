@echo off
REM ============================================================
REM  Flask Chatbot - Easy Launcher
REM  Double-click this file to run the Flask app
REM ============================================================

echo.
echo ========================================
echo  Flask AI Chatbot Lead Generator
echo ========================================
echo.

REM Navigate to the script directory
cd /d "%~dp0"

echo [*] Starting Flask server...
echo.
echo ========================================
echo  Server URLs:
echo  - Local:   http://localhost:5000
echo  - Network: http://192.168.1.3:5000
echo.
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

REM Run the Flask app
python app.py

REM If app stops
echo.
echo [*] Server stopped
pause
