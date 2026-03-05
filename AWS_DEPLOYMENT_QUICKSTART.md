# AWS Deployment Quick Start Guide

## 🚀 Deploy SarvaSahay to AWS in 3 Steps

This guide gets your Docker containers running on AWS ECS with minimal configuration.

---

## Prerequisites

✅ AWS Account (Free Tier eligible)  
✅ AWS CLI installed and configured  
✅ Docker Desktop running  
✅ Application tested locally  

---

## Step 1: Configure AWS Credentials

```powershell
# Configure AWS CLI with your credentials
aws configure

# You'll be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (use: ap-south-1 for Mumbai, India)
# - Default output format (use: json)

# Verify configuration
aws sts get-caller-identity
```

**Get AWS Credentials:**
1. Go to AWS Console → IAM → Users → Your User
2. Security Credentials → Create Access Key
3. Download and save the credentials securely

---

## Step 2: Choose Your Deployment Method

### Option A: Automated Script (Fastest) ⚡

```powershell
# Deploy to development environment
.\scripts\deploy_to_aws.ps1 -Environment dev -Region ap-south-1

# Deploy to production
.\scripts\deploy_to_aws.ps1 -Environment production -Region ap-south-1
```

**What this does:**
- Creates ECR repository
- Builds and pushes Docker image
- Updates ECS task definition
- Deploys to ECS cluster (if exists)

**Note:** First time? You'll need to create infrastructure first (see Option B or C).

---

### Option B: AWS Copilot (Recommended for Beginners) 🎯

AWS Copilot handles all infrastructure automatically.

#### Install Copilot

```powershell
# Download Copilot CLI
Invoke-WebRequest -OutFile copilot.exe https://github.com/aws/copilot-cli/releases/latest/download/copilot-windows.exe

# Move to Program Files
Move-Item -Path .\copilot.exe -Destination "$env:ProgramFiles\copilot.exe"

# Add to PATH (restart terminal after)
$env:Path += ";$env:ProgramFiles"
```

#### Deploy with Copilot

```bash
# 1. Initialize application
copilot app init sarvasahay-platform

# 2. Create environment
copilot env init --name production --profile default --default-config

# 3. Deploy environment (creates VPC, subnets, etc.)
copilot env deploy --name production

# 4. Create service
copilot svc init --name app \
  --svc-type "Load Balanced Web Service" \
  --dockerfile ./Dockerfile \
  --port 8000

# 5. Deploy service
copilot svc deploy --name app --env production

# 6. Get service URL
copilot svc show --name app
```

**Copilot creates:**
- VPC with public/private subnets
- Application Load Balancer
- ECS Cluster and Service
- CloudWatch Logs
- Auto-scaling configuration

**Cost:** ~$50-100/month for production setup

---

### Option C: Terraform (Production Ready) 🏗️

Full infrastructure as code with complete control.

#### Install Terraform

```powershell
# Using Chocolatey
choco install terraform

# Or download from: https://www.terraform.io/downloads
```

#### Deploy with Terraform

```bash
# 1. Navigate to terraform directory
cd infrastructure/terraform

# 2. Initialize Terraform
terraform init

# 3. Create terraform.tfvars file
cat > terraform.tfvars << EOF
aws_region = "ap-south-1"
environment = "production"
app_name = "sarvasahay"
container_image = "ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/sarvasahay-production:latest"
db_password = "YOUR_SECURE_PASSWORD_HERE"
EOF

# 4. Review infrastructure plan
terraform plan

# 5. Apply infrastructure
terraform apply

# 6. Get outputs
terraform output alb_dns_name
```

**Terraform creates:**
- Complete VPC with networking
- RDS PostgreSQL database
- ElastiCache Redis cluster
- ECS Cluster with Fargate
- Application Load Balancer
- S3 buckets for storage
- CloudWatch monitoring
- Auto-scaling policies

**Cost:** ~$250-400/month for production setup

---

## Step 3: Verify Deployment

### Check Service Status

```powershell
# Get cluster name
$CLUSTER = "sarvasahay-production-cluster"
$SERVICE = "sarvasahay-production-app"
$REGION = "ap-south-1"

# Check service status
aws ecs describe-services `
  --cluster $CLUSTER `
  --services $SERVICE `
  --region $REGION `
  --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}"

# Get ALB DNS name
aws elbv2 describe-load-balancers `
  --region $REGION `
  --query "LoadBalancers[?contains(LoadBalancerName, 'sarvasahay')].DNSName" `
  --output text
```

### Test Application

```powershell
# Get ALB URL (replace with your actual ALB DNS)
$ALB_URL = "sarvasahay-alb-123456789.ap-south-1.elb.amazonaws.com"

# Test health endpoint
curl http://$ALB_URL/health

# Test API
curl http://$ALB_URL/api/v1/health
```

### View Logs

```powershell
# Stream logs in real-time
aws logs tail /ecs/sarvasahay-production --follow --region ap-south-1

# View last 100 lines
aws logs tail /ecs/sarvasahay-production --since 1h --region ap-south-1
```

---

## Post-Deployment Configuration

### 1. Set Up Custom Domain (Optional)

```bash
# Create Route53 hosted zone
aws route53 create-hosted-zone --name sarvasahay.gov.in --caller-reference $(date +%s)

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --query "LoadBalancers[0].DNSName" --output text)

# Create DNS record (update hosted-zone-id)
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch '{
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

### 2. Enable HTTPS/SSL

