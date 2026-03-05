# SarvaSahay Platform - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the SarvaSahay platform to production. The platform supports multiple deployment options: Docker, Kubernetes, and AWS Lambda.

## Prerequisites

### Required Software
- Docker 20.10+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl configured with cluster access
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- AWS CLI (for Lambda deployment)

### Required Accounts
- AWS account (for Lambda/S3)
- Twilio account (for SMS/Voice)
- Email service provider (SendGrid/AWS SES)
- Government API credentials (PM-KISAN, DBT, PFMS)

## Deployment Options

### Option 1: Docker Compose (Development/Staging)
### Option 2: Kubernetes (Production)
### Option 3: AWS Lambda (Serverless)

---

## Option 1: Docker Compose Deployment

### Step 1: Environment Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://sarvasahay:password@postgres:5432/sarvasahay_db
POSTGRES_USER=sarvasahay
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=sarvasahay_db

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_secret_key_here_min_32_chars
ENCRYPTION_KEY=your_encryption_key_base64_encoded
JWT_SECRET=your_jwt_secret_key

# Government APIs
PM_KISAN_API_KEY=your_pm_kisan_api_key
PM_KISAN_API_URL=https://pmkisan.gov.in/api/v1
DBT_API_KEY=your_dbt_api_key
DBT_API_URL=https://dbtbharat.gov.in/api/v1
PFMS_API_KEY=your_pfms_api_key
PFMS_API_URL=https://pfms.nic.in/api/v1

# Notification Services
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@sarvasahay.gov.in

# AWS Configuration (for document storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=sarvasahay-documents

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
API_VERSION=v1
MAX_WORKERS=4
```

### Step 2: Build Docker Images

```bash
# Build the application image
docker build -t sarvasahay-platform:latest -f infrastructure/docker/Dockerfile .

# Verify the image
docker images | grep sarvasahay
```

### Step 3: Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Initialize Database

```bash
# Run database migrations
docker-compose exec app alembic upgrade head

# Verify database schema
docker-compose exec app python scripts/db_manager.py verify
```

### Step 5: Load Initial Data

```bash
# Load government schemes
docker-compose exec app python scripts/db_manager.py load-schemes

# Load form templates
docker-compose exec app python scripts/db_manager.py load-templates

# Verify data
docker-compose exec app python scripts/db_manager.py stats
```

### Step 6: Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/api/v1/health/database

# Check Redis connection
curl http://localhost:8000/api/v1/health/cache
```

---

## Option 2: Kubernetes Deployment

### Step 1: Create Namespace

```bash
kubectl create namespace sarvasahay
kubectl config set-context --current --namespace=sarvasahay
```

### Step 2: Create Secrets

```bash
# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=username=sarvasahay \
  --from-literal=password=your_secure_password \
  --from-literal=database=sarvasahay_db

# Redis credentials
kubectl create secret generic redis-credentials \
  --from-literal=password=your_redis_password

# Application secrets
kubectl create secret generic app-secrets \
  --from-literal=secret-key=your_secret_key \
  --from-literal=encryption-key=your_encryption_key \
  --from-literal=jwt-secret=your_jwt_secret

# Government API credentials
kubectl create secret generic gov-api-credentials \
  --from-literal=pm-kisan-key=your_pm_kisan_key \
  --from-literal=dbt-key=your_dbt_key \
  --from-literal=pfms-key=your_pfms_key

# Notification service credentials
kubectl create secret generic notification-credentials \
  --from-literal=twilio-sid=your_twilio_sid \
  --from-literal=twilio-token=your_twilio_token \
  --from-literal=sendgrid-key=your_sendgrid_key

# AWS credentials
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=your_aws_access_key \
  --from-literal=secret-access-key=your_aws_secret_key
```

### Step 3: Create ConfigMap

```bash
kubectl create configmap app-config \
  --from-literal=environment=production \
  --from-literal=log-level=INFO \
  --from-literal=api-version=v1 \
  --from-literal=pm-kisan-url=https://pmkisan.gov.in/api/v1 \
  --from-literal=dbt-url=https://dbtbharat.gov.in/api/v1 \
  --from-literal=pfms-url=https://pfms.nic.in/api/v1 \
  --from-literal=aws-region=ap-south-1 \
  --from-literal=s3-bucket=sarvasahay-documents
```

### Step 4: Deploy PostgreSQL

```bash
# Apply PostgreSQL deployment
kubectl apply -f infrastructure/kubernetes/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

### Step 5: Deploy Redis

```bash
# Apply Redis deployment
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
```

### Step 6: Deploy Application

```bash
# Apply application deployment
kubectl apply -f infrastructure/kubernetes/deployment.yaml

