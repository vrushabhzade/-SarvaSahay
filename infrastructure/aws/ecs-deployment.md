# AWS ECS Deployment Guide for SarvaSahay Platform

## Overview

This guide covers deploying your Docker containers to AWS using:
- **Amazon ECS with Fargate**: Serverless container orchestration
- **Application Load Balancer**: Traffic distribution and health checks
- **Amazon RDS**: Managed PostgreSQL database
- **Amazon ElastiCache**: Managed Redis cluster
- **Amazon ECR**: Docker image registry
- **CloudWatch**: Monitoring and logging

## Architecture

```
Internet → ALB → ECS Fargate Tasks → RDS PostgreSQL
                                   → ElastiCache Redis
                                   → S3 (Documents)
                                   → Lambda (Processing)
```

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured
3. Docker installed locally
4. Your application tested locally

## Deployment Options

### Option 1: Quick Deploy with AWS Copilot (Recommended for Getting Started)
### Option 2: Manual ECS Deployment (Full Control)
### Option 3: Terraform Infrastructure as Code (Production Ready)

---

## Option 1: Quick Deploy with AWS Copilot

AWS Copilot simplifies ECS deployment with a CLI tool.

### Step 1: Install AWS Copilot

```powershell
# Windows (PowerShell)
Invoke-WebRequest -OutFile copilot.exe https://github.com/aws/copilot-cli/releases/latest/download/copilot-windows.exe
Move-Item -Path .\copilot.exe -Destination $Env:ProgramFiles\copilot.exe
```

### Step 2: Initialize Application

```bash
# Initialize Copilot application
copilot app init sarvasahay-platform

# Create environment (dev/staging/prod)
copilot env init --name dev --profile default --default-config

# Deploy environment
copilot env deploy --name dev
```

### Step 3: Create and Deploy Services

```bash
# Create main application service
copilot svc init --name app \
  --svc-type "Load Balanced Web Service" \
  --dockerfile ./Dockerfile \
  --port 8000

# Deploy the service
copilot svc deploy --name app --env dev
```

### Step 4: Add Database and Redis

```bash
# Add RDS PostgreSQL
copilot storage init --name sarvasahay-db \
  --storage-type Aurora \
  --engine PostgreSQL \
  --initial-db sarvasahay

# Add ElastiCache Redis
copilot storage init --name sarvasahay-cache \
  --storage-type Redis
```

---

## Option 2: Manual ECS Deployment

For full control over your infrastructure.

### Step 1: Create ECR Repository

```bash
# Create repository for your Docker image
aws ecr create-repository --repository-name sarvasahay-platform --region ap-south-1

# Get login credentials
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
```

### Step 2: Build and Push Docker Image

```bash
# Build image
docker build -t sarvasahay-platform .

# Tag image
docker tag sarvasahay-platform:latest YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-platform:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-platform:latest
```

### Step 3: Create VPC and Networking (if not exists)

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region ap-south-1

# Create subnets (public and private)
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.1.0/24 --availability-zone ap-south-1a
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.2.0/24 --availability-zone ap-south-1b

# Create Internet Gateway
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --vpc-id vpc-xxxxx --internet-gateway-id igw-xxxxx
```

### Step 4: Create RDS Database

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier sarvasahay-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.7 \
  --master-username sarvasahay \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name sarvasahay-db-subnet \
  --backup-retention-period 7 \
  --region ap-south-1
```

### Step 5: Create ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id sarvasahay-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name sarvasahay-cache-subnet \
  --security-group-ids sg-xxxxx \
  --region ap-south-1
```

### Step 6: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name sarvasahay-cluster --region ap-south-1
```

### Step 7: Create Task Definition

See `task-definition.json` file created below.

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition.json
```

### Step 8: Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name sarvasahay-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --region ap-south-1

# Create target group
aws elbv2 create-target-group \
  --name sarvasahay-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region ap-south-1

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### Step 9: Create ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster sarvasahay-cluster \
  --service-name sarvasahay-app \
  --task-definition sarvasahay-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=sarvasahay-app,containerPort=8000 \
  --region ap-south-1
```

---

## Option 3: Terraform Deployment (Recommended for Production)

Infrastructure as Code for reproducible deployments.

### Step 1: Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### Step 2: Configure Variables

Edit `terraform.tfvars`:

