# AWS ECS Deployment Script for SarvaSahay Platform (PowerShell)
# This script automates the deployment of Docker containers to AWS ECS

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "ap-south-1",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 SarvaSahay AWS Deployment Script" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Image Tag: $ImageTag" -ForegroundColor Yellow
Write-Host ""

# Configuration
$APP_NAME = "sarvasahay"
$CLUSTER_NAME = "$APP_NAME-$Environment-cluster"
$SERVICE_NAME = "$APP_NAME-$Environment-app"

# Step 1: Get AWS Account ID
Write-Host "📋 Step 1: Getting AWS Account ID..." -ForegroundColor Cyan
try {
    $ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
    Write-Host "✅ Account ID: $ACCOUNT_ID" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get AWS Account ID. Please configure AWS CLI." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Create ECR Repository (if not exists)
Write-Host "📦 Step 2: Setting up ECR Repository..." -ForegroundColor Cyan
$ECR_REPO = "$APP_NAME-$Environment"
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com/$ECR_REPO"

aws ecr describe-repositories --repository-names $ECR_REPO --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating ECR repository: $ECR_REPO" -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ECR_REPO --region $Region | Out-Null
    Write-Host "✅ ECR repository created" -ForegroundColor Green
} else {
    Write-Host "✅ ECR repository already exists" -ForegroundColor Green
}
Write-Host ""

# Step 3: Build Docker Image
Write-Host "🔨 Step 3: Building Docker Image..." -ForegroundColor Cyan
docker build -t ${APP_NAME}:${ImageTag} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Login to ECR
Write-Host "🔐 Step 4: Logging into ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECR_URI
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECR login failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Logged into ECR" -ForegroundColor Green
Write-Host ""

# Step 5: Tag and Push Image
Write-Host "📤 Step 5: Pushing Image to ECR..." -ForegroundColor Cyan
docker tag ${APP_NAME}:${ImageTag} ${ECR_URI}:${ImageTag}
docker push ${ECR_URI}:${ImageTag}
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Image push failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Image pushed to ECR: ${ECR_URI}:${ImageTag}" -ForegroundColor Green
Write-Host ""

# Step 6: Check if ECS Cluster exists
Write-Host "🔍 Step 6: Checking ECS Cluster..." -ForegroundColor Cyan
$clusterExists = aws ecs describe-clusters --clusters $CLUSTER_NAME --region $Region --query "clusters[0].status" --output text 2>$null
if ($clusterExists -ne "ACTIVE") {
    Write-Host "⚠️  ECS Cluster '$CLUSTER_NAME' not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To create infrastructure, choose one of these options:" -ForegroundColor Cyan
    Write-Host "  1. Use Terraform: cd infrastructure/terraform && terraform apply" -ForegroundColor White
    Write-Host "  2. Use AWS Copilot: copilot init" -ForegroundColor White
    Write-Host "  3. Manual setup: See infrastructure/aws/ecs-deployment.md" -ForegroundColor White
    Write-Host ""
    Write-Host "After infrastructure is created, run this script again." -ForegroundColor Yellow
    exit 0
}
Write-Host "✅ ECS Cluster is active" -ForegroundColor Green
Write-Host ""

# Step 7: Update Task Definition
Write-Host "📝 Step 7: Updating Task Definition..." -ForegroundColor Cyan

# Read and update task definition
$taskDefFile = "infrastructure/aws/task-definition.json"
if (Test-Path $taskDefFile) {
    $taskDef = Get-Content $taskDefFile | ConvertFrom-Json
    
    # Update image URI
    $taskDef.containerDefinitions[0].image = "${ECR_URI}:${ImageTag}"
    
    # Update ARNs with actual account ID
    $taskDef.executionRoleArn = $taskDef.executionRoleArn -replace "YOUR_ACCOUNT_ID", $ACCOUNT_ID
    $taskDef.taskRoleArn = $taskDef.taskRoleArn -replace "YOUR_ACCOUNT_ID", $ACCOUNT_ID
    
    # Save updated task definition
    $taskDef | ConvertTo-Json -Depth 10 | Set-Content "infrastructure/aws/task-definition-updated.json"
    
    # Register task definition
    $newTaskDef = aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition-updated.json --region $Region | ConvertFrom-Json
    $taskDefArn = $newTaskDef.taskDefinition.taskDefinitionArn
    
    Write-Host "✅ Task definition registered: $taskDefArn" -ForegroundColor Green
} else {
    Write-Host "⚠️  Task definition file not found: $taskDefFile" -ForegroundColor Yellow
    Write-Host "Using existing task definition..." -ForegroundColor Yellow
}
Write-Host ""