# Wait for application to be ready
kubectl wait --for=condition=ready pod -l app=sarvasahay --timeout=300s

# Check deployment status
kubectl get deployments
kubectl get pods
```

### Step 7: Deploy Ingress

```bash
# Apply ingress configuration
kubectl apply -f infrastructure/kubernetes/nginx-ingress.yaml

# Get ingress IP
kubectl get ingress sarvasahay-ingress
```

### Step 8: Initialize Database

```bash
# Get application pod name
POD_NAME=$(kubectl get pods -l app=sarvasahay -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $POD_NAME -- alembic upgrade head

# Load initial data
kubectl exec -it $POD_NAME -- python scripts/db_manager.py load-schemes
kubectl exec -it $POD_NAME -- python scripts/db_manager.py load-templates
```

### Step 9: Configure Auto-Scaling

```bash
# Apply horizontal pod autoscaler
kubectl apply -f infrastructure/kubernetes/hpa.yaml

# Verify HPA
kubectl get hpa
```

### Step 10: Health Check

```bash
# Get service URL
SERVICE_URL=$(kubectl get ingress sarvasahay-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Check health
curl http://$SERVICE_URL/health
curl http://$SERVICE_URL/api/v1/health/database
curl http://$SERVICE_URL/api/v1/health/cache
```

---

## Option 3: AWS Lambda Deployment

### Step 1: Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region: ap-south-1
# Enter default output format: json
```

### Step 2: Create S3 Bucket

```bash
# Create bucket for documents
aws s3 mb s3://sarvasahay-documents --region ap-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket sarvasahay-documents \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket sarvasahay-documents \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### Step 3: Create RDS Database

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier sarvasahay-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.7 \
  --master-username sarvasahay \
  --master-user-password your_secure_password \
  --allocated-storage 100 \
  --storage-type gp3 \
  --vpc-security-group-ids sg-xxxxxxxx \
  --db-subnet-group-name sarvasahay-subnet-group \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --tags Key=Project,Value=SarvaSahay Key=Environment,Value=Production
```

### Step 4: Create ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id sarvasahay-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name sarvasahay-subnet-group \
  --security-group-ids sg-xxxxxxxx \
  --snapshot-retention-limit 5 \
  --snapshot-window "03:00-05:00" \
  --preferred-maintenance-window "mon:05:00-mon:07:00" \
  --tags Key=Project,Value=SarvaSahay Key=Environment,Value=Production
```

### Step 5: Deploy Lambda Functions

```bash
# Navigate to lambda directory
cd infrastructure/lambda

# Run deployment script (PowerShell on Windows)
.\deploy-lambda.ps1

# Or bash script (Linux/Mac)
./deploy-lambda.sh
```

### Step 6: Configure API Gateway

```bash
# Create API Gateway
aws apigateway create-rest-api \
  --name sarvasahay-api \
  --description "SarvaSahay Platform API" \
  --endpoint-configuration types=REGIONAL

# Get API ID
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='sarvasahay-api'].id" --output text)

# Create resources and methods (automated in deployment script)
```

### Step 7: Set Environment Variables

```bash
# Update Lambda function configuration
aws lambda update-function-configuration \
  --function-name sarvasahay-eligibility \
  --environment "Variables={
    DATABASE_URL=postgresql://sarvasahay:password@sarvasahay-db.xxxxx.ap-south-1.rds.amazonaws.com:5432/sarvasahay_db,
    REDIS_URL=redis://sarvasahay-redis.xxxxx.cache.amazonaws.com:6379/0,
    SECRET_KEY=your_secret_key,
    ENCRYPTION_KEY=your_encryption_key,
    PM_KISAN_API_KEY=your_pm_kisan_key,
    DBT_API_KEY=your_dbt_key,
    PFMS_API_KEY=your_pfms_key,
    TWILIO_ACCOUNT_SID=your_twilio_sid,
    TWILIO_AUTH_TOKEN=your_twilio_token,
    AWS_S3_BUCKET=sarvasahay-documents
  }"
```

### Step 8: Initialize Database

```bash
# Connect to RDS instance
psql -h sarvasahay-db.xxxxx.ap-south-1.rds.amazonaws.com -U sarvasahay -d sarvasahay_db

# Run migrations (from local machine with VPN/bastion)
alembic upgrade head

# Load initial data
python scripts/db_manager.py load-schemes
python scripts/db_manager.py load-templates
```

---

## Post-Deployment Configuration

### 1. Configure Monitoring

```bash
# Set up CloudWatch alarms (AWS)
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

# Set up log aggregation
# Configure application to send logs to CloudWatch/ELK
```

### 2. Configure Backups

```bash
# Database backups (automated in RDS)
aws rds modify-db-instance \
  --db-instance-identifier sarvasahay-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# Redis backups (automated in ElastiCache)