```hcl
aws_region = "ap-south-1"
environment = "production"
app_name = "sarvasahay"
container_image = "YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-platform:latest"
db_password = "YOUR_SECURE_PASSWORD"
```

### Step 3: Plan and Apply

```bash
# Review changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output alb_dns_name
```

---

## Post-Deployment Configuration

### 1. Update DNS

Point your domain to the ALB DNS name:

```bash
# Get ALB DNS
aws elbv2 describe-load-balancers --names sarvasahay-alb --query 'LoadBalancers[0].DNSName'

# Create Route53 record (if using Route53)
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch file://dns-change.json
```

### 2. Configure SSL/TLS

```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name sarvasahay.gov.in \
  --validation-method DNS \
  --region ap-south-1

# Add HTTPS listener to ALB
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 3. Set Up Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/sarvasahay-cluster/sarvasahay-app \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/sarvasahay-cluster/sarvasahay-app \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### 4. Configure CloudWatch Monitoring

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard --dashboard-name SarvaSahay --dashboard-body file://dashboard.json

# Set up alarms
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

## Environment Variables

Update your ECS task definition with these environment variables:

```json
{
  "environment": [
    {"name": "DATABASE_URL", "value": "postgresql://user:pass@rds-endpoint:5432/sarvasahay"},
    {"name": "REDIS_URL", "value": "redis://elasticache-endpoint:6379/0"},
    {"name": "AWS_DEFAULT_REGION", "value": "ap-south-1"},
    {"name": "AWS_S3_BUCKET_DOCUMENTS", "value": "sarvasahay-documents"},
    {"name": "ENVIRONMENT", "value": "production"}
  ]
}
```

---

## Cost Estimation (Mumbai Region - ap-south-1)

### Development Environment
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB): ~$30/month
- RDS db.t3.micro: ~$15/month
- ElastiCache cache.t3.micro: ~$12/month
- ALB: ~$20/month
- **Total: ~$77/month**

### Production Environment
- ECS Fargate (4 tasks, 1 vCPU, 2GB): ~$120/month
- RDS db.t3.small (Multi-AZ): ~$60/month
- ElastiCache cache.t3.small: ~$25/month
- ALB: ~$20/month
- S3, CloudWatch, Data Transfer: ~$25/month
- **Total: ~$250/month**

---

## Monitoring and Maintenance

### View Logs

```bash
# View ECS service logs
aws logs tail /ecs/sarvasahay-app --follow

# View specific task logs
aws ecs describe-tasks --cluster sarvasahay-cluster --tasks task-id
```

### Update Service

```bash
# Update task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update service with new task definition
aws ecs update-service \
  --cluster sarvasahay-cluster \
  --service sarvasahay-app \
  --task-definition sarvasahay-task:2 \
  --force-new-deployment
```

### Rollback

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster sarvasahay-cluster \
  --service sarvasahay-app \
  --task-definition sarvasahay-task:1
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service events
aws ecs describe-services --cluster sarvasahay-cluster --services sarvasahay-app

# Check task stopped reason
aws ecs describe-tasks --cluster sarvasahay-cluster --tasks task-id
```

### Health Check Failures

```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Test health endpoint
curl http://ALB_DNS_NAME/health
```

### Database Connection Issues

```bash
# Test RDS connectivity from ECS task
aws ecs execute-command \
  --cluster sarvasahay-cluster \
  --task task-id \
  --container sarvasahay-app \
  --interactive \
  --command "/bin/bash"

# Inside container
psql -h rds-endpoint -U sarvasahay -d sarvasahay
```

---

## Security Best Practices

1. **Use Secrets Manager** for sensitive data
2. **Enable VPC Flow Logs** for network monitoring
3. **Use IAM roles** instead of access keys
4. **Enable encryption** for RDS and S3
5. **Implement WAF** on ALB for DDoS protection
6. **Regular security patches** via automated task updates
7. **Enable CloudTrail** for audit logging

---

## Next Steps

1. Set up CI/CD pipeline (see `ci-cd-pipeline.md`)
2. Configure backup and disaster recovery
3. Implement blue-green deployment
4. Set up multi-region failover
5. Configure CDN (CloudFront) for static assets

---

## Support Resources

- AWS ECS Documentation: https://docs.aws.amazon.com/ecs/
- AWS Copilot: https://aws.github.io/copilot-cli/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/
