# SarvaSahay Platform - Quick Deployment Script (PowerShell)
# This script provides a simple way to deploy the platform on Windows

$ErrorActionPreference = "Stop"

# Functions
function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Check prerequisites
function Check-Prerequisites {
    Print-Info "Checking prerequisites..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Print-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    Print-Success "Docker is installed"
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Print-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    Print-Success "Docker Compose is installed"
    
    if (-not (Test-Path ".env")) {
        Print-Error ".env file not found. Please create it from .env.example"
        exit 1
    }
    Print-Success ".env file exists"
}

# Build Docker images
function Build-Images {
    Print-Info "Building Docker images..."
    docker build -t sarvasahay-platform:latest -f infrastructure/docker/Dockerfile .
    Print-Success "Docker images built successfully"
}

# Start services
function Start-Services {
    Print-Info "Starting services..."
    docker-compose up -d
    Print-Success "Services started successfully"
}

# Wait for services to be ready
function Wait-ForServices {
    Print-Info "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    Print-Info "Waiting for PostgreSQL..."
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        try {
            docker-compose exec -T postgres pg_isready -U sarvasahay 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                break
            }
        } catch {}
        Start-Sleep -Seconds 2
        $retries++
    }
    Print-Success "PostgreSQL is ready"
    
    # Wait for Redis
    Print-Info "Waiting for Redis..."
    $retries = 0
    while ($retries -lt $maxRetries) {
        try {
            docker-compose exec -T redis redis-cli ping 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                break
            }
        } catch {}
        Start-Sleep -Seconds 2
        $retries++
    }
    Print-Success "Redis is ready"
    
    # Wait for application
    Print-Info "Waiting for application..."
    Start-Sleep -Seconds 10
    $retries = 0
    while ($retries -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                break
            }
        } catch {}
        Start-Sleep -Seconds 5
        $retries++
    }
    Print-Success "Application is ready"
}

# Initialize database
function Initialize-Database {
    Print-Info "Initializing database..."
    
    # Run migrations
    Print-Info "Running database migrations..."
    docker-compose exec -T app alembic upgrade head
    Print-Success "Database migrations completed"
    
    # Load initial data
    Print-Info "Loading government schemes..."
    docker-compose exec -T app python scripts/db_manager.py load-schemes
    Print-Success "Government schemes loaded"
    
    Print-Info "Loading form templates..."
    docker-compose exec -T app python scripts/db_manager.py load-templates
    Print-Success "Form templates loaded"
}

# Health check
function Test-Health {
    Print-Info "Running health checks..."
    
    # Check API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Print-Success "API health check passed"
        }
    } catch {
        Print-Error "API health check failed"
        exit 1
    }
    
    # Check database
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/database" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Print-Success "Database health check passed"
        }
    } catch {
        Print-Error "Database health check failed"
        exit 1
    }
    
    # Check cache
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/cache" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Print-Success "Cache health check passed"
        }
    } catch {
        Print-Error "Cache health check failed"
        exit 1
    }
}

# Show deployment info
function Show-Info {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  SarvaSahay Platform Deployment Complete" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Application URL: http://localhost:8000"
    Write-Host "API Documentation: http://localhost:8000/docs"
    Write-Host "Health Check: http://localhost:8000/health"
    Write-Host ""
    Write-Host "To view logs:"
    Write-Host "  docker-compose logs -f"
    Write-Host ""
    Write-Host "To stop services:"
    Write-Host "  docker-compose down"
    Write-Host ""
    Write-Host "To restart services:"
    Write-Host "  docker-compose restart"
    Write-Host ""
}

# Main deployment flow
function Main {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  SarvaSahay Platform Deployment" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Check-Prerequisites
    Build-Images
    Start-Services
    Wait-ForServices
    Initialize-Database
    Test-Health
    Show-Info
    
    Print-Success "Deployment completed successfully!"
}

# Run main function
Main
