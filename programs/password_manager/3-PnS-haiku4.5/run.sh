#!/bin/bash
# Password Manager - Single Run Setup and Startup Script for Unix/Linux/macOS
# This script installs dependencies and starts the Flask application

echo ""
echo "============================================"
echo "  Self-Hosted Password Manager"
echo "  Security-First Flask Application"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "[1/3] Installing required dependencies..."
pip3 install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "Done!"

echo ""
echo "[2/3] Initializing database..."
python3 -c "from app import create_app; app = create_app(); print('Database initialized successfully!')"
if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize database"
    exit 1
fi
echo "Done!"

echo ""
echo "[3/3] Starting Password Manager..."
echo ""
echo "============================================"
echo "  Server is running!"
echo "  Open your browser and go to:"
echo "  http://localhost:5000"
echo ""
echo "  Register a new account to get started."
echo "  Press Ctrl+C to stop the server."
echo "============================================"
echo ""

python3 app.py
