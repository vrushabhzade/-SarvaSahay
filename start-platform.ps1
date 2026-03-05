# SarvaSahay Platform Startup Script
Write-Host "=== SarvaSahay Platform Startup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -NoNewline
$dockerRunning = $false

try {
    $null = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host " OK" -ForegroundColor Green
    }
} catch {
    Write-Host " NOT RUNNING" -ForegroundColor Red
}

if (-not $dockerRunning) {
    Write-Host ""
    Write-Host "Docker Desktop is not running!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please start Docker Desktop:" -ForegroundColor White
    Write-Host "  1. Press Windows Key" -ForegroundColor Gray
    Write-Host "  2. Type 'Docker Desktop'" -ForegroundColor Gray
    Write-Host "  3. Right-click and select 'Run as administrator'" -ForegroundColor Gray
    Write-Host "  4. Wait for Docker to start (whale icon in system tray)" -ForegroundColor Gray
    Write-Host "  5. Run this script again" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Docker is running, start the platform
Write-Host ""
Write-Host "Starting SarvaSahay platform..." -ForegroundColor Cyan
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Platform Started Successfully! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Yellow
    Write-Host "  API:          http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health Check: http://localhost:8000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Yellow
    Write-Host "  View logs:    docker-compose logs -f" -ForegroundColor Gray
    Write-Host "  Stop:         docker-compose down" -ForegroundColor Gray
    Write-Host "  Restart:      docker-compose restart" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Failed to start platform. Check logs with:" -ForegroundColor Red
    Write-Host "  docker-compose logs" -ForegroundColor Gray
    Write-Host ""
}
