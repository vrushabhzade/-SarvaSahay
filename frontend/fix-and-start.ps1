# SarvaSahay Frontend - Fix and Start Script
Write-Host "🔧 Fixing SarvaSahay Frontend..." -ForegroundColor Cyan

# Navigate to web-app
Set-Location web-app

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Install Material-UI if not present
Write-Host "📦 Ensuring all dependencies are installed..." -ForegroundColor Yellow
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material axios react-router-dom --legacy-peer-deps

Write-Host "`n✅ Dependencies installed!" -ForegroundColor Green

# Clear any existing processes on port 3000
Write-Host "`n🔍 Checking port 3000..." -ForegroundColor Yellow
$process = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "⚠️  Port 3000 is in use. Attempting to free it..." -ForegroundColor Yellow
    Stop-Process -Id $process.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "`n🚀 Starting SarvaSahay Frontend..." -ForegroundColor Green
Write-Host "   Opening at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Yellow

# Start the app
npm start
