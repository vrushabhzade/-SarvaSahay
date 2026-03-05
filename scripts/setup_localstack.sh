#!/bin/bash
# LocalStack Setup Script for SarvaSahay Platform
# This script creates all necessary AWS resources in LocalStack

set -e

ENDPOINT_URL="http://localhost:4566"
REGION="us-east-1"

echo "🚀 Setting up LocalStack for SarvaSahay Platform..."
echo ""

# Check if LocalStack is running
echo "📡 Checking LocalStack connection..."
if ! curl -s $ENDPOINT_URL/_localstack/health > /dev/null; then
    echo "❌ LocalStack is not running!"
    echo ""
    echo "Please start LocalStack first:"
    echo "  docker run -d -p 4566:4566 localstack/localstack"
    echo ""
    exit 1
fi
echo "✅ LocalStack is running"
echo ""

# Create S3 buckets
echo "🪣 Creating S3 buckets..."
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-documents --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-documents already exists"
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-ml-models --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-ml-models already exists"
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://sarvasahay-backups --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-backups already exists"
echo "✅ S3 buckets created"
echo ""

# Create DynamoDB tables
echo "🗄️  Creating DynamoDB tables..."

# Sessions table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table \
  --table-name sarvasahay-sessions \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-sessions already exists"

# Cache table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table \
  --table-name sarvasahay-cache \
  --attribute-definitions AttributeName=key,AttributeType=S \
  --key-schema AttributeName=key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-cache already exists"

# Audit logs table
aws --endpoint-url=$ENDPOINT_URL dynamodb create-table \
  --table-name sarvasahay-audit-logs \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-audit-logs already exists"

echo "✅ DynamoDB tables created"
echo ""

# Create SNS topics
echo "📢 Creating SNS topics..."
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-eligibility --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-eligibility already exists"
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-applications --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-applications already exists"
aws --endpoint-url=$ENDPOINT_URL sns create-topic --name sarvasahay-alerts --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-alerts already exists"
echo "✅ SNS topics created"
echo ""

# Create SQS queues
echo "📬 Creating SQS queues..."
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-documents --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-documents already exists"
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-eligibility --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-eligibility already exists"
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name sarvasahay-notifications --region $REGION 2>/dev/null || echo "  ℹ️  sarvasahay-notifications already exists"
echo "✅ SQS queues created"
echo ""

# Verify resources
echo "🔍 Verifying resources..."
echo ""
echo "S3 Buckets:"
aws --endpoint-url=$ENDPOINT_URL s3 ls
echo ""
echo "DynamoDB Tables:"
aws --endpoint-url=$ENDPOINT_URL dynamodb list-tables --region $REGION --output table
echo ""
echo "SNS Topics:"
aws --endpoint-url=$ENDPOINT_URL sns list-topics --region $REGION --output table
echo ""
echo "SQS Queues:"
aws --endpoint-url=$ENDPOINT_URL sqs list-queues --region $REGION --output table
echo ""

echo "✅ LocalStack setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure platform: python scripts/update_aws_endpoints.py localstack --enable"
echo "  2. Restart services: docker-compose down && docker-compose up -d"
echo "  3. Run tests: pytest tests/integration/"
echo ""
