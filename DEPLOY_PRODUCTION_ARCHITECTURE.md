# Deploy SarvaSahay with Production AWS Architecture

This guide deploys your SarvaSahay platform with the complete AWS architecture shown in your diagram.

## 🏗️ Architecture Overview

Your deployment will include:

```
Git Repository (GitHub/GitLab)
    ↓
CI/CD Pipeline (GitHub Actions/GitLab CI)
    ↓
AWS Infrastructure:
├── Application Layer
│   ├── Application Load Balancer (ALB)
│   ├── ECS Fargate Cluster
│   ├── Auto Scaling (2-10 tasks)
│   └── CloudWatch Monitoring
├── Data Layer
│   ├── RDS PostgreSQL (Multi-AZ)
│   ├── ElastiCache Redis
│   └── S3 Buckets (Documents, ML Models, Backups)
├── Processing Layer
│   ├── Lambda Functions (Eligibility, OCR, Notifications)
│   ├── SQS Queues (Async processing)
│   └── SNS Topics (Notifications)
└── Security & Monitoring
    ├── CloudWatch Logs & Metrics
    ├── CloudWatch Alarms
    ├── AWS Secrets Manager
    └── IAM Roles & Policies
```

---

## 📋 Prerequisites

1. **AWS Account** with admin access
2. **AWS CLI** configured
3. **Docker** installed
4. **Terraform** installed (optional, for IaC)
5. **Git** repository for your code

---

## 🚀 Deployment Options

Choose the method that best fits your needs:

### Option 1: Automated Terraform Deployment (Recommended)
### Option 2: AWS Copilot (Easiest)
### Option 3: Manual AWS Console Setup

---

## Option 1: Terraform Deployment (Complete Architecture)

This creates the EXACT architecture from your diagram.

### Step 1: Prepare Your Environment

```powershell
# 1. Configure AWS credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Region: ap-south-1 (Mumbai, India)
# Output format: json

# 2. Verify AWS access
aws sts get-caller-identity

# 3. Get your AWS Account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
Write-Host "AWS Account ID: $ACCOUNT_ID"
```

### Step 2: Create S3 Bucket for Terraform State

```powershell
# Create S3 bucket for Terraform state (one-time setup)
aws s3 mb s3://sarvasahay-terraform-state --region ap-south-1

# Enable versioning
aws s3api put-bucket-versioning `
  --bucket sarvasahay-terraform-state `
  --versioning-configuration Status=Enabled `
  --region ap-south-1

# Enable encryption
aws s3api put-bucket-encryption `
  --bucket sarvasahay-terraform-state `
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }' `
  --region ap-south-1
```

### Step 3: Configure Terraform Variables

```powershell
# Navigate to terraform directory
cd infrastructure/terraform

# Create terraform.tfvars file
@"
# AWS Configuration
aws_region = "ap-south-1"
environment = "production"
app_name = "sarvasahay"

# Container Configuration
container_image = "$ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest"
container_port = 8000

# Scaling Configuration
desired_count = 2
min_capacity = 2
max_capacity = 10

# Task Resources
task_cpu = 1024      # 1 vCPU
task_memory = 2048   # 2 GB

# Database Configuration
db_instance_class = "db.t3.small"
db_allocated_storage = 20
db_password = "CHANGE_THIS_SECURE_PASSWORD"

# Redis Configuration
redis_node_type = "cache.t3.micro"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
"@ | Out-File -FilePath terraform.tfvars -Encoding UTF8
```

### Step 4: Build and Push Docker Image

```powershell
# Go back to project root
cd ../..

# Build Docker image
docker build -t sarvasahay-production:latest .

# Create ECR repository
aws ecr create-repository `
  --repository-name sarvasahay-production `
  --region ap-south-1

# Login to ECR
aws ecr get-login-password --region ap-south-1 | `
  docker login --username AWS --password-stdin `
  $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# Tag image
docker tag sarvasahay-production:latest `
  $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest

# Push image
docker push $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest
```

### Step 5: Deploy Infrastructure with Terraform

```powershell
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure (takes 10-15 minutes)
terraform apply

# Type 'yes' when prompted
```

**What Terraform Creates:**
- ✅ VPC with public/private subnets across 2 AZs
- ✅ Application Load Balancer
- ✅ ECS Fargate Cluster
- ✅ ECS Service with auto-scaling (2-10 tasks)
- ✅ RDS PostgreSQL (Multi-AZ for high availability)
- ✅ ElastiCache Redis cluster
- ✅ S3 buckets (documents, ML models, backups)
- ✅ CloudWatch Log Groups
- ✅ CloudWatch Alarms (CPU, Memory)
- ✅ IAM Roles and Security Groups
- ✅ Auto-scaling policies

