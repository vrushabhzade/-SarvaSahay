# AWS Lambda Deployment Guide for SarvaSahay Platform

## Prerequisites

### 1. AWS CLI Configuration
Ensure AWS CLI is properly configured with valid credentials:

```powershell
# Configure AWS CLI
aws configure

# Enter your credentials:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: ap-south-1
# Default output format: json
```

### 2. Verify AWS Credentials
```powershell
# Test credentials
aws sts get-caller-identity

# Should return your account information
```

### 3. Create IAM Roles

Before deploying Lambda functions, create the required IAM roles in AWS Console:

#### Eligibility Engine Role
- Role name: `sarvasahay-eligibility-lambda-role`
- Permissions:
  - AWSLambdaBasicExecutionRole
  - AmazonS3ReadOnlyAccess (for ML models)
  - AmazonDynamoDBReadOnlyAccess (for scheme data)

#### Document Processor Role
- Role name: `sarvasahay-document-lambda-role`
- Permissions:
  - AWSLambdaBasicExecutionRole
  - AmazonS3FullAccess (for document storage)
  - AmazonTextractFullAccess (for OCR)
  - AmazonRekognitionReadOnlyAccess (for validation)

#### OCR Processor Role
- Role name: `sarvasahay-ocr-lambda-role`
- Permissions:
  - AWSLambdaBasicExecutionRole
  - AmazonTextractFullAccess
  - AmazonS3ReadOnlyAccess

#### Notification Handler Role
- Role name: `sarvasahay-notification-lambda-role`
- Permissions:
  - AWSLambdaBasicExecutionRole
  - AmazonSNSFullAccess (for notifications)
  - AmazonSQSFullAccess (for message queues)

#### Tracking Updater Role
- Role name: `sarvasahay-tracking-lambda-role`
- Permissions:
  - AWSLambdaBasicExecutionRole
  - AmazonDynamoDBFullAccess (for tracking data)
  - AmazonSQSFullAccess (for message queues)

### 4. Create S3 Buckets

```powershell
# Create S3 buckets
aws s3 mb s3://sarvasahay-documents --region ap-south-1
aws s3 mb s3://sarvasahay-ml-models --region ap-south-1
aws s3 mb s3://sarvasahay-backups --region ap-south-1

# Enable encryption
aws s3api put-bucket-encryption `
    --bucket sarvasahay-documents `
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

### 5. Create Lambda Function Directories

The deployment script expects the following directory structure:

```
services/
├── eligibility_engine/
│   ├── lambda_function.py
│   └── requirements.txt
├── document_processor/
│   ├── lambda_function.py
│   └── requirements.txt
├── ocr_processor/
│   ├── lambda_function.py
│   └── requirements.txt
├── notification_handler/
│   ├── lambda_function.py
│   └── requirements.txt
└── tracking_updater/
    ├── lambda_function.py
    └── requirements.txt
```

## Deployment

### Option 1: Deploy All Functions

```powershell
# Set your AWS Account ID
$env:AWS_ACCOUNT_ID="334931733930"

# Run deployment script
.\infrastructure\lambda\deploy-lambda.ps1
```

### Option 2: Deploy Individual Functions

```powershell
# Deploy eligibility engine only
aws lambda create-function `
    --function-name sarvasahay-eligibility-engine `
    --runtime python3.11 `
    --role arn:aws:iam::334931733930:role/sarvasahay-eligibility-lambda-role `
    --handler lambda_function.lambda_handler `
    --zip-file fileb://eligibility-engine.zip `
    --memory-size 3008 `
    --timeout 300 `
    --region ap-south-1
```

## Testing Lambda Functions

### Test Eligibility Engine

```powershell
# Create test payload
$payload = @{
    user_profile = @{
        age = 35
        gender = "male"
        caste = "obc"
        annual_income = 50000
        land_ownership = 2.5
    }
} | ConvertTo-Json

# Invoke function
aws lambda invoke `
    --function-name sarvasahay-eligibility-engine `
    --payload $payload `
    --region ap-south-1 `
    response.json

# View response
Get-Content response.json
```

### Test Document Processor

```powershell
$payload = @{
    document = @{
        s3_bucket = "sarvasahay-documents"
        s3_key = "documents/user123/aadhaar.jpg"
        document_type = "aadhaar"
    }
} | ConvertTo-Json

aws lambda invoke `
    --function-name sarvasahay-document-processor `
    --payload $payload `
    --region ap-south-1 `
    response.json
```

## Monitoring

### View Lambda Logs

```powershell
# View recent logs
aws logs tail /aws/lambda/sarvasahay-eligibility-engine --follow
```

### Check Function Metrics

```powershell
# Get function configuration
aws lambda get-function --function-name sarvasahay-eligibility-engine

# Get function metrics
aws cloudwatch get-metric-statistics `
    --namespace AWS/Lambda `
    --metric-name Duration `
    --dimensions Name=FunctionName,Value=sarvasahay-eligibility-engine `
    --start-time 2024-01-01T00:00:00Z `
    --end-time 2024-01-02T00:00:00Z `
    --period 3600 `
    --statistics Average
```

## Troubleshooting

### Issue: Signature Does Not Match Error

This means your AWS credentials are incorrect or expired.

**Solution:**
```powershell
# Reconfigure AWS CLI
aws configure

# Or check your credentials file
notepad $env:USERPROFILE\.aws\credentials
```

### Issue: Access Denied

Your IAM user doesn't have permission to create Lambda functions.

**Solution:**
Add the following policy to your IAM user:
- AWSLambda_FullAccess
- IAMReadOnlyAccess

### Issue: Role Does Not Exist

The IAM role for the Lambda function hasn't been created.

**Solution:**
Create the required IAM roles in AWS Console (see Prerequisites section).

### Issue: Function Already Exists

The Lambda function already exists and you're trying to create it again.

**Solution:**
Use update instead of create:
```powershell
aws lambda update-function-code `
    --function-name sarvasahay-eligibility-engine `
    --zip-file fileb://eligibility-engine.zip
```

## Next Steps

1. Create Lambda function code in the service directories
2. Set up API Gateway to expose Lambda functions
3. Configure SQS queues for async processing
4. Set up CloudWatch alarms for monitoring
5. Configure VPC for secure database access

## Useful Commands

```powershell
# List all Lambda functions
aws lambda list-functions --region ap-south-1

# Delete a Lambda function
aws lambda delete-function --function-name sarvasahay-eligibility-engine

# Update function configuration
aws lambda update-function-configuration `
    --function-name sarvasahay-eligibility-engine `
    --memory-size 4096 `
    --timeout 600

# Add environment variables
aws lambda update-function-configuration `
    --function-name sarvasahay-eligibility-engine `
    --environment "Variables={ML_MODEL_PATH=/opt/ml/models,DEBUG=true}"
```

## Cost Estimation

Based on the configuration:
- Eligibility Engine: ~$0.20 per 1000 invocations
- Document Processor: ~$0.15 per 1000 invocations
- OCR Processor: ~$0.10 per 1000 invocations
- Notification Handler: ~$0.05 per 1000 invocations
- Tracking Updater: ~$0.08 per 1000 invocations

Plus AWS Textract costs: ~$1.50 per 1000 pages

## Support

For issues or questions:
- Check AWS Lambda documentation: https://docs.aws.amazon.com/lambda/
- Review CloudWatch logs for errors
- Contact the SarvaSahay development team