aws elasticache modify-cache-cluster \
  --cache-cluster-id sarvasahay-redis \
  --snapshot-retention-limit 7 \
  --snapshot-window "03:00-05:00"
```

### 3. Configure SSL/TLS

```bash
# For Kubernetes with cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml

# Create certificate issuer
kubectl apply -f infrastructure/kubernetes/cert-issuer.yaml

# Update ingress with TLS
kubectl apply -f infrastructure/kubernetes/nginx-ingress-tls.yaml
```

### 4. Configure Rate Limiting

```bash
# Update Redis configuration for rate limiting
# Configure in application settings
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_WINDOW=60
```

### 5. Configure CORS

```bash
# Update application configuration
export CORS_ORIGINS="https://sarvasahay.gov.in,https://app.sarvasahay.gov.in"
export CORS_ALLOW_CREDENTIALS=true
```

---

## Verification Checklist

### Application Health
- [ ] API endpoints responding (200 OK)
- [ ] Database connection working
- [ ] Redis cache working
- [ ] All services running

### Security
- [ ] SSL/TLS certificates installed
- [ ] Secrets properly configured
- [ ] Firewall rules configured
- [ ] API authentication working
- [ ] Encryption enabled

### Performance
- [ ] Response times <5 seconds for eligibility
- [ ] Auto-scaling configured
- [ ] Load balancing working
- [ ] Caching enabled

### Monitoring
- [ ] CloudWatch/Prometheus metrics collecting
- [ ] Alerts configured
- [ ] Log aggregation working
- [ ] Dashboard accessible

### Backups
- [ ] Database backups scheduled
- [ ] Redis snapshots configured
- [ ] Backup restoration tested

### Integration
- [ ] Government APIs accessible
- [ ] SMS/Voice services working
- [ ] Email notifications working
- [ ] Document storage working

---

## Rollback Procedure

### Docker Compose Rollback

```bash
# Stop current version
docker-compose down

# Pull previous version
docker pull sarvasahay-platform:previous-tag

# Update docker-compose.yml with previous tag
# Start previous version
docker-compose up -d
```

### Kubernetes Rollback

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/sarvasahay

# Rollback to specific revision
kubectl rollout undo deployment/sarvasahay --to-revision=2

# Check rollback status
kubectl rollout status deployment/sarvasahay
```

### Lambda Rollback

```bash
# List function versions
aws lambda list-versions-by-function --function-name sarvasahay-eligibility

# Update alias to previous version
aws lambda update-alias \
  --function-name sarvasahay-eligibility \
  --name production \
  --function-version 2
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database status
kubectl get pods -l app=postgres
docker-compose ps postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### 2. Redis Connection Failed
```bash
# Check Redis status
kubectl get pods -l app=redis
docker-compose ps redis

# Test connection
redis-cli -h redis -p 6379 ping
```

#### 3. API Not Responding
```bash
# Check application logs
kubectl logs -l app=sarvasahay --tail=100
docker-compose logs app --tail=100

# Check pod status
kubectl describe pod <pod-name>

# Restart application
kubectl rollout restart deployment/sarvasahay
docker-compose restart app
```

#### 4. High Memory Usage
```bash
# Check resource usage
kubectl top pods
docker stats

# Scale up resources
kubectl scale deployment sarvasahay --replicas=5

# Update resource limits
kubectl edit deployment sarvasahay
```

---

## Maintenance

### Regular Tasks

#### Daily
- Monitor application logs
- Check error rates
- Verify backup completion

#### Weekly
- Review performance metrics
- Check disk space
- Update security patches

#### Monthly
- Review and optimize database
- Update dependencies
- Conduct security audit
- Test disaster recovery

---

## Support

For deployment issues or questions:
- Email: devops@sarvasahay.gov.in
- Slack: #sarvasahay-deployment
- Documentation: https://docs.sarvasahay.gov.in

---

## Appendix

### A. Required Ports

- 8000: Application API
- 5432: PostgreSQL
- 6379: Redis
- 443: HTTPS (production)
- 80: HTTP (redirect to HTTPS)

### B. Resource Requirements

**Minimum (Development)**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB

**Recommended (Production)**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD

**High Availability (Production)**
- CPU: 16 cores
- RAM: 32 GB
- Disk: 500 GB SSD
- Multiple availability zones

### C. Scaling Guidelines

**User Load vs Resources**
- 1,000 users: 2 replicas, 4GB RAM each
- 10,000 users: 5 replicas, 8GB RAM each
- 100,000 users: 20 replicas, 16GB RAM each

---

*Last Updated: March 2, 2026*
*Version: 1.0.0*
