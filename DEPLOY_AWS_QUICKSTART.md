# 🚀 AWS Deployment - Quick Start Guide

Deploy SarvaSahay to AWS in 3 simple steps.

---

## Prerequisites (5 minutes)

### 1. Install AWS CLI
```bash
# Windows (PowerShell as Administrator)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version
```

### 2. Configure AWS Credentials
```bash
aws configure
```
Enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `ap-south-1` (Mumbai, India)
- **Default output format**: `json`

### 3. Verify Docker is Running
```bash
docker ps
```

---

## Deployment Steps

### Option A: Automated Deployment (Recommended)

```powershell
# Run the automated deployment script
.\deploy-to-aws-complete.ps1
```

This script will:
1. ✅ Build and push backend Docker image to ECR
2. ✅ Create ECS cluster and register task definition
3. ✅ Build frontend React app
4. ✅ Upload frontend to S3
5. ✅ Configure static website hosting
6. ✅ Provide deployment URLs

**Time:** ~15-20 minutes

---

### Option B: Manual Deployment

#### Step 1: Deploy Backend (10 minutes)

```bash
# 1. Get your AWS account ID
aws sts get-caller-identity --query Account --output text

# 2. Create ECR repository
aws ecr create-repository --repository-name sarvasahay-backend --region ap-south-1

# 3. Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com

# 4. Build Docker image
cd -SarvaSahay
docker build -t sarvasahay-backend .

# 5. Tag and push image
docker tag sarvasahay-backend:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-backend:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-backend:latest

# 6. Create ECS cluster
aws ecs create-cluster --cluster-name sarvasahay-cluster --region ap-south-1
```

#### Step 2: Deploy Frontend (5 minutes)

```bash
# 1. Build frontend
cd frontend/web-app
npm run build

# 2. Create S3 bucket
aws s3 mb s3://sarvasahay-frontend --region ap-south-1

# 3. Enable static website hosting
aws s3 website s3://sarvasahay-frontend --index-document index.html --error-document index.html

# 4. Upload files
aws s3 sync build/ s3://sarvasahay-frontend --delete

# 5. Make bucket public
aws s3api put-bucket-policy --bucket sarvasahay-frontend --policy file://../../infrastructure/aws/s3-bucket-policy.json

# 6. Get website URL
echo "Frontend URL: http://sarvasahay-frontend.s3-website.ap-south-1.amazonaws.com"
```

---

## Verify Deployment

### Backend
```bash
# Check ECR repository
aws ecr describe-repositories --repository-names sarvasahay-backend --region ap-south-1

# Check ECS cluster
aws ecs describe-clusters --clusters sarvasahay-cluster --region ap-south-1
```

### Frontend
```bash
# Check S3 bucket
aws s3 ls s3://sarvasahay-frontend/

# Test website
curl http://sarvasahay-frontend.s3-website.ap-south-1.amazonaws.com
```

---

## Access Your Application

### Frontend URL
```
http://sarvasahay-frontend.s3-website.ap-south-1.amazonaws.com
```

### Backend API (after ECS service is created)
```
http://<alb-dns-name>
```

---

## Next Steps (Production Setup)

### 1. Create Database (RDS PostgreSQL)
```bash
aws rds create-db-instance \
  --db-instance-identifier sarvasahay-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username sarvasahay \
  --master-user-password <secure-password> \
  --allocated-storage 20 \
  --region ap-south-1
```

### 2. Create Redis Cache (ElastiCache)
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id sarvasahay-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region ap-south-1
```

### 3. Create Load Balancer (ALB)
```bash
aws elbv2 create-load-balancer \
  --name sarvasahay-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --region ap-south-1
```

### 4. Create ECS Service
```bash
aws ecs create-service \
  --cluster sarvasahay-cluster \
  --service-name sarvasahay-backend \
  --task-definition sarvasahay-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region ap-south-1
