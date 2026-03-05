# LocalStack Setup Script for SarvaSahay Platform (PowerShell)
# This script creates all necessary AWS resources in LocalStack

$ErrorActionPreference = "Continue"

$ENDPOINT_URL = "http://localhost:4566"
$REGION = "us-east-1"

Write-Host "🚀 Setting up LocalStack for SarvaSahay Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if LocalStack is running
Write-Host "📡 Checking LocalStack connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ENDPOINT_URL/_localstack/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ LocalStack is running" -ForegroundColor Green
} catch {
    Write-Host "❌ LocalStack is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start LocalStack first:"
    Write-Host "  docker run -d -p 4566:4566 localstack/localstack"
    Write-Host ""
    exit 1
}
Write-Host ""

# Create S3 buckets
Write-Host "🪣 Creating S3 buckets..." -ForegroundColor Yellow
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-documents --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-documents already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-ml-models --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-ml-models already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-backups --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-backups already exists" -ForegroundColor Gray }
Write-Host "✅ S3 buckets created" -ForegroundColor Green
Write-Host ""

# Create DynamoDB tables
Write-Host "🗄️  Creating DynamoDB tables..." -ForegroundColor Yellow

# Sessions table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table `
  --table-name sarvasahay-sessions `
  --attribute-definitions AttributeName=id,AttributeType=S `
  --key-schema AttributeName=id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-sessions already exists" -ForegroundColor Gray }

# Cache table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table `
  --table-name sarvasahay-cache `
  --attribute-definitions AttributeName=key,AttributeType=S `
  --key-schema AttributeName=key,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-cache already exists" -ForegroundColor Gray }

# Audit logs table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table `
  --table-name sarvasahay-audit-logs `
  --attribute-definitions AttributeName=id,AttributeType=S `
  --key-schema AttributeName=id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-audit-logs already exists" -ForegroundColor Gray }

Write-Host "✅ DynamoDB tables created" -ForegroundColor Green
Write-Host ""

# Create SNS topics
Write-Host "📢 Creating SNS topics..." -ForegroundColor Yellow
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-eligibility --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-eligibility already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-applications --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-applications already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-alerts --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-alerts already exists" -ForegroundColor Gray }
Write-Host "✅ SNS topics created" -ForegroundColor Green
Write-Host ""

# Create SQS queues
Write-Host "📬 Creating SQS queues..." -ForegroundColor Yellow
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-documents --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-documents already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-eligibility --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-eligibility already exists" -ForegroundColor Gray }
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-notifications --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ℹ️  sarvasahay-notifications already exists" -ForegroundColor Gray }
Write-Host "✅ SQS queues created" -ForegroundColor Green
Write-Host ""

# Verify resources
Write-Host "🔍 Verifying resources..." -ForegroundColor Yellow
Write-Host ""
Write-Host "S3 Buckets:" -ForegroundColor Cyan
aws --endpoint-url=$ENDPOINT_URL s3 ls
Write-Host ""
Write-Host "DynamoDB Tables:" -ForegroundColor Cyan
aws --endpoint-url=$ENDPOINT_URL dynamodb list-tables --region $REGION --output table
Write-Host ""
Write-Host "SNS Topics:" -ForegroundColor Cyan
aws --endpoint-url=$ENDPOINT_URL sns list-topics --region $REGION --output table
Write-Host ""
Write-Host "SQS Queues:" -ForegroundColor Cyan
aws --endpoint-url=$ENDPOINT_URL sqs list-queues --region $REGION --output table
Write-Host ""

Write-Host "✅ LocalStack setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Configure platform: python scripts/update_aws_endpoints.py localstack --enable"
Write-Host "  2. Restart services: docker-compose down; docker-compose up -d"
Write-Host "  3. Run tests: pytest tests/integration/"
Write-Host ""
