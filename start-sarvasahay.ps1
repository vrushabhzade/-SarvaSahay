# SarvaSahay Platform - Quick Start Script
Write-Host "🚀 Starting SarvaSahay Platform..." -ForegroundColor Green

# Check if Docker is running
Write-Host "`n📦 Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check backend containers
Write-Host "`n🔍 Checking backend services..." -ForegroundColor Yellow
$containers = docker ps --format "{{.Names}}"
$backendRunning = $containers -match "sarvasahay-app"
$postgresRunning = $containers -match "sarvasahay-postgres"
$redisRunning = $containers -match "sarvasahay-redis"

if (-not $backendRunning) {
    Write-Host "⚠️  Backend not running. Starting Docker containers..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
} else {
    Write-Host "✅ Backend is running" -ForegroundColor Green
}

# Display backend status
Write-Host "`n📊 Backend Status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "sarvasahay"

# Test backend connection
Write-Host "`n🔗 Testing backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    Write-Host "✅ Backend API is responding" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor White
    Write-Host "   Environment: $($response.environment)" -ForegroundColor White
} catch {
    Write-Host "❌ Backend API is not responding" -ForegroundColor Red
    Write-Host "   Please wait a moment and try again" -ForegroundColor Yellow
}

# Start frontend
Write-Host "`n🎨 Starting frontend..." -ForegroundColor Yellow
Write-Host "   Frontend will open at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Backend API is at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs are at: http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`n📝 Press Ctrl+C to stop the frontend" -ForegroundColor Yellow
Write-Host "`n" -NoNewline

# Navigate to frontend and start
Set-Location frontend/web-app
npm start
