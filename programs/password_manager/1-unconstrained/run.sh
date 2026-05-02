#!/bin/bash

# Password Manager Setup & Run Script

echo "🔐 Password Manager Setup"
echo "========================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python $(python3 --version | cut -d' ' -f2) detected"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "🚀 Starting Password Manager..."
echo "================================"
echo ""
echo "✓ The app is running at: http://localhost:5000"
echo "✓ Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python app.py