# Step 8: Update ECS Service
Write-Host "🔄 Step 8: Updating ECS Service..." -ForegroundColor Cyan
$serviceExists = aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $Region --query "services[0].status" --output text 2>$null

if ($serviceExists -eq "ACTIVE") {
    aws ecs update-service `
        --cluster $CLUSTER_NAME `
        --service $SERVICE_NAME `
        --force-new-deployment `
        --region $Region | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Service update initiated" -ForegroundColor Green
    } else {
        Write-Host "❌ Service update failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Service '$SERVICE_NAME' not found in cluster" -ForegroundColor Yellow
    Write-Host "Please create the service first using Terraform or AWS Console" -ForegroundColor Yellow
}
Write-Host ""

# Step 9: Wait for Deployment
Write-Host "⏳ Step 9: Waiting for deployment to complete..." -ForegroundColor Cyan
Write-Host "This may take 2-5 minutes..." -ForegroundColor Yellow

$maxWaitTime = 300  # 5 minutes
$waitInterval = 15
$elapsed = 0

while ($elapsed -lt $maxWaitTime) {
    Start-Sleep -Seconds $waitInterval
    $elapsed += $waitInterval
    
    $deployment = aws ecs describe-services `
        --cluster $CLUSTER_NAME `
        --services $SERVICE_NAME `
        --region $Region `
        --query "services[0].deployments[0]" | ConvertFrom-Json
    
    $running = $deployment.runningCount
    $desired = $deployment.desiredCount
    $status = $deployment.rolloutState
    
    Write-Host "  Status: $status | Running: $running/$desired" -ForegroundColor Gray
    
    if ($status -eq "COMPLETED" -and $running -eq $desired) {
        Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
        break
    }
    
    if ($status -eq "FAILED") {
        Write-Host "❌ Deployment failed" -ForegroundColor Red
        exit 1
    }
}

if ($elapsed -ge $maxWaitTime) {
    Write-Host "⚠️  Deployment is taking longer than expected" -ForegroundColor Yellow
    Write-Host "Check AWS Console for details" -ForegroundColor Yellow
}
Write-Host ""

# Step 10: Get Service URL
Write-Host "🌐 Step 10: Getting Service URL..." -ForegroundColor Cyan
$albArn = aws ecs describe-services `
    --cluster $CLUSTER_NAME `
    --services $SERVICE_NAME `
    --region $Region `
    --query "services[0].loadBalancers[0].targetGroupArn" --output text 2>$null

if ($albArn -and $albArn -ne "None") {
    $albName = aws elbv2 describe-target-groups `
        --target-group-arns $albArn `
        --region $Region `
        --query "TargetGroups[0].LoadBalancerArns[0]" --output text 2>$null
    
    if ($albName) {
        $albDns = aws elbv2 describe-load-balancers `
            --load-balancer-arns $albName `
            --region $Region `
            --query "LoadBalancers[0].DNSName" --output text 2>$null
        
        Write-Host "✅ Application URL: http://$albDns" -ForegroundColor Green
    }
}
Write-Host ""

# Summary
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "🎉 Deployment Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Environment:    $Environment" -ForegroundColor White
Write-Host "Region:         $Region" -ForegroundColor White
Write-Host "Cluster:        $CLUSTER_NAME" -ForegroundColor White
Write-Host "Service:        $SERVICE_NAME" -ForegroundColor White
Write-Host "Image:          ${ECR_URI}:${ImageTag}" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Monitor deployment: aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $Region" -ForegroundColor White
Write-Host "  2. View logs: aws logs tail /ecs/$APP_NAME-$Environment --follow --region $Region" -ForegroundColor White
Write-Host "  3. Check health: curl http://ALB_DNS_NAME/health" -ForegroundColor White
Write-Host ""
