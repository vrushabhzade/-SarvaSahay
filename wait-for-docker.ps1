# Wait for Docker Desktop to be ready
Write-Host "Waiting for Docker Desktop to start..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ready = $false

while ((-not $ready) -and ($attempt -lt $maxAttempts)) {
    $attempt++
    Write-Host "Attempt $attempt/$maxAttempts..." -NoNewline
    
    $result = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        Write-Host " Docker is ready!" -ForegroundColor Green
    } else {
        Write-Host " Still starting..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if ($ready) {
    Write-Host "`nDocker Desktop is ready! Starting SarvaSahay platform..." -ForegroundColor Green
    Write-Host "`nRunning: docker-compose up -d" -ForegroundColor Cyan
    docker-compose up -d
    
    Write-Host "`nPlatform started successfully!" -ForegroundColor Green
    Write-Host "`nAccess points:" -ForegroundColor Yellow
    Write-Host "  - API: http://localhost:8000" -ForegroundColor White
    Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor White
    
    Write-Host "`nView logs with: docker-compose logs -f" -ForegroundColor Cyan
} else {
    Write-Host "`nDocker Desktop failed to start after $maxAttempts attempts" -ForegroundColor Red
    Write-Host "Please start Docker Desktop manually and try again" -ForegroundColor Yellow
}
