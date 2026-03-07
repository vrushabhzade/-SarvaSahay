#!/usr/bin/env pwsh
# Start SarvaSahay Frontend
# This script starts the React development server

Write-Host "🇮🇳 Starting SarvaSahay Frontend..." -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "frontend/web-app")) {
    Write-Host "❌ Error: frontend/web-app directory not found" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Navigate to frontend directory
Set-Location frontend/web-app

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Starting development server..." -ForegroundColor Green
Write-Host ""
Write-Host "The app will open at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "You should see:" -ForegroundColor Yellow
Write-Host "  • 🇮🇳 SarvaSahay Platform header" -ForegroundColor White
Write-Host "  • Welcome message in English, Hindi, Marathi" -ForegroundColor White
Write-Host "  • Four feature cards" -ForegroundColor White
Write-Host "  • Stats section (30+ schemes, 89% accuracy, <5s response)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the development server
npm start
