# SarvaSahay - AWS Deployment Step-by-Step Guide

This guide will help you deploy the SarvaSahay platform to AWS in production.

---

## 📋 Prerequisites

### 1. AWS Account Setup
- [ ] AWS account created
- [ ] AWS CLI installed
- [ ] AWS credentials configured

### 2. Required Tools
```bash
# Install AWS CLI
# Windows (PowerShell as Administrator)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version

# Install Terraform (optional, for infrastructure as code)
# Download from: https://www.terraform.io/downloads
```

### 3. Configure AWS Credentials
```bash
# Run this command and enter your AWS credentials
aws configure

# You'll need:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: ap-south-1 (Mumbai, India)
# - Default output format: json
```

---

## 🚀 Deployment Options

Choose one of these three methods:

### Option 1: Quick Deploy (Recommended for Testing)
**Time:** ~15 minutes  
**Complexity:** Easy  
**Cost:** ~$77/month

### Option 2: Terraform Deploy (Recommended for Production)
**Time:** ~30 minutes  
**Complexity:** Medium  
**Cost:** ~$250-400/month

### Option 3: Manual Deploy (Full Control)
**Time:** ~60 minutes  
**Complexity:** Advanced  
**Cost:** Variable

---

## 🎯 Option 1: Quick Deploy with AWS Copilot

### Step 1: Install AWS Copilot
```powershell
# Windows PowerShell
Invoke-WebRequest -OutFile copilot-windows.exe https://github.com/aws/copilot-cli/releases/latest/download/copilot-windows.exe

# Move to a directory in your PATH
Move-Item -Path .\copilot-windows.exe -Destination C:\Windows\System32\copilot.exe

# Verify installation
copilot --version
```

### Step 2: Initialize Application
```bash
# Navigate to your project directory
cd "C:\Users\VRUSHABH\OneDrive\Music\Desktop\KIRO PROJECT\Rural Ai prototype"

# Initialize Copilot application
copilot app init sarvasahay

# Create environment
copilot env init --name production --profile default --region ap-south-1
```

### Step 3: Deploy Service
```bash
# Create and deploy the service
copilot svc init --name api --svc-type "Load Balanced Web Service" --dockerfile infrastructure/docker/Dockerfile

# Deploy to production
copilot svc deploy --name api --env production
```

### Step 4: Add Database
```bash
# Add RDS PostgreSQL
copilot storage init --name sarvasahay-db --storage-type Aurora --engine PostgreSQL

# Add ElastiCache Redis
copilot storage init --name sarvasahay-cache --storage-type Redis
```

### Step 5: Get Application URL
```bash
# Get the deployed URL
copilot svc show --name api
```

**Your app will be available at:** `https://api.sarvasahay-production.ap-south-1.aws`

---

## 🏗️ Option 2: Terraform Deploy (Infrastructure as Code)

### Step 1: Install Terraform
```powershell
# Download and install from https://www.terraform.io/downloads
# Or use Chocolatey
choco install terraform

# Verify
terraform --version
```

### Step 2: Configure Variables
```bash
# Navigate to terraform directory
cd infrastructure/terraform

# Create terraform.tfvars file
notepad terraform.tfvars
```

Add this content:
```hcl
aws_region = "ap-south-1"
environment = "production"
app_name = "sarvasahay"

# Database
db_username = "sarvasahay_admin"
db_password = "CHANGE_THIS_PASSWORD"  # Use a strong password

# Application
app_port = 8000
app_count = 2  # Number of containers

# Domain (optional)
domain_name = "sarvasahay.gov.in"  # Your domain
```

### Step 3: Initialize Terraform
```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply
```

Type `yes` when prompted.

### Step 4: Build and Push Docker Image
```bash
# Get ECR login
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# Build image
docker build -f infrastructure/docker/Dockerfile -t sarvasahay:latest .

# Tag image
docker tag sarvasahay:latest YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest
```

