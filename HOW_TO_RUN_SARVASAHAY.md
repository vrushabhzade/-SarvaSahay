# 🇮🇳 How to Run SarvaSahay Platform

Complete guide to running the SarvaSahay AI-powered government scheme platform.

---

## Quick Start (Fastest Way)

### Start Everything at Once:

```powershell
.\start-sarvasahay.ps1
```

This will start:
- ✅ Backend API (http://localhost:8000)
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ LocalStack (AWS services)
- ✅ Frontend React App (http://localhost:3000)

---

## Step-by-Step Start

### Step 1: Start Backend Services

```bash
# Start Docker containers
docker-compose up -d

# Verify containers are running
docker ps
```

You should see 4 containers:
- `sarvasahay-app` (Backend API)
- `sarvasahay-postgres` (Database)
- `sarvasahay-redis` (Cache)
- `sarvasahay-localstack` (AWS services)

### Step 2: Verify Backend is Running

```bash
# Test API
curl http://localhost:8000/

# Should return:
# {"message":"Welcome to SarvaSahay Platform","version":"0.1.0",...}
```

Or open in browser: http://localhost:8000/docs

### Step 3: Start Frontend

```powershell
# Option A: Use script
.\start-frontend.ps1

# Option B: Manual
cd frontend/web-app
npm start
```

The app will open automatically at: http://localhost:3000

---

## What You Should See

### Backend (http://localhost:8000)
```json
{
  "message": "Welcome to SarvaSahay Platform",
  "version": "0.1.0",
  "status": "operational"
}
```

### Frontend (http://localhost:3000)
```
┌────────────────────────────────────────────────────┐
│ 🇮🇳 SarvaSahay  [Home] [Eligibility] [Documents]  │
│                                    🟢 Online [Login]│
├────────────────────────────────────────────────────┤
│                                                    │
│         🇮🇳 SarvaSahay Platform                    │
│            सरवसहाय मंच                             │
│                                                    │
│  AI-powered government scheme eligibility          │
│  सरकारी योजनाओं के लिए पात्रता जांच              │
│                                                    │
│   [Check Eligibility Now]  [Learn More]           │
│                                                    │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐             │
│  │  ✓  │  │ 📄  │  │ 📋  │  │ 🎯  │             │
│  │Check│  │Upload│  │Apply│  │Track│             │
│  │Elig.│  │ Docs │  │Forms│  │Apps │             │
│  └─────┘  └─────┘  └─────┘  └─────┘             │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  30+              89%             <5s    │    │
│  │  Government       AI Accuracy     Response│    │
│  │  Schemes                          Time    │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Testing the Platform

### 1. Test Backend APIs

#### Profile Service
```bash
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "name": "Test User",
    "age": 30,
    "gender": "male",
    "state": "Maharashtra"
  }'
```

#### Eligibility Check
```bash
curl -X POST http://localhost:8000/api/v1/eligibility/check \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "test-profile-id"
  }'
```

### 2. Test Frontend Flow

#### A. Home Page
1. Open http://localhost:3000
2. Verify welcome message in 3 languages
3. Check backend status (should show "Online" in green)

#### B. Login Flow
1. Click "Login" button
2. Enter phone: `9876543210`
3. Click "Send OTP"
4. Enter OTP: `123456`
5. Click "Verify OTP"
6. Should redirect to profile page

#### C. Navigation
1. Click "Eligibility" → Check eligibility page
2. Click "Documents" → Document upload page
3. Click "Applications" → Applications page
4. Click "Tracking" → Tracking page
5. Click "Help" → FAQ page

#### D. Language Switching
1. Click language icon (🌐) in navbar
2. Select "हिंदी (Hindi)" or "मराठी (Marathi)"
3. UI labels should update (when translations are complete)

---

## Available URLs

### Frontend
- **Home**: http://localhost:3000/
- **Login**: http://localhost:3000/login
- **Profile**: http://localhost:3000/profile
- **Eligibility**: http://localhost:3000/eligibility
- **Documents**: http://localhost:3000/documents
- **Applications**: http://localhost:3000/applications
- **Tracking**: http://localhost:3000/tracking
- **Help**: http://localhost:3000/help

### Backend
- **API Root**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Backend API Endpoints
- **Profiles**: http://localhost:8000/api/v1/profiles
- **Eligibility**: http://localhost:8000/api/v1/eligibility
- **Documents**: http://localhost:8000/api/v1/documents
- **Applications**: http://localhost:8000/api/v1/applications
- **Tracking**: http://localhost:8000/api/v1/tracking
- **SMS**: http://localhost:8000/api/v1/sms
- **Voice**: http://localhost:8000/api/v1/voice
- **Monitoring**: http://localhost:8000/api/v1/monitoring

---

## Stopping the Platform

### Stop Frontend
```bash
# In terminal where npm start is running
Press Ctrl+C
```

### Stop Backend
```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Troubleshooting

