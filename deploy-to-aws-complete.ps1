#!/usr/bin/env pwsh
# Complete AWS Deployment Script for SarvaSahay
# Deploys both frontend and backend to AWS

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "ap-south-1",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackend,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipFrontend
)

Write-Host "🚀 SarvaSahay AWS Deployment Script" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version
    Write-Host "✅ AWS CLI installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ AWS Account: $($identity.Account)" -ForegroundColor Green
    Write-Host "✅ AWS User: $($identity.Arn)" -ForegroundColor Green
    $accountId = $identity.Account
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BACKEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $SkipBackend) {
    # Step 1: Create ECR repository
    Write-Host "Step 1: Creating ECR repository..." -ForegroundColor Yellow
    try {
        aws ecr describe-repositories --repository-names sarvasahay-backend --region $Region 2>$null
        Write-Host "✅ ECR repository already exists" -ForegroundColor Green
    } catch {
        aws ecr create-repository --repository-name sarvasahay-backend --region $Region
        Write-Host "✅ ECR repository created" -ForegroundColor Green
    }

    # Step 2: Build Docker image
    Write-Host ""
    Write-Host "Step 2: Building Docker image..." -ForegroundColor Yellow
    Set-Location -SarvaSahay
    docker build -t sarvasahay-backend:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Docker image built" -ForegroundColor Green

    # Step 3: Login to ECR
    Write-Host ""
    Write-Host "Step 3: Logging in to ECR..." -ForegroundColor Yellow
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$accountId.dkr.ecr.$Region.amazonaws.com"
    Write-Host "✅ Logged in to ECR" -ForegroundColor Green

    # Step 4: Tag and push image
    Write-Host ""
    Write-Host "Step 4: Pushing image to ECR..." -ForegroundColor Yellow
    docker tag sarvasahay-backend:latest "$accountId.dkr.ecr.$Region.amazonaws.com/sarvasahay-backend:latest"
    docker push "$accountId.dkr.ecr.$Region.amazonaws.com/sarvasahay-backend:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker push failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Image pushed to ECR" -ForegroundColor Green

    # Step 5: Create ECS cluster
    Write-Host ""
    Write-Host "Step 5: Creating ECS cluster..." -ForegroundColor Yellow
    try {
        aws ecs describe-clusters --clusters sarvasahay-cluster --region $Region 2>$null
        Write-Host "✅ ECS cluster already exists" -ForegroundColor Green
    } catch {
        aws ecs create-cluster --cluster-name sarvasahay-cluster --region $Region
        Write-Host "✅ ECS cluster created" -ForegroundColor Green
    }

    # Step 6: Register task definition
    Write-Host ""
    Write-Host "Step 6: Registering ECS task definition..." -ForegroundColor Yellow
    
    # Update task definition with account ID
    $taskDefPath = "infrastructure/aws/task-definition-complete.json"
    $taskDef = Get-Content $taskDefPath -Raw
    $taskDef = $taskDef -replace '<account-id>', $accountId
    $taskDef | Set-Content "$taskDefPath.tmp"
    
    aws ecs register-task-definition --cli-input-json file://$taskDefPath.tmp --region $Region
    Remove-Item "$taskDefPath.tmp"
    Write-Host "✅ Task definition registered" -ForegroundColor Green

    # Step 7: Create or update ECS service
    Write-Host ""
    Write-Host "Step 7: Creating/updating ECS service..." -ForegroundColor Yellow
    Write-Host "⚠️  Note: You need to manually configure VPC, subnets, and security groups" -ForegroundColor Yellow
    Write-Host "   Run the following command with your VPC details:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   aws ecs create-service \\" -ForegroundColor Cyan
    Write-Host "     --cluster sarvasahay-cluster \\" -ForegroundColor Cyan
    Write-Host "     --service-name sarvasahay-backend \\" -ForegroundColor Cyan
    Write-Host "     --task-definition sarvasahay-backend \\" -ForegroundColor Cyan
    Write-Host "     --desired-count 2 \\" -ForegroundColor Cyan
    Write-Host "     --launch-type FARGATE \\" -ForegroundColor Cyan
    Write-Host "     --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}' \\" -ForegroundColor Cyan
    Write-Host "     --region $Region" -ForegroundColor Cyan
    Write-Host ""

    Set-Location ..
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FRONTEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $SkipFrontend) {
    # Step 1: Build frontend
    Write-Host "Step 1: Building frontend..." -ForegroundColor Yellow
    Set-Location frontend/web-app
    
    # Create production env file
    $apiUrl = Read-Host "Enter backend API URL (e.g., https://api.sarvasahay.com or ALB DNS)"
    "REACT_APP_API_URL=$apiUrl`nREACT_APP_ENV=production" | Set-Content .env.production
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Frontend built" -ForegroundColor Green

    # Step 2: Create S3 bucket
    Write-Host ""
    Write-Host "Step 2: Creating S3 bucket..." -ForegroundColor Yellow
    try {
        aws s3 mb s3://sarvasahay-frontend-$Environment --region $Region
        Write-Host "✅ S3 bucket created" -ForegroundColor Green
    } catch {
        Write-Host "✅ S3 bucket already exists" -ForegroundColor Green
    }

    # Step 3: Enable static website hosting
    Write-Host ""
    Write-Host "Step 3: Enabling static website hosting..." -ForegroundColor Yellow
    aws s3 website s3://sarvasahay-frontend-$Environment --index-document index.html --error-document index.html
    Write-Host "✅ Static website hosting enabled" -ForegroundColor Green

    # Step 4: Upload files
    Write-Host ""
    Write-Host "Step 4: Uploading files to S3..." -ForegroundColor Yellow
    aws s3 sync build/ s3://sarvasahay-frontend-$Environment --delete --region $Region
    Write-Host "✅ Files uploaded" -ForegroundColor Green

    # Step 5: Make bucket public
    Write-Host ""
    Write-Host "Step 5: Configuring bucket policy..." -ForegroundColor Yellow
    $bucketPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::sarvasahay-frontend-$Environment/*"
    }
  ]
}
"@
    $bucketPolicy | Set-Content bucket-policy.json
    aws s3api put-bucket-policy --bucket sarvasahay-frontend-$Environment --policy file://bucket-policy.json
    Remove-Item bucket-policy.json
    Write-Host "✅ Bucket policy configured" -ForegroundColor Green

    # Step 6: Get S3 website URL
    Write-Host ""
    Write-Host "Step 6: Getting S3 website URL..." -ForegroundColor Yellow
    $websiteUrl = "http://sarvasahay-frontend-$Environment.s3-website.$Region.amazonaws.com"
    Write-Host "✅ Frontend deployed to: $websiteUrl" -ForegroundColor Green

    # Step 7: CloudFront (optional)
    Write-Host ""
    Write-Host "Step 7: CloudFront distribution (optional)..." -ForegroundColor Yellow
    $createCF = Read-Host "Create CloudFront distribution? (y/n)"
    if ($createCF -eq 'y') {
        Write-Host "Creating CloudFront distribution..." -ForegroundColor Yellow
        Write-Host "⚠️  This may take 15-20 minutes" -ForegroundColor Yellow
        
        # Create CloudFront distribution
        aws cloudfront create-distribution --distribution-config file://../../infrastructure/aws/cloudfront-config.json --region $Region
        Write-Host "✅ CloudFront distribution created" -ForegroundColor Green
        Write-Host "   Check AWS Console for distribution URL" -ForegroundColor Cyan
    }

    Set-Location ../..
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host ""

if (-not $SkipBackend) {
    Write-Host "Backend:" -ForegroundColor Yellow
    Write-Host "  ✅ Docker image pushed to ECR" -ForegroundColor Green
    Write-Host "  ✅ ECS cluster created" -ForegroundColor Green
    Write-Host "  ✅ Task definition registered" -ForegroundColor Green
    Write-Host "  ⚠️  ECS service needs manual configuration" -ForegroundColor Yellow
    Write-Host ""
}

if (-not $SkipFrontend) {
    Write-Host "Frontend:" -ForegroundColor Yellow
    Write-Host "  ✅ Built and uploaded to S3" -ForegroundColor Green
    Write-Host "  ✅ Static website hosting enabled" -ForegroundColor Green
    Write-Host "  🌐 URL: $websiteUrl" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "📚 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Configure VPC, subnets, and security groups" -ForegroundColor White
Write-Host "  2. Create RDS PostgreSQL database" -ForegroundColor White
Write-Host "  3. Create ElastiCache Redis cluster" -ForegroundColor White
Write-Host "  4. Create Application Load Balancer" -ForegroundColor White
Write-Host "  5. Create ECS service with ALB integration" -ForegroundColor White
Write-Host "  6. Configure domain and SSL certificate" -ForegroundColor White
Write-Host "  7. Set up CloudWatch monitoring and alarms" -ForegroundColor White
Write-Host ""

Write-Host "📖 For detailed instructions, see:" -ForegroundColor Cyan
Write-Host "   - AWS_FULL_DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "   - AWS_DEPLOYMENT_STEP_BY_STEP.md" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Deployment script completed successfully!" -ForegroundColor Green