### Step 6: Get Deployment Outputs

```powershell
# Get all outputs
terraform output

# Get specific outputs
$ALB_DNS = terraform output -raw alb_dns_name
$ECR_URL = terraform output -raw ecr_repository_url
$RDS_ENDPOINT = terraform output -raw rds_endpoint
$REDIS_ENDPOINT = terraform output -raw redis_endpoint

Write-Host "Application URL: http://$ALB_DNS"
Write-Host "API Documentation: http://$ALB_DNS/docs"
```

### Step 7: Configure Secrets in AWS Secrets Manager

```powershell
# Store database credentials
aws secretsmanager create-secret `
  --name sarvasahay/database-url `
  --secret-string "postgresql://sarvasahay:YOUR_PASSWORD@$RDS_ENDPOINT:5432/sarvasahay" `
  --region ap-south-1

# Store Redis URL
aws secretsmanager create-secret `
  --name sarvasahay/redis-url `
  --secret-string "redis://$REDIS_ENDPOINT:6379/0" `
  --region ap-south-1

# Store application secret key
aws secretsmanager create-secret `
  --name sarvasahay/secret-key `
  --secret-string (New-Guid).ToString() `
  --region ap-south-1

# Store encryption key
aws secretsmanager create-secret `
  --name sarvasahay/encryption-key `
  --secret-string (New-Guid).ToString() `
  --region ap-south-1
```

### Step 8: Verify Deployment

```powershell
# Check ECS service status
aws ecs describe-services `
  --cluster sarvasahay-production-cluster `
  --services sarvasahay-production-app `
  --region ap-south-1 `
  --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}"

# Check ALB target health
aws elbv2 describe-target-health `
  --target-group-arn (terraform output -raw target_group_arn) `
  --region ap-south-1

# Test application
curl "http://$ALB_DNS"
curl "http://$ALB_DNS/docs"
```

---

## Option 2: AWS Copilot Deployment (Simplified)

AWS Copilot automatically creates a similar architecture with less configuration.

### Step 1: Install Copilot

```powershell
# Download Copilot CLI
Invoke-WebRequest -OutFile copilot.exe `
  https://github.com/aws/copilot-cli/releases/latest/download/copilot-windows.exe

# Move to Program Files
Move-Item copilot.exe "$env:ProgramFiles\copilot.exe"
```

### Step 2: Initialize and Deploy

```bash
# Initialize application
copilot app init sarvasahay-platform

# Create production environment
copilot env init --name production --profile default --default-config

# Deploy environment infrastructure
copilot env deploy --name production

# Create load-balanced web service
copilot svc init --name app \
  --svc-type "Load Balanced Web Service" \
  --dockerfile ./Dockerfile \
  --port 8000

# Deploy service
copilot svc deploy --name app --env production

# Add database
copilot storage init --name sarvasahay-db \
  --storage-type Aurora \
  --engine PostgreSQL \
  --initial-db sarvasahay

# Add Redis
copilot storage init --name sarvasahay-cache \
  --storage-type Redis

# Get service URL
copilot svc show --name app
```

---

## Post-Deployment Configuration

### 1. Set Up Custom Domain (Optional)

```powershell
# Create Route53 hosted zone
aws route53 create-hosted-zone `
  --name sarvasahay.gov.in `
  --caller-reference (Get-Date -Format "yyyyMMddHHmmss")

# Get ALB DNS
$ALB_DNS = terraform output -raw alb_dns_name

# Create CNAME record
aws route53 change-resource-record-sets `
  --hosted-zone-id YOUR_HOSTED_ZONE_ID `
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "sarvasahay.gov.in",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
      }
    }]
  }'
```

### 2. Enable HTTPS with SSL Certificate

```powershell
# Request SSL certificate
aws acm request-certificate `
  --domain-name sarvasahay.gov.in `
  --validation-method DNS `
  --region ap-south-1

# Get certificate ARN
$CERT_ARN = aws acm list-certificates `
  --query "CertificateSummaryList[?DomainName=='sarvasahay.gov.in'].CertificateArn" `
  --output text

# Add HTTPS listener to ALB
aws elbv2 create-listener `
  --load-balancer-arn (terraform output -raw alb_arn) `
  --protocol HTTPS `
  --port 443 `
  --certificates CertificateArn=$CERT_ARN `
  --default-actions Type=forward,TargetGroupArn=(terraform output -raw target_group_arn) `
  --region ap-south-1
```

### 3. Set Up CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: sarvasahay-production
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster sarvasahay-production-cluster \
            --service sarvasahay-production-app \
            --force-new-deployment \
            --region ap-south-1
