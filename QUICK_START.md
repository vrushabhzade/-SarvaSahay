# SarvaSahay Platform - Quick Start Guide

Get the SarvaSahay platform up and running in minutes!

## Prerequisites

- Docker Desktop installed
- 8GB RAM minimum
- 20GB free disk space

## Quick Deployment (5 Minutes)

### Step 1: Clone and Configure (2 minutes)

```bash
# Navigate to project directory
cd sarvasahay-platform

# Create environment file
cp .env.example .env

# Edit .env with your credentials (use any text editor)
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Minimum required configuration in .env:**
```env
# Database (use defaults for local development)
POSTGRES_PASSWORD=your_secure_password_here

# Security (generate random strings)
SECRET_KEY=your_secret_key_min_32_characters_long
ENCRYPTION_KEY=your_base64_encoded_encryption_key
JWT_SECRET=your_jwt_secret_key_here

# Optional: Add real API keys for full functionality
PM_KISAN_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
```

### Step 2: Deploy (3 minutes)

**Windows:**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. ✓ Check prerequisites
2. ✓ Build Docker images
3. ✓ Start all services
4. ✓ Initialize database
5. ✓ Load government schemes
6. ✓ Run health checks

### Step 3: Access the Platform

Once deployment completes:

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Test the Platform

### 1. Check System Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-02T10:30:00Z",
  "services": {
    "database": "connected",
    "cache": "connected",
    "api": "running"
  }
}
```

### 2. Create a Test Profile

```bash
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 35,
    "gender": "male",
    "caste": "obc",
    "annual_income": 50000,
    "state": "Maharashtra",
    "district": "Pune"
  }'
```

### 3. Check Eligibility

```bash
curl http://localhost:8000/api/v1/eligibility/evaluate/{profile_id}
```

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Access Database
```bash
docker-compose exec postgres psql -U sarvasahay -d sarvasahay_db
```

### Access Redis
```bash
docker-compose exec redis redis-cli
```

### Run Tests
```bash
docker-compose exec app python -m pytest tests/
```

## Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Stop the conflicting service or change ports in docker-compose.yml
```

### Services Not Starting

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Restart Docker Desktop and try again
```

### Database Connection Failed

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## Next Steps

1. **Configure Real APIs:** Add your government API credentials to `.env`
2. **Set Up Notifications:** Configure Twilio/SendGrid for SMS/email
3. **Load Production Data:** Import real government schemes
4. **Security:** Generate strong encryption keys
5. **Monitoring:** Set up CloudWatch or Prometheus

## Production Deployment

For production deployment, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [SYSTEM_VALIDATION_REPORT.md](SYSTEM_VALIDATION_REPORT.md) - System validation status

## Support

- **Documentation:** See README.md
- **Issues:** Check SYSTEM_VALIDATION_REPORT.md for known issues
- **API Reference:** http://localhost:8000/docs (after deployment)

## Clean Up

To completely remove the platform:

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker rmi sarvasahay-platform:latest
```

---

**Deployment Time:** ~5 minutes  
**First-Time Setup:** ~10 minutes  
**Ready for Testing:** Immediately after deployment

Happy deploying! 🚀
