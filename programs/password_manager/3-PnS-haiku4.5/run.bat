@echo off
REM Password Manager - Single Run Setup and Startup Script for Windows
REM This script installs dependencies and starts the Flask application

echo.
echo ============================================
echo  Self-Hosted Password Manager
echo  Security-First Flask Application
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Installing required dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Done!

echo.
echo [2/3] Initializing database...
python -c "from app import create_app; app = create_app(); print('Database initialized successfully!')"
if errorlevel 1 (
    echo Error: Failed to initialize database
    pause
    exit /b 1
)
echo Done!

echo.
echo [3/3] Starting Password Manager...
echo.
echo ============================================
echo  Server is running!
echo  Open your browser and go to:
echo  http://localhost:5000
echo.
echo  Register a new account to get started.
echo  Press Ctrl+C to stop the server.
echo ============================================
echo.

python app.py