### Step 5: Deploy to ECS
```bash
# Update ECS service
aws ecs update-service --cluster sarvasahay-cluster --service sarvasahay-service --force-new-deployment --region ap-south-1
```

### Step 6: Get Application URL
```bash
# Get load balancer DNS
terraform output alb_dns_name
```

---

## 🔧 Option 3: Manual AWS Console Deploy

### Step 1: Create ECR Repository
1. Go to AWS Console → ECR
2. Click "Create repository"
3. Name: `sarvasahay`
4. Click "Create"

### Step 2: Push Docker Image
```bash
# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# Build and push
docker build -f infrastructure/docker/Dockerfile -t sarvasahay:latest .
docker tag sarvasahay:latest YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest
```

### Step 3: Create RDS Database
1. Go to AWS Console → RDS
2. Click "Create database"
3. Choose PostgreSQL
4. Template: Production
5. DB instance identifier: `sarvasahay-db`
6. Master username: `sarvasahay_admin`
7. Master password: (create strong password)
8. Instance type: db.t3.micro (for testing) or db.t3.medium (production)
9. Storage: 20 GB
10. Click "Create database"

### Step 4: Create ElastiCache Redis
1. Go to AWS Console → ElastiCache
2. Click "Create"
3. Choose Redis
4. Name: `sarvasahay-cache`
5. Node type: cache.t3.micro
6. Number of replicas: 1
7. Click "Create"

### Step 5: Create ECS Cluster
1. Go to AWS Console → ECS
2. Click "Create Cluster"
3. Cluster name: `sarvasahay-cluster`
4. Infrastructure: AWS Fargate
5. Click "Create"

### Step 6: Create Task Definition
1. Go to ECS → Task Definitions
2. Click "Create new Task Definition"
3. Family: `sarvasahay-task`
4. Launch type: Fargate
5. CPU: 1 vCPU
6. Memory: 2 GB
7. Add container:
   - Name: `sarvasahay-app`
   - Image: `YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest`
   - Port: 8000
   - Environment variables:
     ```
     DATABASE_URL=postgresql://user:pass@db-endpoint:5432/sarvasahay
     REDIS_URL=redis://cache-endpoint:6379
     ENVIRONMENT=production
     ```
8. Click "Create"

### Step 7: Create Application Load Balancer
1. Go to EC2 → Load Balancers
2. Click "Create Load Balancer"
3. Choose "Application Load Balancer"
4. Name: `sarvasahay-alb`
5. Scheme: Internet-facing
6. Listeners: HTTP (80), HTTPS (443)
7. Availability Zones: Select at least 2
8. Create target group:
   - Name: `sarvasahay-targets`
   - Target type: IP
   - Protocol: HTTP
   - Port: 8000
9. Click "Create"

### Step 8: Create ECS Service
1. Go to ECS → Clusters → sarvasahay-cluster
2. Click "Create Service"
3. Launch type: Fargate
4. Task Definition: sarvasahay-task
5. Service name: `sarvasahay-service`
6. Number of tasks: 2
7. Load balancer: sarvasahay-alb
8. Target group: sarvasahay-targets
9. Click "Create Service"

### Step 9: Configure Domain (Optional)
1. Go to Route 53
2. Create hosted zone for your domain
3. Create A record pointing to ALB
4. Update nameservers at your domain registrar

---

## 🔐 Security Configuration

### 1. Set Environment Variables
```bash
# In ECS Task Definition, add these environment variables:
DATABASE_URL=postgresql://user:password@rds-endpoint:5432/sarvasahay
REDIS_URL=redis://elasticache-endpoint:6379
SECRET_KEY=your-secret-key-here
AWS_REGION=ap-south-1
ENVIRONMENT=production
```

### 2. Configure Security Groups
```bash
# Application Security Group
- Allow inbound: Port 8000 from ALB security group
- Allow outbound: All traffic

# Database Security Group
- Allow inbound: Port 5432 from application security group
- Allow outbound: None

# Redis Security Group
- Allow inbound: Port 6379 from application security group
- Allow outbound: None

# ALB Security Group
- Allow inbound: Port 80 (HTTP) from 0.0.0.0/0
- Allow inbound: Port 443 (HTTPS) from 0.0.0.0/0
- Allow outbound: Port 8000 to application security group
```

