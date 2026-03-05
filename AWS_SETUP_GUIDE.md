# AWS Configuration Setup Guide for SarvaSahay Platform

## Quick Start Options

You have three options for AWS configuration:

1. **LocalStack (Recommended for Development)** - Run AWS services locally
2. **AWS Free Tier** - Use real AWS services with free tier limits
3. **Full AWS Production** - Complete AWS setup for production

---

## Option 1: LocalStack Setup (Local Development)

LocalStack simulates AWS services on your local machine - perfect for development and testing.

### Step 1: Install and Start LocalStack

```bash
# Using Docker (recommended)
docker run -d -p 4566:4566 -p 4571:4571 localstack/localstack

# Or add to your docker-compose.yml
```

### Step 2: Configure Platform for LocalStack

```bash
# Run the automated configuration script
python scripts/update_aws_endpoints.py localstack --enable

# This will update your .env file with LocalStack endpoints
```

### Step 3: Create Local AWS Resources

```bash
# Set AWS CLI to use LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566

# Create S3 buckets
aws --endpoint-url=http://localhost:4566 s3 mb s3://sarvasahay-documents
aws --endpoint-url=http://localhost:4566 s3 mb s3://sarvasahay-ml-models
aws --endpoint-url=http://localhost:4566 s3 mb s3://sarvasahay-backups

# Create DynamoDB tables
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name sarvasahay-sessions \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name sarvasahay-cache \
  --attribute-definitions AttributeName=key,AttributeType=S \
  --key-schema AttributeName=key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Create SNS topics
aws --endpoint-url=http://localhost:4566 sns create-topic --name sarvasahay-eligibility
aws --endpoint-url=http://localhost:4566 sns create-topic --name sarvasahay-applications
aws --endpoint-url=http://localhost:4566 sns create-topic --name sarvasahay-alerts

# Create SQS queues
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name sarvasahay-documents
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name sarvasahay-eligibility
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name sarvasahay-notifications
```

### Step 4: Verify LocalStack Setup

```bash
# Test S3
python -c "from shared.utils.aws_s3 import get_s3_client; print('S3 OK')"

# Test Lambda
python -c "from shared.utils.aws_lambda import get_lambda_client; print('Lambda OK')"
```

---

## Option 2: AWS Free Tier Setup

### Step 1: Create AWS Account

1. Go to https://aws.amazon.com/free/
2. Sign up for a free tier account
3. Note your AWS Account ID (12-digit number)

### Step 2: Create IAM User

```bash
# In AWS Console:
# 1. Go to IAM → Users → Add User
# 2. User name: sarvasahay-dev
# 3. Access type: Programmatic access
# 4. Attach policies:
#    - AmazonS3FullAccess
#    - AWSLambdaFullAccess
#    - AmazonDynamoDBFullAccess
#    - AmazonSNSFullAccess
#    - AmazonSQSFullAccess
# 5. Save Access Key ID and Secret Access Key
```

### Step 3: Configure AWS Credentials

Update your `.env` file:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012
```

### Step 4: Create AWS Resources

```bash
# Set your region
export AWS_REGION=ap-south-1

# Create S3 buckets
aws s3 mb s3://sarvasahay-documents-dev --region $AWS_REGION
aws s3 mb s3://sarvasahay-ml-models-dev --region $AWS_REGION
aws s3 mb s3://sarvasahay-backups-dev --region $AWS_REGION

# Update .env with actual bucket names
python scripts/update_aws_endpoints.py s3 \
  --documents sarvasahay-documents-dev \
  --ml-models sarvasahay-ml-models-dev \
  --backups sarvasahay-backups-dev

# Create DynamoDB tables
aws dynamodb create-table \
  --table-name sarvasahay-sessions \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# Create SNS topics
aws sns create-topic --name sarvasahay-eligibility --region $AWS_REGION
aws sns create-topic --name sarvasahay-applications --region $AWS_REGION
aws sns create-topic --name sarvasahay-alerts --region $AWS_REGION

# Create SQS queues
aws sqs create-queue --queue-name sarvasahay-documents --region $AWS_REGION
aws sqs create-queue --queue-name sarvasahay-eligibility --region $AWS_REGION
aws sqs create-queue --queue-name sarvasahay-notifications --region $AWS_REGION
```

### Step 5: Update SNS/SQS ARNs in .env

After creating resources, get their ARNs:

```bash
# Get SNS topic ARNs
aws sns list-topics --region $AWS_REGION

# Get SQS queue URLs
aws sqs list-queues --region $AWS_REGION

# Update .env file manually with actual ARNs
```

---

## Option 3: Full AWS Production Setup

For production deployment with all AWS services.

### Step 1: Set Up AWS Organization

1. Create production AWS account
2. Set up IAM roles with least privilege
3. Enable CloudTrail for audit logging
4. Configure AWS Config for compliance

### Step 2: Deploy Infrastructure

```bash
# Use the provided Terraform/CloudFormation scripts
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Or use AWS CDK
cd infrastructure/cdk
cdk deploy
```

### Step 3: Configure Production Endpoints

```bash
# Update region (e.g., Mumbai for India)
python scripts/update_aws_endpoints.py region ap-south-1

# Update API Gateway (after deployment)
python scripts/update_aws_endpoints.py api-gateway YOUR-API-ID

# Update S3 buckets (use production names)
python scripts/update_aws_endpoints.py s3 \
  --documents sarvasahay-prod-documents \
  --ml-models sarvasahay-prod-ml-models \
  --backups sarvasahay-prod-backups
