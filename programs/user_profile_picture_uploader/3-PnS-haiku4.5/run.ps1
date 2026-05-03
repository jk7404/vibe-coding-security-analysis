# Profile Picture Upload Tool - Quick Start Script

Write-Host "Setting up Profile Picture Upload Tool..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Create uploads directory
Write-Host "Creating uploads directory..." -ForegroundColor Yellow
if (-Not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

# Run the application
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✓ Setup complete! Starting server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n🌐 Open your browser:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:5000/" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Gray

python app.py
