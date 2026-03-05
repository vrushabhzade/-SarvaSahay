# AWS Endpoint Configuration Guide

This guide explains how to update AWS endpoints for the SarvaSahay platform.

## Overview

The platform uses AWS services for:
- **S3**: Document storage and ML model storage
- **Lambda**: Serverless processing functions
- **API Gateway**: REST API endpoints
- **Textract**: OCR document processing
- **Rekognition**: Document validation
- **SNS**: Notification topics
- **SQS**: Message queues
- **DynamoDB**: NoSQL data storage

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Update your `.env` file with the appropriate AWS endpoints:

```bash
# AWS Region
AWS_DEFAULT_REGION=ap-south-1  # Change to your region

# AWS API Gateway Endpoint
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.ap-south-1.amazonaws.com
AWS_API_GATEWAY_STAGE=prod

# AWS S3 Buckets
AWS_S3_BUCKET_DOCUMENTS=sarvasahay-documents
AWS_S3_BUCKET_ML_MODELS=sarvasahay-ml-models
AWS_S3_BUCKET_BACKUPS=sarvasahay-backups

# AWS Lambda Functions
AWS_LAMBDA_ELIGIBILITY_FUNCTION=sarvasahay-eligibility-engine
AWS_LAMBDA_DOCUMENT_PROCESSOR=sarvasahay-document-processor
AWS_LAMBDA_OCR_FUNCTION=sarvasahay-ocr-processor
AWS_LAMBDA_NOTIFICATION_FUNCTION=sarvasahay-notification-handler
AWS_LAMBDA_TRACKING_FUNCTION=sarvasahay-tracking-updater

# AWS SNS Topics (replace ACCOUNT_ID with your AWS account ID)
AWS_SNS_TOPIC_ELIGIBILITY=arn:aws:sns:ap-south-1:ACCOUNT_ID:sarvasahay-eligibility
AWS_SNS_TOPIC_APPLICATIONS=arn:aws:sns:ap-south-1:ACCOUNT_ID:sarvasahay-applications
AWS_SNS_TOPIC_ALERTS=arn:aws:sns:ap-south-1:ACCOUNT_ID:sarvasahay-alerts

# AWS SQS Queues (replace ACCOUNT_ID with your AWS account ID)
AWS_SQS_QUEUE_DOCUMENTS=https://sqs.ap-south-1.amazonaws.com/ACCOUNT_ID/sarvasahay-documents
AWS_SQS_QUEUE_ELIGIBILITY=https://sqs.ap-south-1.amazonaws.com/ACCOUNT_ID/sarvasahay-eligibility
AWS_SQS_QUEUE_NOTIFICATIONS=https://sqs.ap-south-1.amazonaws.com/ACCOUNT_ID/sarvasahay-notifications

# AWS DynamoDB Tables
AWS_DYNAMODB_TABLE_SESSIONS=sarvasahay-sessions
AWS_DYNAMODB_TABLE_CACHE=sarvasahay-cache
AWS_DYNAMODB_TABLE_AUDIT=sarvasahay-audit-logs
```

### Method 2: Custom Endpoint URLs (For LocalStack or Custom AWS Endpoints)

If you're using LocalStack for local development or custom AWS endpoints, you can add these to your `.env`:

```bash
# Custom S3 Endpoint (for LocalStack)
AWS_S3_ENDPOINT_URL=http://localhost:4566

# Custom Lambda Endpoint
AWS_LAMBDA_ENDPOINT_URL=http://localhost:4566

# Custom DynamoDB Endpoint
AWS_DYNAMODB_ENDPOINT_URL=http://localhost:4566

# Custom SQS Endpoint
AWS_SQS_ENDPOINT_URL=http://localhost:4566

# Custom SNS Endpoint
AWS_SNS_ENDPOINT_URL=http://localhost:4566
```

## Region-Specific Endpoints

### Common AWS Regions

```bash
# Mumbai, India
AWS_DEFAULT_REGION=ap-south-1

# Singapore
AWS_DEFAULT_REGION=ap-southeast-1

# US East (N. Virginia)
AWS_DEFAULT_REGION=us-east-1

# US West (Oregon)
AWS_DEFAULT_REGION=us-west-2

# Europe (Ireland)
AWS_DEFAULT_REGION=eu-west-1
```

### Update Region in All Services

When changing regions, update these endpoints:

```bash
# API Gateway
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.YOUR-REGION.amazonaws.com

# SNS Topics
AWS_SNS_TOPIC_ELIGIBILITY=arn:aws:sns:YOUR-REGION:ACCOUNT_ID:sarvasahay-eligibility

# SQS Queues
AWS_SQS_QUEUE_DOCUMENTS=https://sqs.YOUR-REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-documents
```

## Code-Level Configuration

### Update S3 Client (shared/utils/aws_s3.py)

To use custom S3 endpoints:

```python
# Add endpoint_url parameter
self.s3_client = boto3.client(
    's3',
    region_name=self.region,
    endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL'),  # Add this line
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
```

### Update Lambda Client (shared/utils/aws_lambda.py)

To use custom Lambda endpoints:

```python
# Add endpoint_url parameter
self.lambda_client = boto3.client(
    'lambda',
    region_name=self.region,
    endpoint_url=os.getenv('AWS_LAMBDA_ENDPOINT_URL'),  # Add this line
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
```

## Docker Compose Configuration

Update `docker-compose.yml` to pass custom endpoints:

```yaml
app:
  environment:
    # ... existing variables ...
    AWS_S3_ENDPOINT_URL: ${AWS_S3_ENDPOINT_URL}
    AWS_LAMBDA_ENDPOINT_URL: ${AWS_LAMBDA_ENDPOINT_URL}
    AWS_DYNAMODB_ENDPOINT_URL: ${AWS_DYNAMODB_ENDPOINT_URL}
    AWS_SQS_ENDPOINT_URL: ${AWS_SQS_ENDPOINT_URL}
    AWS_SNS_ENDPOINT_URL: ${AWS_SNS_ENDPOINT_URL}
```

## Kubernetes Configuration

Update Kubernetes secrets with new endpoints:

```bash
# Update AWS region
kubectl create secret generic aws-config \
  --from-literal=region=YOUR-REGION \
  --from-literal=api-gateway-endpoint=https://your-api-id.execute-api.YOUR-REGION.amazonaws.com \
  --dry-run=client -o yaml | kubectl apply -f -

# Update SNS topics
kubectl create secret generic aws-sns-topics \
  --from-literal=eligibility=arn:aws:sns:YOUR-REGION:ACCOUNT_ID:sarvasahay-eligibility \
  --from-literal=applications=arn:aws:sns:YOUR-REGION:ACCOUNT_ID:sarvasahay-applications \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Testing Endpoint Configuration

### Test S3 Connection

```python
from shared.utils.aws_s3 import get_s3_client

s3_client = get_s3_client()
# This will use the configured endpoint
```

### Test Lambda Connection

```python
from shared.utils.aws_lambda import get_lambda_client

lambda_client = get_lambda_client()
# This will use the configured endpoint
```

### Verify Endpoints

```bash
# Check current AWS configuration
aws configure list

# Test S3 endpoint
aws s3 ls --endpoint-url $AWS_S3_ENDPOINT_URL

# Test Lambda endpoint
aws lambda list-functions --endpoint-url $AWS_LAMBDA_ENDPOINT_URL --region $AWS_DEFAULT_REGION
```

## Common Scenarios

### Scenario 1: Moving from ap-south-1 to us-east-1

1. Update `.env`:
```bash
AWS_DEFAULT_REGION=us-east-1
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

2. Update all ARNs:
```bash
# Find and replace in .env
sed -i 's/ap-south-1/us-east-1/g' .env
```

3. Restart services:
```bash
docker-compose down
docker-compose up -d
```

### Scenario 2: Using LocalStack for Local Development

1. Start LocalStack:
```bash
docker run -d -p 4566:4566 localstack/localstack
```

2. Update `.env`:
```bash
AWS_S3_ENDPOINT_URL=http://localhost:4566
AWS_LAMBDA_ENDPOINT_URL=http://localhost:4566
AWS_DYNAMODB_ENDPOINT_URL=http://localhost:4566
AWS_SQS_ENDPOINT_URL=http://localhost:4566
AWS_SNS_ENDPOINT_URL=http://localhost:4566
AWS_DEFAULT_REGION=us-east-1
```

3. Create local resources:
```bash
# Create S3 buckets
aws --endpoint-url=http://localhost:4566 s3 mb s3://sarvasahay-documents

# Create DynamoDB tables
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name sarvasahay-sessions \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Scenario 3: Using AWS China Regions

```bash
# Beijing Region
AWS_DEFAULT_REGION=cn-north-1
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.cn-north-1.amazonaws.com.cn

# Ningxia Region
AWS_DEFAULT_REGION=cn-northwest-1
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.cn-northwest-1.amazonaws.com.cn
```

## Troubleshooting

### Issue: "Could not connect to the endpoint URL"

**Solution**: Verify the endpoint URL format and region:
```bash
# Check endpoint format
echo $AWS_API_GATEWAY_ENDPOINT

# Verify region matches
echo $AWS_DEFAULT_REGION
```

### Issue: "Access Denied" errors

**Solution**: Ensure IAM permissions include the new region:
```json
{
  "Effect": "Allow",
  "Action": ["s3:*", "lambda:*"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:RequestedRegion": ["ap-south-1", "us-east-1"]
    }
  }
}
```

### Issue: Lambda functions not found

**Solution**: Verify function names and region:
```bash
# List functions in the region
aws lambda list-functions --region $AWS_DEFAULT_REGION

# Update function names in .env if they differ
```

## Best Practices

1. **Use Environment Variables**: Never hardcode endpoints in code
2. **Region Consistency**: Ensure all services use the same region for optimal performance
3. **Endpoint Validation**: Test endpoints before deploying to production
4. **Documentation**: Document any custom endpoint configurations
5. **Monitoring**: Set up CloudWatch alarms for endpoint connectivity issues

## Additional Resources

- [AWS Service Endpoints](https://docs.aws.amazon.com/general/latest/gr/rande.html)
- [Boto3 Configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)
- [LocalStack Documentation](https://docs.localstack.cloud/)
