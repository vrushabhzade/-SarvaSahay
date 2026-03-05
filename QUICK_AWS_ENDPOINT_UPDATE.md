# Quick AWS Endpoint Update Guide

## TL;DR - Quick Commands

### Show Current Configuration
```bash
python scripts/update_aws_endpoints.py show
```

### Change AWS Region
```bash
# Example: Change from ap-south-1 to us-east-1
python scripts/update_aws_endpoints.py region us-east-1
```

### Update API Gateway
```bash
# Update with your API Gateway ID
python scripts/update_aws_endpoints.py api-gateway abc123xyz
```

### Update S3 Buckets
```bash
python scripts/update_aws_endpoints.py s3 \
  --documents my-docs-bucket \
  --ml-models my-models-bucket \
  --backups my-backups-bucket
```

### Enable LocalStack (Local Development)
```bash
python scripts/update_aws_endpoints.py localstack --enable
```

### Disable LocalStack
```bash
python scripts/update_aws_endpoints.py localstack --disable
```

## Manual Update (Edit .env file)

### 1. Change Region
```bash
# Edit .env file
AWS_DEFAULT_REGION=us-east-1  # Change this
```

### 2. Update API Gateway Endpoint
```bash
# Replace YOUR-API-ID and YOUR-REGION
AWS_API_GATEWAY_ENDPOINT=https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com
```

### 3. Update S3 Buckets
```bash
AWS_S3_BUCKET_DOCUMENTS=your-documents-bucket
AWS_S3_BUCKET_ML_MODELS=your-ml-models-bucket
AWS_S3_BUCKET_BACKUPS=your-backups-bucket
```

### 4. Update Lambda Functions
```bash
AWS_LAMBDA_ELIGIBILITY_FUNCTION=your-eligibility-function-name
AWS_LAMBDA_DOCUMENT_PROCESSOR=your-document-processor-name
AWS_LAMBDA_OCR_FUNCTION=your-ocr-function-name
```

### 5. Update SNS Topics (Replace ACCOUNT_ID and REGION)
```bash
AWS_SNS_TOPIC_ELIGIBILITY=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-eligibility
AWS_SNS_TOPIC_APPLICATIONS=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-applications
AWS_SNS_TOPIC_ALERTS=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-alerts
```

### 6. Update SQS Queues (Replace ACCOUNT_ID and REGION)
```bash
AWS_SQS_QUEUE_DOCUMENTS=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-documents
AWS_SQS_QUEUE_ELIGIBILITY=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-eligibility
AWS_SQS_QUEUE_NOTIFICATIONS=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-notifications
```

## After Updating

### Restart Services
```bash
# Stop services
docker-compose down

# Start services with new configuration
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### Verify Configuration
```bash
# Test AWS connection
docker-compose exec app python -c "
from shared.utils.aws_s3 import get_s3_client
s3 = get_s3_client()
print('S3 client initialized successfully')
"
```

## Common Regions

| Region Name | Region Code | Location |
|-------------|-------------|----------|
| Mumbai | ap-south-1 | India |
| Singapore | ap-southeast-1 | Singapore |
| Tokyo | ap-northeast-1 | Japan |
| N. Virginia | us-east-1 | USA East |
| Oregon | us-west-2 | USA West |
| Ireland | eu-west-1 | Europe |
| Frankfurt | eu-central-1 | Europe |

## LocalStack Setup (Local Development)

### Start LocalStack
```bash
docker run -d -p 4566:4566 localstack/localstack
```

### Configure Platform
```bash
python scripts/update_aws_endpoints.py localstack --enable
```

### Create Local Resources
```bash
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
```

## Troubleshooting

### Issue: "Could not connect to endpoint"
```bash
# Check endpoint URL format
python scripts/update_aws_endpoints.py show

# Verify AWS credentials
aws configure list
```

### Issue: "Access Denied"
```bash
# Check IAM permissions
aws sts get-caller-identity

# Verify credentials in .env
cat .env | grep AWS_ACCESS_KEY_ID
```

### Issue: "Function not found"
```bash
# List Lambda functions in region
aws lambda list-functions --region YOUR-REGION

# Update function names in .env
```

## Need Help?

- **Full Documentation**: See `docs/AWS_ENDPOINT_CONFIGURATION.md`
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: See `TROUBLESHOOTING.md`