```

### 5. Configure Domain (Optional)
```bash
# Create Route 53 hosted zone
aws route53 create-hosted-zone --name sarvasahay.com --caller-reference $(date +%s)

# Request SSL certificate
aws acm request-certificate \
  --domain-name sarvasahay.com \
  --subject-alternative-names *.sarvasahay.com \
  --validation-method DNS \
  --region ap-south-1
```

---

## Cost Estimate

### Development Environment (~$50-80/month)
- ECS Fargate (1 task): $15/month
- RDS db.t3.micro: $15/month
- ElastiCache t3.micro: $12/month
- S3 + Data transfer: $5/month
- ALB: $20/month

### Production Environment (~$200-400/month)
- ECS Fargate (2-4 tasks): $60-120/month
- RDS db.t3.small: $30/month
- ElastiCache t3.small: $25/month
- S3 + CloudFront: $20/month
- ALB: $20/month
- Data transfer: $50/month

---

## Troubleshooting

### Issue: AWS CLI not found
```bash
# Install AWS CLI
# Windows: https://awscli.amazonaws.com/AWSCLIV2.msi
# Mac: brew install awscli
# Linux: sudo apt-get install awscli
```

### Issue: Docker build fails
```bash
# Check Docker is running
docker ps

# Check Dockerfile exists
cd -SarvaSahay
ls Dockerfile
```

### Issue: ECR push fails
```bash
# Re-login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com
```

### Issue: S3 bucket already exists
```bash
# Use a unique bucket name
aws s3 mb s3://sarvasahay-frontend-<your-name> --region ap-south-1
```

---

## Useful Commands

### View Logs
```bash
# ECS logs
aws logs tail /ecs/sarvasahay-backend --follow

# CloudWatch logs
aws logs describe-log-groups --region ap-south-1
```

### Update Backend
```bash
# Rebuild and push
docker build -t sarvasahay-backend .
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-backend:latest

# Force new deployment
aws ecs update-service --cluster sarvasahay-cluster --service sarvasahay-backend --force-new-deployment
```

### Update Frontend
```bash
# Rebuild and upload
cd frontend/web-app
npm run build
aws s3 sync build/ s3://sarvasahay-frontend --delete

# Invalidate CloudFront cache (if using CloudFront)
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

### Delete Resources (Cleanup)
```bash
# Delete ECS service
aws ecs delete-service --cluster sarvasahay-cluster --service sarvasahay-backend --force

# Delete ECS cluster
aws ecs delete-cluster --cluster sarvasahay-cluster

# Delete ECR repository
aws ecr delete-repository --repository-name sarvasahay-backend --force

# Delete S3 bucket
aws s3 rb s3://sarvasahay-frontend --force

# Delete RDS instance
aws rds delete-db-instance --db-instance-identifier sarvasahay-db --skip-final-snapshot

# Delete ElastiCache cluster
aws elasticache delete-cache-cluster --cache-cluster-id sarvasahay-redis
```

---

## Support & Documentation

### Detailed Guides
- `AWS_FULL_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `AWS_DEPLOYMENT_STEP_BY_STEP.md` - Step-by-step instructions
- `DEPLOY_PRODUCTION_ARCHITECTURE.md` - Architecture details
- `infrastructure/terraform/` - Terraform IaC files

### AWS Documentation
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [RDS Documentation](https://docs.aws.amazon.com/rds/)

---

## Summary

✅ **Quick Deployment:** Use `.\deploy-to-aws-complete.ps1`
✅ **Frontend:** Deployed to S3 with static website hosting
✅ **Backend:** Docker image pushed to ECR, ready for ECS
✅ **Cost:** Starting at ~$50/month for development
✅ **Time:** 15-20 minutes for basic deployment

**Your SarvaSahay platform is ready for AWS! 🚀**

For production setup with database, load balancer, and domain, see `AWS_FULL_DEPLOYMENT_GUIDE.md`.
