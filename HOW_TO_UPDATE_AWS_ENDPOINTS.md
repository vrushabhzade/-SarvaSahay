# How to Update AWS Endpoints in SarvaSahay Platform

## 📋 Quick Reference

Your platform has built-in tools to easily update AWS endpoints. Here are all the ways to do it:

---

## Method 1: Using the Update Script (Recommended) ⚡

### View Current Configuration

```powershell
python scripts/update_aws_endpoints.py show
```

This shows all your current AWS settings including region, buckets, Lambda functions, etc.

---

### Common Update Scenarios

#### 1. Change AWS Region

When moving from one region to another (e.g., Mumbai to Singapore):

```powershell
# Change region (updates all ARNs and endpoints automatically)
python scripts/update_aws_endpoints.py region ap-southeast-1

# Common regions:
# ap-south-1      - Mumbai, India
# ap-southeast-1  - Singapore
# us-east-1       - N. Virginia, USA
# us-west-2       - Oregon, USA
# eu-west-1       - Ireland, Europe
```

**What this updates:**
- AWS_DEFAULT_REGION
- API Gateway endpoint
- SNS topic ARNs
- SQS queue URLs

---

#### 2. Update API Gateway Endpoint

After deploying your API Gateway:

```powershell
# Update with your API Gateway ID
python scripts/update_aws_endpoints.py api-gateway abc123xyz

# With specific region
python scripts/update_aws_endpoints.py api-gateway abc123xyz --region ap-south-1
```

**Example:**
```powershell
# If your API Gateway URL is:
# https://xyz789abc.execute-api.ap-south-1.amazonaws.com
# Then your API ID is: xyz789abc

python scripts/update_aws_endpoints.py api-gateway xyz789abc
```

---

#### 3. Update S3 Bucket Names

After creating your S3 buckets:

```powershell
python scripts/update_aws_endpoints.py s3 \
  --documents sarvasahay-prod-documents \
  --ml-models sarvasahay-prod-ml-models \
  --backups sarvasahay-prod-backups
```

**Real example:**
```powershell
python scripts/update_aws_endpoints.py s3 `
  --documents sarvasahay-production-documents `
  --ml-models sarvasahay-production-ml-models `
  --backups sarvasahay-production-backups
```

---

#### 4. Switch to LocalStack (Development)

For local development with LocalStack:

```powershell
# Enable LocalStack endpoints
python scripts/update_aws_endpoints.py localstack --enable

# Disable LocalStack (switch back to real AWS)
python scripts/update_aws_endpoints.py localstack --disable
```

**What this does:**
- Sets all endpoint URLs to http://localhost:4566
- Changes region to us-east-1 (LocalStack default)
- Keeps your bucket/function names unchanged

---

## Method 2: Manual .env File Updates

If you prefer direct editing:

### 1. Open .env File

```powershell
notepad .env
# or
code .env
```

### 2. Update Specific Values

#### Change Region
```bash
AWS_DEFAULT_REGION=ap-south-1
```

#### Update S3 Buckets
```bash
AWS_S3_BUCKET_DOCUMENTS=your-documents-bucket
AWS_S3_BUCKET_ML_MODELS=your-ml-models-bucket
AWS_S3_BUCKET_BACKUPS=your-backups-bucket
```

#### Update API Gateway
```bash
AWS_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.ap-south-1.amazonaws.com
AWS_API_GATEWAY_STAGE=prod
```

#### Update Lambda Functions
```bash
AWS_LAMBDA_ELIGIBILITY_FUNCTION=sarvasahay-eligibility-engine
AWS_LAMBDA_DOCUMENT_PROCESSOR=sarvasahay-document-processor
AWS_LAMBDA_OCR_FUNCTION=sarvasahay-ocr-processor
```

#### Update SNS Topics (Replace ACCOUNT_ID and REGION)
```bash
AWS_SNS_TOPIC_ELIGIBILITY=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-eligibility
AWS_SNS_TOPIC_APPLICATIONS=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-applications
AWS_SNS_TOPIC_ALERTS=arn:aws:sns:REGION:ACCOUNT_ID:sarvasahay-alerts
```

#### Update SQS Queues (Replace ACCOUNT_ID and REGION)
```bash
AWS_SQS_QUEUE_DOCUMENTS=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-documents
AWS_SQS_QUEUE_ELIGIBILITY=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-eligibility
AWS_SQS_QUEUE_NOTIFICATIONS=https://sqs.REGION.amazonaws.com/ACCOUNT_ID/sarvasahay-notifications
```

### 3. Save and Restart Services

```powershell
docker-compose down
docker-compose up -d
```

---

## Method 3: After AWS Deployment

### After Deploying with Terraform

```powershell
# Get outputs from Terraform
cd infrastructure/terraform
terraform output

