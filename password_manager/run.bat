@echo off
echo.
echo 🔐 Password Manager Setup
echo =========================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% detected
echo.

if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 📚 Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed

echo.
echo 🚀 Starting Password Manager...
echo ================================
echo.
echo ✓ The app is running at: http://localhost:5000
echo ✓ Press Ctrl+C to stop the server
echo.

python app.py
pause