### Issue 1: Backend not starting

**Check Docker:**
```bash
docker ps
docker logs sarvasahay-app
```

**Solution:**
```bash
docker-compose down
docker-compose up -d
```

### Issue 2: Frontend shows default React app

**Solution:**
```bash
# Clear browser cache
Ctrl+Shift+Delete → Clear cached files

# Hard reload
Ctrl+Shift+R

# Or open in incognito
Ctrl+Shift+N
```

### Issue 3: Port already in use

**Frontend (3000):**
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Backend (8000):**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 4: Dependencies missing

**Frontend:**
```bash
cd frontend/web-app
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Backend:**
```bash
pip install -r requirements.txt
```

### Issue 5: Database connection error

**Solution:**
```bash
# Restart PostgreSQL container
docker restart sarvasahay-postgres

# Check logs
docker logs sarvasahay-postgres
```

---

## Development Workflow

### Making Changes

#### Frontend Changes:
1. Edit files in `frontend/web-app/src/`
2. Changes auto-reload in browser
3. Check browser console for errors

#### Backend Changes:
1. Edit files in `services/` or `api/`
2. Restart container: `docker-compose restart app`
3. Check logs: `docker logs -f sarvasahay-app`

### Running Tests

#### Backend Tests:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# All tests
pytest
```

#### Frontend Tests:
```bash
cd frontend/web-app
npm test
```

---

## Environment Configuration

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://sarvasahay:password@localhost:5432/sarvasahay

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS (LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=ap-south-1

# API
API_VERSION=v1
DEBUG=True
```

### Frontend (environment variables)
```bash
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# Environment
REACT_APP_ENV=development
```

---

## Production Deployment

### AWS Deployment

See detailed guides:
- `AWS_DEPLOYMENT_STEP_BY_STEP.md` - Complete AWS setup
- `DEPLOY_PRODUCTION_ARCHITECTURE.md` - Architecture guide
- `infrastructure/terraform/` - Infrastructure as code

Quick deploy:
```bash
# Using Terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Using AWS Copilot
copilot init
copilot deploy
```

---

## System Requirements

### Development:
- **OS**: Windows 10/11, macOS, Linux
- **Docker**: 20.10+
- **Node.js**: 16+
- **Python**: 3.9+
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space

### Production:
- **AWS Account** with appropriate permissions
- **ECS Fargate** for container orchestration
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for caching
- **S3** for document storage
- **CloudWatch** for monitoring

---

## Performance Metrics

### Expected Performance:
- **Eligibility Check**: <5 seconds for 30+ schemes
- **Model Inference**: <1 second
- **API Response**: <500ms average
- **Frontend Load**: <3 seconds initial
- **Concurrent Users**: 1,000+
- **Uptime**: 99.5% during business hours

### Monitoring:
```bash
# Check metrics
curl http://localhost:8000/api/v1/monitoring/metrics

# Check health
curl http://localhost:8000/health
```

---

## Support & Documentation

### Documentation Files:
- `README.md` - Project overview
- `FRONTEND_READY.md` - Frontend documentation
- `FRONTEND_FIX_COMPLETE.md` - Fix details
- `START_FRONTEND.md` - Frontend startup guide
- `SARVASAHAY_DEMO.md` - Demo guide
- `AWS_DEPLOYMENT_STEP_BY_STEP.md` - AWS deployment
- `CURRENT_STATUS.md` - Project status

### API Documentation:
- Interactive: http://localhost:8000/docs
- Alternative: http://localhost:8000/redoc

### Architecture:
- `.kiro/specs/sarvasahay-platform/design.md`
- `.kiro/specs/sarvasahay-platform/requirements.md`

---

## Quick Commands Reference

```bash
# Start everything
.\start-sarvasahay.ps1

# Start backend only
docker-compose up -d

# Start frontend only
.\start-frontend.ps1

# Stop everything
docker-compose down

# View logs
docker logs -f sarvasahay-app

# Run tests
pytest

# Check status
docker ps
curl http://localhost:8000/
curl http://localhost:3000/
```

---

## Success Checklist

After starting, verify:

- [ ] Backend API responds at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Frontend loads at http://localhost:3000
- [ ] Frontend shows "🇮🇳 SarvaSahay Platform" header
- [ ] Navbar shows "Online" status (green)
- [ ] Welcome message in 3 languages visible
- [ ] Four feature cards displayed
- [ ] Stats section shows "30+", "89%", "<5s"
- [ ] Login page accessible
- [ ] All routes working (profile, eligibility, etc.)
- [ ] Docker containers running (4 containers)
- [ ] No errors in browser console
- [ ] No errors in terminal

---

## 🎉 You're Ready!

The SarvaSahay platform is now running and ready for development or testing.

**Frontend**: http://localhost:3000
**Backend**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

Happy coding! 🚀
