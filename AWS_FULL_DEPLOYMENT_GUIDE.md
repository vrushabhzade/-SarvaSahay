# 🚀 Deploy SarvaSahay to AWS - Complete Guide

This guide covers deploying both frontend (React) and backend (Python/FastAPI) to AWS.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Route 53   │────────▶│  CloudFront  │                 │
│  │     DNS      │         │     CDN      │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                    ┌──────────────┴──────────────┐          │
│                    │                             │          │
│            ┌───────▼────────┐         ┌─────────▼────────┐ │
│            │   S3 Bucket    │         │   ALB (Load      │ │
│            │   (Frontend)   │         │   Balancer)      │ │
│            │   React App    │         └─────────┬────────┘ │
│            └────────────────┘                   │          │
│                                         ┌───────▼────────┐ │
│                                         │   ECS Fargate  │ │
│                                         │   (Backend)    │ │
│                                         │   FastAPI      │ │
│                                         └───────┬────────┘ │
│                                                 │          │
│                    ┌────────────────────────────┼──────┐   │
│                    │                            │      │   │
│            ┌───────▼────────┐         ┌────────▼──────▼┐  │
│            │   RDS          │         │  ElastiCache  │  │
│            │   PostgreSQL   │         │  Redis        │  │
│            └────────────────┘         └───────────────┘  │
│                                                           │
│            ┌────────────────┐         ┌───────────────┐  │
│            │   S3 Bucket    │         │  CloudWatch   │  │
│            │   (Documents)  │         │  (Monitoring) │  │
│            └────────────────┘         └───────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. AWS Account Setup
- AWS account with appropriate permissions
- AWS CLI installed and configured
- IAM user with admin access (or specific permissions)

### 2. Install Required Tools
```bash
# AWS CLI
# Windows: Download from https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: sudo apt-get install awscli

# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output format (json)

# Docker (for building images)
# Already installed

# Node.js (for frontend build)
# Already installed

# Terraform (optional, for IaC)
choco install terraform  # Windows
# or download from https://www.terraform.io/downloads
```

---

## Deployment Options

### Option 1: AWS Amplify (Easiest for Frontend + Backend)
- **Best for:** Quick deployment with CI/CD
- **Time:** 30 minutes
- **Cost:** ~$50-100/month

### Option 2: S3 + CloudFront (Frontend) + ECS (Backend)
- **Best for:** Production-ready, scalable
- **Time:** 2-3 hours
- **Cost:** ~$100-200/month

### Option 3: Terraform (Infrastructure as Code)
- **Best for:** Reproducible, version-controlled infrastructure
- **Time:** 3-4 hours
- **Cost:** ~$100-200/month

---

## Option 1: AWS Amplify Deployment (Recommended for Quick Start)

### Step 1: Deploy Backend to ECS

#### 1.1 Build and Push Docker Image to ECR

```bash
# Navigate to backend directory
cd -SarvaSahay

# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.ap-south-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name sarvasahay-backend --region ap-south-1

# Build Docker image
docker build -t sarvasahay-backend .

# Tag image
docker tag sarvasahay-backend:latest <your-account-id>.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-backend:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-backend:latest
```

#### 1.2 Create ECS Cluster and Service

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name sarvasahay-cluster --region ap-south-1

# Register task definition (see task-definition.json below)
aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster sarvasahay-cluster \
  --service-name sarvasahay-backend \
  --task-definition sarvasahay-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region ap-south-1
```

### Step 2: Deploy Frontend to S3 + CloudFront

#### 2.1 Build Frontend

```bash
# Navigate to frontend
cd frontend/web-app

# Update API endpoint in .env
echo "REACT_APP_API_URL=https://api.sarvasahay.com" > .env.production

# Build for production
npm run build
```

#### 2.2 Create S3 Bucket and Deploy

```bash
# Create S3 bucket
aws s3 mb s3://sarvasahay-frontend --region ap-south-1

# Enable static website hosting
aws s3 website s3://sarvasahay-frontend --index-document index.html --error-document index.html

# Upload build files
aws s3 sync build/ s3://sarvasahay-frontend --delete