### 3. Enable SSL/TLS
```bash
# Request certificate in AWS Certificate Manager
aws acm request-certificate \
  --domain-name sarvasahay.gov.in \
  --validation-method DNS \
  --region ap-south-1

# Add HTTPS listener to ALB with certificate
```

---

## 📊 Post-Deployment Verification

### 1. Check Service Health
```bash
# Check ECS service status
aws ecs describe-services --cluster sarvasahay-cluster --services sarvasahay-service --region ap-south-1

# Check running tasks
aws ecs list-tasks --cluster sarvasahay-cluster --service-name sarvasahay-service --region ap-south-1
```

### 2. Test Application
```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers --names sarvasahay-alb --region ap-south-1 --query 'LoadBalancers[0].DNSName'

# Test API
curl http://YOUR-ALB-DNS-NAME/
curl http://YOUR-ALB-DNS-NAME/docs
```

### 3. Monitor Logs
```bash
# View CloudWatch logs
aws logs tail /ecs/sarvasahay-task --follow --region ap-south-1
```

---

## 💰 Cost Estimation

### Development Environment (~$77/month)
- ECS Fargate (1 task): $30/month
- RDS db.t3.micro: $15/month
- ElastiCache cache.t3.micro: $12/month
- ALB: $20/month
- Data transfer: Minimal

### Production Environment (~$250-400/month)
- ECS Fargate (2-4 tasks): $60-120/month
- RDS db.t3.medium: $70/month
- ElastiCache cache.t3.medium: $50/month
- ALB: $20/month
- S3 storage: $10/month
- CloudWatch: $10/month
- Data transfer: $20-100/month

---

## 🔄 Continuous Deployment

### GitHub Actions (Automated)
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
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com
      
      - name: Build and push Docker image
        run: |
          docker build -f infrastructure/docker/Dockerfile -t sarvasahay:${{ github.sha }} .
          docker tag sarvasahay:${{ github.sha }} ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster sarvasahay-cluster --service sarvasahay-service --force-new-deployment
```

---

## 🆘 Troubleshooting

### Issue: Tasks keep stopping
**Solution:** Check CloudWatch logs for errors, verify environment variables

### Issue: Can't connect to database
**Solution:** Verify security groups allow traffic from ECS tasks to RDS

### Issue: High costs
**Solution:** Use Fargate Spot for non-critical tasks, enable auto-scaling

### Issue: Slow performance
**Solution:** Increase task CPU/memory, add more tasks, enable caching

---

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Copilot Guide](https://aws.github.io/copilot-cli/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Project Documentation](./DEPLOY_PRODUCTION_ARCHITECTURE.md)

---

## ✅ Deployment Checklist

- [ ] AWS account configured
- [ ] AWS CLI installed and configured
- [ ] Docker image built and tested locally
- [ ] ECR repository created
- [ ] Docker image pushed to ECR
- [ ] RDS database created
- [ ] ElastiCache Redis created
- [ ] ECS cluster created
- [ ] Task definition created
- [ ] Application Load Balancer created
- [ ] ECS service created and running
- [ ] Security groups configured
- [ ] Environment variables set
- [ ] SSL certificate configured (optional)
- [ ] Domain configured (optional)
- [ ] Monitoring and alerts set up
- [ ] Application tested and verified

---

**Need Help?** Check the detailed guides:
- [DEPLOY_PRODUCTION_ARCHITECTURE.md](./DEPLOY_PRODUCTION_ARCHITECTURE.md)
- [AWS_DEPLOYMENT_QUICKSTART.md](./AWS_DEPLOYMENT_QUICKSTART.md)
- [infrastructure/aws/ecs-deployment.md](./infrastructure/aws/ecs-deployment.md)