```

---

## Common Configuration Tasks

### Change AWS Region

```bash
# Example: Change from Mumbai to Singapore
python scripts/update_aws_endpoints.py region ap-southeast-1
```

### View Current Configuration

```bash
python scripts/update_aws_endpoints.py show
```

### Switch Between LocalStack and AWS

```bash
# Enable LocalStack
python scripts/update_aws_endpoints.py localstack --enable

# Disable LocalStack (use real AWS)
python scripts/update_aws_endpoints.py localstack --disable
```

---

## Testing Your Configuration

### Test S3 Upload/Download

```python
from shared.utils.aws_s3 import get_s3_client
import io

s3 = get_s3_client()

# Upload test file
test_data = io.BytesIO(b"Test document content")
s3_key = s3.upload_document(test_data, "test-user", "test-doc", "txt")
print(f"Uploaded to: {s3_key}")

# Download test file
content = s3.download_document(s3_key)
print(f"Downloaded: {content}")

# Clean up
s3.delete_document(s3_key)
print("Test successful!")
```

### Test Lambda Invocation

```python
from shared.utils.aws_lambda import get_lambda_client

lambda_client = get_lambda_client()

# Test eligibility engine (will fail if function doesn't exist)
try:
    result = lambda_client.invoke_eligibility_engine({
        "age": 25,
        "income": 50000,
        "state": "Maharashtra"
    })
    print(f"Lambda result: {result}")
except Exception as e:
    print(f"Lambda test: {e}")
    print("Note: Lambda functions need to be deployed first")
```

---

## Troubleshooting

### Issue: "Could not connect to endpoint"

```bash
# Check endpoint configuration
python scripts/update_aws_endpoints.py show

# Verify LocalStack is running (if using LocalStack)
docker ps | grep localstack

# Test AWS credentials
aws sts get-caller-identity
```

### Issue: "Access Denied"

```bash
# Verify AWS credentials
aws configure list

# Check IAM permissions
aws iam get-user

# Ensure .env has correct credentials
cat .env | grep AWS_ACCESS_KEY_ID
```

### Issue: "Bucket does not exist"

```bash
# List existing buckets
aws s3 ls

# Create missing buckets
aws s3 mb s3://your-bucket-name --region your-region
```

---

## Security Best Practices

1. **Never commit .env file** - It contains sensitive credentials
2. **Use IAM roles** in production instead of access keys
3. **Enable encryption** for S3 buckets (already configured in code)
4. **Rotate credentials** regularly
5. **Use AWS Secrets Manager** for production secrets
6. **Enable MFA** for AWS console access
7. **Set up CloudWatch alarms** for unusual activity

---

## Cost Optimization

### Free Tier Limits (First 12 months)

- **S3**: 5GB storage, 20,000 GET requests, 2,000 PUT requests
- **Lambda**: 1M free requests, 400,000 GB-seconds compute
- **DynamoDB**: 25GB storage, 25 read/write capacity units
- **SNS**: 1M publishes, 100,000 HTTP deliveries
- **SQS**: 1M requests

### Tips to Stay Within Free Tier

1. Use LocalStack for development
2. Delete test resources after use
3. Set up billing alerts in AWS Console
4. Use S3 lifecycle policies to delete old files
5. Monitor usage in AWS Cost Explorer

---

## Next Steps

After configuring AWS:

1. **Restart services**: `docker-compose down && docker-compose up -d`
2. **Run tests**: `pytest tests/integration/test_comprehensive_integration.py`
3. **Deploy Lambda functions**: See `infrastructure/lambda/README.md`
4. **Set up monitoring**: Configure CloudWatch dashboards

---

## Quick Reference

### Environment Variables

```bash
# Core AWS
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012

# Custom Endpoints (LocalStack)
AWS_S3_ENDPOINT_URL=http://localhost:4566
AWS_LAMBDA_ENDPOINT_URL=http://localhost:4566
AWS_DYNAMODB_ENDPOINT_URL=http://localhost:4566
AWS_SQS_ENDPOINT_URL=http://localhost:4566
AWS_SNS_ENDPOINT_URL=http://localhost:4566

# S3 Buckets
AWS_S3_BUCKET_DOCUMENTS=sarvasahay-documents
AWS_S3_BUCKET_ML_MODELS=sarvasahay-ml-models
AWS_S3_BUCKET_BACKUPS=sarvasahay-backups

# Lambda Functions
AWS_LAMBDA_ELIGIBILITY_FUNCTION=sarvasahay-eligibility-engine
AWS_LAMBDA_DOCUMENT_PROCESSOR=sarvasahay-document-processor
AWS_LAMBDA_OCR_FUNCTION=sarvasahay-ocr-processor
```

### Useful Commands

```bash
# Show config
python scripts/update_aws_endpoints.py show

# Change region
python scripts/update_aws_endpoints.py region us-east-1

# Enable LocalStack
python scripts/update_aws_endpoints.py localstack --enable

# Test connection
aws s3 ls --endpoint-url $AWS_S3_ENDPOINT_URL
```

---

## Support

- **Documentation**: See `docs/AWS_ENDPOINT_CONFIGURATION.md`
- **Quick Guide**: See `QUICK_AWS_ENDPOINT_UPDATE.md`
- **Troubleshooting**: See `TROUBLESHOOTING.md`
- **AWS Documentation**: https://docs.aws.amazon.com/
- **LocalStack Docs**: https://docs.localstack.cloud/