# Update .env with the outputs
# Example outputs:
# alb_dns_name = "sarvasahay-alb-123456.ap-south-1.elb.amazonaws.com"
# s3_bucket_documents = "sarvasahay-production-documents"
# rds_endpoint = "sarvasahay-db.abc123.ap-south-1.rds.amazonaws.com"

# Update your .env file with these values
```

### After Deploying with AWS Copilot

```bash
# Get service information
copilot svc show --name app

# Update .env with the service URL and resource names
```

### After Manual AWS Deployment

```powershell
# Get ALB DNS name
aws elbv2 describe-load-balancers --query "LoadBalancers[0].DNSName" --output text

# Get RDS endpoint
aws rds describe-db-instances --query "DBInstances[0].Endpoint.Address" --output text

# Get ElastiCache endpoint
aws elasticache describe-cache-clusters --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text

# Get S3 bucket names
aws s3 ls | grep sarvasahay

# Update .env with these values
```

---

## Complete Configuration Example

Here's a complete real-world example after AWS deployment:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012

# S3 Buckets (from Terraform output or AWS Console)
AWS_S3_BUCKET_DOCUMENTS=sarvasahay-production-documents
AWS_S3_BUCKET_ML_MODELS=sarvasahay-production-ml-models
AWS_S3_BUCKET_BACKUPS=sarvasahay-production-backups

# Lambda Functions (from deployment)
AWS_LAMBDA_ELIGIBILITY_FUNCTION=sarvasahay-prod-eligibility-engine
AWS_LAMBDA_DOCUMENT_PROCESSOR=sarvasahay-prod-document-processor
AWS_LAMBDA_OCR_FUNCTION=sarvasahay-prod-ocr-processor

# API Gateway (from AWS Console or Terraform)
AWS_API_GATEWAY_ENDPOINT=https://xyz789abc.execute-api.ap-south-1.amazonaws.com
AWS_API_GATEWAY_STAGE=prod

# SNS Topics (replace with your account ID)
AWS_SNS_TOPIC_ELIGIBILITY=arn:aws:sns:ap-south-1:123456789012:sarvasahay-eligibility
AWS_SNS_TOPIC_APPLICATIONS=arn:aws:sns:ap-south-1:123456789012:sarvasahay-applications
AWS_SNS_TOPIC_ALERTS=arn:aws:sns:ap-south-1:123456789012:sarvasahay-alerts

# SQS Queues (replace with your account ID)
AWS_SQS_QUEUE_DOCUMENTS=https://sqs.ap-south-1.amazonaws.com/123456789012/sarvasahay-documents
AWS_SQS_QUEUE_ELIGIBILITY=https://sqs.ap-south-1.amazonaws.com/123456789012/sarvasahay-eligibility
AWS_SQS_QUEUE_NOTIFICATIONS=https://sqs.ap-south-1.amazonaws.com/123456789012/sarvasahay-notifications

# Database (from RDS deployment)
DATABASE_URL=postgresql://sarvasahay:PASSWORD@sarvasahay-db.abc123.ap-south-1.rds.amazonaws.com:5432/sarvasahay

# Redis (from ElastiCache deployment)
REDIS_URL=redis://sarvasahay-cache.abc123.0001.aps1.cache.amazonaws.com:6379/0
```

---

## Verification Steps

### 1. Test Configuration

```powershell
# Run the test script
python scripts/test_aws_config.py
```

This will verify:
- ✅ Environment variables are set
- ✅ S3 connection works
- ✅ Lambda connection works
- ✅ S3 upload/download operations

### 2. Check Service Connectivity

```powershell
# Test S3 access
aws s3 ls s3://sarvasahay-documents --region ap-south-1

# Test Lambda functions
aws lambda list-functions --region ap-south-1

# Test RDS connectivity (from within your app)
docker-compose exec app python -c "from shared.database.models import Base; print('DB OK')"
```

### 3. Verify Application