# Make bucket public (for static hosting)
aws s3api put-bucket-policy --bucket sarvasahay-frontend --policy file://s3-bucket-policy.json
```

#### 2.3 Create CloudFront Distribution

```bash
# Create CloudFront distribution (see cloudfront-config.json below)
aws cloudfront create-distribution --distribution-config file://infrastructure/aws/cloudfront-config.json
```

---

## Option 2: Complete AWS Setup with All Services

### Step 1: Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region ap-south-1

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone ap-south-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone ap-south-1b

# Create Internet Gateway
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --vpc-id vpc-xxx --internet-gateway-id igw-xxx

# Create security groups
aws ec2 create-security-group --group-name sarvasahay-alb-sg --description "ALB Security Group" --vpc-id vpc-xxx
aws ec2 create-security-group --group-name sarvasahay-ecs-sg --description "ECS Security Group" --vpc-id vpc-xxx
aws ec2 create-security-group --group-name sarvasahay-rds-sg --description "RDS Security Group" --vpc-id vpc-xxx
```

### Step 2: Create RDS Database

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier sarvasahay-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.7 \
  --master-username sarvasahay \
  --master-user-password <your-secure-password> \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxx \
  --db-subnet-group-name sarvasahay-db-subnet \
  --backup-retention-period 7 \
  --region ap-south-1
```

### Step 3: Create ElastiCache Redis

```bash
# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id sarvasahay-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx \
  --cache-subnet-group-name sarvasahay-cache-subnet \
  --region ap-south-1
```

### Step 4: Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name sarvasahay-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --region ap-south-1

# Create target group
aws elbv2 create-target-group \
  --name sarvasahay-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health \
  --region ap-south-1

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### Step 5: Deploy Backend to ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name sarvasahay-cluster --region ap-south-1

# Register task definition
aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition-complete.json

# Create ECS service with ALB
aws ecs create-service \
  --cluster sarvasahay-cluster \
  --service-name sarvasahay-backend \
  --task-definition sarvasahay-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=sarvasahay-backend,containerPort=8000 \
  --region ap-south-1
```

### Step 6: Deploy Frontend

```bash
# Build frontend with production API URL
cd frontend/web-app
REACT_APP_API_URL=https://api.sarvasahay.com npm run build

# Create S3 bucket
aws s3 mb s3://sarvasahay-frontend-prod --region ap-south-1

# Upload files
aws s3 sync build/ s3://sarvasahay-frontend-prod --delete

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://infrastructure/aws/cloudfront-config.json
```

---

## Option 3: Terraform Deployment (Infrastructure as Code)

