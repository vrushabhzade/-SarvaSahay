# AWS Lambda Deployment Script for SarvaSahay Platform (PowerShell)
param(
    [string]$Region = $env:AWS_DEFAULT_REGION,
    [string]$AccountId = $env:AWS_ACCOUNT_ID
)

$ErrorActionPreference = "Stop"

if (-not $Region) { $Region = "ap-south-1" }
$ProjectName = "sarvasahay"

Write-Host "========================================" -ForegroundColor Green
Write-Host "SarvaSahay Lambda Deployment Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check AWS CLI
try {
    $null = aws --version
    Write-Host "AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "Error: AWS CLI not installed" -ForegroundColor Red
    exit 1
}

# Check credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $null = aws sts get-caller-identity
    Write-Host "AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Host "Error: AWS credentials not configured" -ForegroundColor Red
    Write-Host "Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Check if service directories exist
Write-Host "`nChecking service directories..." -ForegroundColor Yellow
$RequiredDirs = @(
    "services\eligibility_engine",
    "services\document_processor",
    "services\ocr_processor",
    "services\notification_handler",
    "services\tracking_updater"
)

$MissingDirs = @()
foreach ($dir in $RequiredDirs) {
    if (-not (Test-Path $dir)) {
        $MissingDirs += $dir
    }
}

if ($MissingDirs.Count -gt 0) {
    Write-Host "`nWarning: The following service directories do not exist:" -ForegroundColor Yellow
    foreach ($dir in $MissingDirs) {
        Write-Host "  - $dir" -ForegroundColor Yellow
    }
    Write-Host "`nThese Lambda functions will be skipped." -ForegroundColor Yellow
    Write-Host "Create the service directories and Lambda handler files before deploying." -ForegroundColor Yellow
    Write-Host "`nContinuing with available services..." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Account ID: $AccountId" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Cyan
Write-Host "`nNote: Lambda functions require IAM roles to be created first." -ForegroundColor Yellow
Write-Host "Please ensure the following roles exist in your AWS account:" -ForegroundColor Yellow
Write-Host "  - ${ProjectName}-eligibility-lambda-role" -ForegroundColor Yellow
Write-Host "  - ${ProjectName}-document-lambda-role" -ForegroundColor Yellow
Write-Host "  - ${ProjectName}-ocr-lambda-role" -ForegroundColor Yellow
Write-Host "  - ${ProjectName}-notification-lambda-role" -ForegroundColor Yellow
Write-Host "  - ${ProjectName}-tracking-lambda-role" -ForegroundColor Yellow
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment script ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