```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name sarvasahay.gov.in \
  --validation-method DNS \
  --region ap-south-1

# Add HTTPS listener to ALB (after certificate is validated)
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 3. Configure Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/sarvasahay-production-cluster/sarvasahay-production-app \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10 \
  --region ap-south-1

# Create CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/sarvasahay-production-cluster/sarvasahay-production-app \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }' \
  --region ap-south-1
```

### 4. Set Up Monitoring Alerts

```bash
# Create high CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sarvasahay-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ClusterName,Value=sarvasahay-production-cluster Name=ServiceName,Value=sarvasahay-production-app \
  --region ap-south-1

# Create high memory alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sarvasahay-high-memory \
  --alarm-description "Alert when memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ClusterName,Value=sarvasahay-production-cluster Name=ServiceName,Value=sarvasahay-production-app \
  --region ap-south-1
```

---

## Updating Your Application

### Deploy New Version

```powershell
# Build and deploy new version
.\scripts\deploy_to_aws.ps1 -Environment production -ImageTag v1.1.0

# Or with Copilot
copilot svc deploy --name app --env production

# Or with Terraform
cd infrastructure/terraform
terraform apply
```

### Rollback to Previous Version

```powershell
# List task definitions
aws ecs list-task-definitions --family-prefix sarvasahay-task --region ap-south-1

# Update service to previous task definition
aws ecs update-service \
  --cluster sarvasahay-production-cluster \
  --service sarvasahay-production-app \
  --task-definition sarvasahay-task:PREVIOUS_VERSION \
  --region ap-south-1
```

---

## Cost Management

### Monitor Costs

```bash
# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Set up billing alert
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alert \
  --alarm-description "Alert when estimated charges exceed $100" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### Cost Optimization Tips

1. **Use Fargate Spot** for non-critical workloads (70% cost savings)
2. **Right-size tasks** - Start with 0.5 vCPU, 1GB RAM
3. **Enable auto-scaling** - Scale down during off-hours
4. **Use S3 lifecycle policies** - Move old data to cheaper storage
5. **Delete unused resources** - Clean up test environments

---

## Troubleshooting

### Service Won't Start

```powershell
# Check service events
aws ecs describe-services --cluster CLUSTER_NAME --services SERVICE_NAME --region ap-south-1

# Check task logs
aws logs tail /ecs/sarvasahay-production --since 30m --region ap-south-1

# Describe failed tasks
aws ecs describe-tasks --cluster CLUSTER_NAME --tasks TASK_ID --region ap-south-1
```

### Can't Access Application

```powershell
# Check target health
aws elbv2 describe-target-health --target-group-arn TARGET_GROUP_ARN --region ap-south-1

# Check security groups
aws ec2 describe-security-groups --region ap-south-1

# Test from within VPC
aws ecs execute-command \
  --cluster CLUSTER_NAME \
  --task TASK_ID \
  --container app \
  --interactive \
  --command "/bin/bash"
```

### Database Connection Issues

```powershell
# Check RDS status
aws rds describe-db-instances --region ap-south-1

# Test connection from ECS task
aws ecs execute-command \
  --cluster CLUSTER_NAME \
  --task TASK_ID \
  --container app \
  --interactive \
  --command "psql -h RDS_ENDPOINT -U sarvasahay -d sarvasahay"
```

---

## Clean Up (Delete Everything)

### With Copilot

```bash
copilot app delete
```

### With Terraform

```bash
cd infrastructure/terraform
terraform destroy
```

### Manual Cleanup

```powershell
# Delete ECS service
aws ecs delete-service --cluster CLUSTER_NAME --service SERVICE_NAME --force --region ap-south-1

# Delete ECS cluster
aws ecs delete-cluster --cluster CLUSTER_NAME --region ap-south-1

# Delete RDS instance
aws rds delete-db-instance --db-instance-identifier DB_NAME --skip-final-snapshot --region ap-south-1

# Delete ECR repository
aws ecr delete-repository --repository-name REPO_NAME --force --region ap-south-1
```

---

## Next Steps

1. ✅ Set up CI/CD pipeline (GitHub Actions, GitLab CI)
2. ✅ Configure backup and disaster recovery
3. ✅ Implement blue-green deployment
4. ✅ Set up multi-region failover
5. ✅ Add CloudFront CDN for static assets
6. ✅ Enable AWS WAF for security
7. ✅ Set up centralized logging with CloudWatch Insights

---

## Support & Resources

- **Full Documentation**: `infrastructure/aws/ecs-deployment.md`
- **AWS ECS Docs**: https://docs.aws.amazon.com/ecs/
- **AWS Copilot**: https://aws.github.io/copilot-cli/
- **Terraform AWS**: https://registry.terraform.io/providers/hashicorp/aws/

---

## Estimated Costs

### Development Environment
- **ECS Fargate**: ~$30/month (2 tasks, 0.5 vCPU, 1GB)
- **RDS db.t3.micro**: ~$15/month
- **ElastiCache**: ~$12/month
- **ALB**: ~$20/month
- **Total**: ~$77/month

### Production Environment
- **ECS Fargate**: ~$120/month (4 tasks, 1 vCPU, 2GB)
- **RDS db.t3.small (Multi-AZ)**: ~$60/month
- **ElastiCache**: ~$25/month
- **ALB**: ~$20/month
- **S3, CloudWatch, Data Transfer**: ~$25/month
- **Total**: ~$250/month

**Free Tier**: First 12 months include significant free usage!

---

**Ready to deploy? Start with Option B (Copilot) for the easiest experience!** 🚀