### Step 1: Initialize Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply configuration
terraform apply
```

The Terraform files are already created in `infrastructure/terraform/`:
- `main.tf` - Main infrastructure
- `variables.tf` - Configuration variables
- `outputs.tf` - Output values

---

## Configuration Files

### 1. Backend Dockerfile (Already exists in -SarvaSahay/)

### 2. Frontend Build Configuration

Create `frontend/web-app/.env.production`:
```env
REACT_APP_API_URL=https://api.sarvasahay.com
REACT_APP_ENV=production
```

### 3. S3 Bucket Policy

Create `infrastructure/aws/s3-bucket-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::sarvasahay-frontend/*"
    }
  ]
}
```

---

## Post-Deployment Steps

### 1. Configure Domain (Optional)

```bash
# Create Route 53 hosted zone
aws route53 create-hosted-zone --name sarvasahay.com --caller-reference $(date +%s)

# Create A record for frontend
aws route53 change-resource-record-sets --hosted-zone-id Z123456 --change-batch file://route53-frontend.json

# Create A record for backend API
aws route53 change-resource-record-sets --hosted-zone-id Z123456 --change-batch file://route53-backend.json
```

### 2. Configure SSL/TLS

```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name sarvasahay.com \
  --subject-alternative-names *.sarvasahay.com \
  --validation-method DNS \
  --region ap-south-1

# Validate certificate (follow DNS validation instructions)
```

### 3. Update Frontend API URL

After backend is deployed, update the frontend:
```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers --names sarvasahay-alb --query 'LoadBalancers[0].DNSName'

# Update frontend .env.production
echo "REACT_APP_API_URL=https://<alb-dns-name>" > frontend/web-app/.env.production

# Rebuild and redeploy
cd frontend/web-app
npm run build
aws s3 sync build/ s3://sarvasahay-frontend --delete
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

### 4. Configure Environment Variables

Update ECS task definition with production values:
- `DATABASE_URL` - RDS endpoint
- `REDIS_URL` - ElastiCache endpoint
- `AWS_REGION` - ap-south-1
- `S3_BUCKET` - Document storage bucket
- `SECRET_KEY` - Generate secure key

---

## Monitoring and Logging

### 1. CloudWatch Logs

```bash
# View ECS logs
aws logs tail /ecs/sarvasahay-backend --follow

# View application logs
aws logs tail /aws/ecs/sarvasahay --follow
```

### 2. CloudWatch Metrics

```bash
# View ECS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=sarvasahay-backend \
  --start-time 2026-03-07T00:00:00Z \
  --end-time 2026-03-07T23:59:59Z \
  --period 3600 \
  --statistics Average
```

### 3. Set Up Alarms

```bash
# Create CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sarvasahay-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## Cost Estimation

### Development Environment (~$50-80/month)
- ECS Fargate (1 task): ~$15/month
- RDS db.t3.micro: ~$15/month
- ElastiCache t3.micro: ~$12/month
- S3 + CloudFront: ~$5/month
- ALB: ~$20/month
- Data transfer: ~$5/month

### Production Environment (~$200-400/month)
- ECS Fargate (2-4 tasks): ~$60-120/month
- RDS db.t3.small: ~$30/month
- ElastiCache t3.small: ~$25/month
- S3 + CloudFront: ~$20/month
- ALB: ~$20/month
- Data transfer: ~$50/month
- CloudWatch: ~$10/month

---

## Troubleshooting

### Backend not starting
```bash
# Check ECS task logs
aws ecs describe-tasks --cluster sarvasahay-cluster --tasks <task-id>
aws logs tail /ecs/sarvasahay-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition sarvasahay-backend
```

### Frontend not loading
```bash
# Check S3 bucket
aws s3 ls s3://sarvasahay-frontend/

# Check CloudFront distribution
aws cloudfront get-distribution --id E123456

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

### Database connection issues
```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier sarvasahay-db

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx

# Test connection from ECS task
aws ecs execute-command --cluster sarvasahay-cluster --task <task-id> --command "psql -h <rds-endpoint> -U sarvasahay"
```

---

## Security Best Practices

1. **Use Secrets Manager** for sensitive data
2. **Enable VPC Flow Logs** for network monitoring
3. **Configure WAF** on CloudFront and ALB
4. **Enable RDS encryption** at rest
5. **Use IAM roles** instead of access keys
6. **Enable CloudTrail** for audit logging
7. **Configure backup policies** for RDS and S3
8. **Use private subnets** for ECS tasks and RDS

---

## Next Steps

1. Set up CI/CD pipeline with GitHub Actions or AWS CodePipeline
2. Configure auto-scaling for ECS services
3. Set up monitoring dashboards in CloudWatch
4. Configure backup and disaster recovery
5. Implement blue-green deployment strategy
6. Set up staging environment

---

## Quick Reference Commands

```bash
# Deploy backend
cd -SarvaSahay
docker build -t sarvasahay-backend .
docker push <ecr-url>/sarvasahay-backend:latest
aws ecs update-service --cluster sarvasahay-cluster --service sarvasahay-backend --force-new-deployment

# Deploy frontend
cd frontend/web-app
npm run build
aws s3 sync build/ s3://sarvasahay-frontend --delete
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"

# View logs
aws logs tail /ecs/sarvasahay-backend --follow

# Scale service
aws ecs update-service --cluster sarvasahay-cluster --service sarvasahay-backend --desired-count 4
```

---

## Support

For detailed guides, see:
- `AWS_DEPLOYMENT_STEP_BY_STEP.md` - Step-by-step AWS setup
- `DEPLOY_PRODUCTION_ARCHITECTURE.md` - Architecture details
- `infrastructure/terraform/` - Terraform IaC files
- `infrastructure/aws/` - AWS configuration files

Your SarvaSahay platform is ready for AWS deployment! 🚀