```

### 4. Configure Monitoring and Alerts

```powershell
# Create CloudWatch dashboard
aws cloudwatch put-dashboard `
  --dashboard-name SarvaSahay-Production `
  --dashboard-body (Get-Content infrastructure/monitoring/dashboard.json -Raw) `
  --region ap-south-1

# Set up SNS topic for alerts
aws sns create-topic --name sarvasahay-alerts --region ap-south-1

# Subscribe email to alerts
aws sns subscribe `
  --topic-arn arn:aws:sns:ap-south-1:$ACCOUNT_ID:sarvasahay-alerts `
  --protocol email `
  --notification-endpoint your-email@example.com `
  --region ap-south-1

# Create high CPU alarm
aws cloudwatch put-metric-alarm `
  --alarm-name sarvasahay-high-cpu `
  --alarm-description "Alert when CPU exceeds 80%" `
  --metric-name CPUUtilization `
  --namespace AWS/ECS `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 2 `
  --alarm-actions arn:aws:sns:ap-south-1:$ACCOUNT_ID:sarvasahay-alerts `
  --dimensions Name=ClusterName,Value=sarvasahay-production-cluster Name=ServiceName,Value=sarvasahay-production-app `
  --region ap-south-1
```

---

## 📊 Architecture Verification

### Check All Components

```powershell
# 1. VPC and Networking
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=SarvaSahay" --region ap-south-1

# 2. Load Balancer
aws elbv2 describe-load-balancers --region ap-south-1

# 3. ECS Cluster and Service
aws ecs describe-clusters --clusters sarvasahay-production-cluster --region ap-south-1
aws ecs describe-services --cluster sarvasahay-production-cluster --services sarvasahay-production-app --region ap-south-1

# 4. RDS Database
aws rds describe-db-instances --region ap-south-1

# 5. ElastiCache Redis
aws elasticache describe-cache-clusters --region ap-south-1

# 6. S3 Buckets
aws s3 ls | Select-String sarvasahay

# 7. Lambda Functions (if deployed)
aws lambda list-functions --region ap-south-1

# 8. CloudWatch Logs
aws logs describe-log-groups --log-group-name-prefix /ecs/sarvasahay --region ap-south-1
```

---

## 🎯 Testing Your Deployment

```powershell
# Get ALB URL
$ALB_URL = terraform output -raw alb_dns_name

# Test welcome endpoint
curl "http://$ALB_URL"

# Test API documentation
Start-Process "http://$ALB_URL/docs"

# Test health endpoint
curl "http://$ALB_URL/api/v1/health"

# Test eligibility check (example)
curl -X POST "http://$ALB_URL/api/v1/eligibility/check" `
  -H "Content-Type: application/json" `
  -d '{
    "age": 25,
    "income": 50000,
    "state": "Maharashtra",
    "occupation": "farmer"
  }'
```

---

## 💰 Cost Estimate

### Production Environment (ap-south-1 - Mumbai)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 2-10 tasks, 1 vCPU, 2GB | $120-600 |
| RDS PostgreSQL | db.t3.small, Multi-AZ | $60 |
| ElastiCache Redis | cache.t3.micro | $12 |
| Application Load Balancer | Standard | $20 |
| S3 Storage | 100GB | $3 |
| Data Transfer | 500GB | $45 |
| CloudWatch | Logs & Metrics | $10 |
| **Total** | | **$270-750/month** |

**Note:** Costs scale with usage. Start with minimum configuration and scale up as needed.

---

## 🔄 Updating Your Deployment

```powershell
# Update application code
git push origin main  # Triggers CI/CD

# Or manual update
docker build -t sarvasahay-production:latest .
docker tag sarvasahay-production:latest $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest
docker push $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest

# Force new deployment
aws ecs update-service `
  --cluster sarvasahay-production-cluster `
  --service sarvasahay-production-app `
  --force-new-deployment `
  --region ap-south-1
```

---

## 🗑️ Clean Up (Delete Everything)

```powershell
# With Terraform
cd infrastructure/terraform
terraform destroy

# Confirm with 'yes'

# Delete ECR images
aws ecr batch-delete-image `
  --repository-name sarvasahay-production `
  --image-ids imageTag=latest `
  --region ap-south-1

# Delete ECR repository
aws ecr delete-repository `
  --repository-name sarvasahay-production `
  --force `
  --region ap-south-1
```

---

## 📚 Next Steps

1. ✅ Set up monitoring dashboards
2. ✅ Configure backup policies
3. ✅ Implement blue-green deployment
4. ✅ Set up disaster recovery
5. ✅ Add WAF for security
6. ✅ Configure CloudFront CDN
7. ✅ Set up multi-region failover

---

## 🆘 Troubleshooting

See `TROUBLESHOOTING.md` for common issues and solutions.

---

**Your SarvaSahay platform is now deployed with production-grade AWS architecture!** 🎉