```powershell
# Check application logs
docker-compose logs -f app

# Test health endpoint
curl http://localhost:8000/health

# Test API endpoint
curl http://localhost:8000/api/v1/health
```

---

## Common Scenarios

### Scenario 1: Moving from LocalStack to Real AWS

```powershell
# 1. Disable LocalStack
python scripts/update_aws_endpoints.py localstack --disable

# 2. Update region
python scripts/update_aws_endpoints.py region ap-south-1

# 3. Update S3 buckets (with your real bucket names)
python scripts/update_aws_endpoints.py s3 `
  --documents sarvasahay-prod-documents `
  --ml-models sarvasahay-prod-ml-models `
  --backups sarvasahay-prod-backups

# 4. Update credentials in .env
# AWS_ACCESS_KEY_ID=your-real-key
# AWS_SECRET_ACCESS_KEY=your-real-secret

# 5. Restart services
docker-compose down
docker-compose up -d

# 6. Test
python scripts/test_aws_config.py
```

---

### Scenario 2: Switching Regions

```powershell
# 1. Update region (this updates all ARNs automatically)
python scripts/update_aws_endpoints.py region us-east-1

# 2. Update API Gateway if you have one in the new region
python scripts/update_aws_endpoints.py api-gateway NEW-API-ID --region us-east-1

# 3. Restart services
docker-compose down
docker-compose up -d
```

---

### Scenario 3: After Terraform Deployment

```powershell
# 1. Deploy with Terraform
cd infrastructure/terraform
terraform apply

# 2. Get outputs
terraform output -json > outputs.json

# 3. Update endpoints using the script or manually
# Get values from outputs.json and update .env

# 4. Restart services
cd ../..
docker-compose down
docker-compose up -d
```

---

## Troubleshooting

### Issue: "Could not connect to endpoint"

```powershell
# Check current configuration
python scripts/update_aws_endpoints.py show

# Verify AWS credentials
aws sts get-caller-identity

# Test endpoint manually
curl http://localhost:4566/_localstack/health  # For LocalStack
```

### Issue: "Access Denied"

```powershell
# Check IAM permissions
aws iam get-user

# Verify credentials in .env
cat .env | Select-String AWS_ACCESS_KEY_ID

# Test with AWS CLI
aws s3 ls --region ap-south-1
```

### Issue: "Bucket does not exist"

```powershell
# List available buckets
aws s3 ls --region ap-south-1

# Create missing bucket
aws s3 mb s3://your-bucket-name --region ap-south-1

# Update .env with correct bucket name
```

---

## Best Practices

1. **Always backup .env before changes**
   ```powershell
   Copy-Item .env .env.backup
   ```

2. **Use the update script when possible**
   - It handles ARN updates automatically
   - Validates configuration
   - Less error-prone

3. **Test after every change**
   ```powershell
   python scripts/test_aws_config.py
   ```

4. **Restart services after updates**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

5. **Keep LocalStack for development**
   - Use LocalStack for local testing
   - Switch to real AWS for staging/production

6. **Document your endpoints**
   - Keep a record of your AWS resource names
   - Document region choices
   - Note any custom configurations

---

## Quick Command Reference

```powershell
# Show current config
python scripts/update_aws_endpoints.py show

# Change region
python scripts/update_aws_endpoints.py region REGION_NAME

# Update API Gateway
python scripts/update_aws_endpoints.py api-gateway API_ID

# Update S3 buckets
python scripts/update_aws_endpoints.py s3 --documents BUCKET1 --ml-models BUCKET2 --backups BUCKET3

# Enable LocalStack
python scripts/update_aws_endpoints.py localstack --enable

# Disable LocalStack
python scripts/update_aws_endpoints.py localstack --disable

# Test configuration
python scripts/test_aws_config.py

# Restart services
docker-compose down; docker-compose up -d
```

---

## Need Help?

- **Full AWS Setup Guide**: `AWS_SETUP_GUIDE.md`
- **Quick AWS Updates**: `QUICK_AWS_ENDPOINT_UPDATE.md`
- **Deployment Guide**: `AWS_DEPLOYMENT_QUICKSTART.md`
- **Configuration Details**: `docs/AWS_ENDPOINT_CONFIGURATION.md`

---

**Pro Tip**: Use `python scripts/update_aws_endpoints.py show` frequently to verify your current configuration! 🚀
