# Docker Connection Guide for SarvaSahay Platform

## Current Status
✅ Docker Desktop installed  
✅ Environment file (.env) configured  
⏳ Waiting for Docker Desktop to start  

## Steps to Connect

### 1. Start Docker Desktop
- Open Docker Desktop from Windows Start menu
- Wait for the whale icon to appear in system tray
- Status should show "Docker Desktop is running"

### 2. Verify Docker is Running
```bash
docker ps
```
Should show an empty list (no error)

### 3. Start SarvaSahay Platform
```bash
# Option A: Use deployment script (recommended)
.\deploy.ps1

# Option B: Manual start
docker-compose up -d
```

### 4. Check Service Status
```bash
# View all running containers
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Access the Platform

Once services are running:
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Quick Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Restart Services
```bash
docker-compose restart
```

### Check Service Health
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Docker Desktop Won't Start
1. Restart your computer
2. Check Windows Services - ensure "Docker Desktop Service" is running
3. Run Docker Desktop as Administrator

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Stop the process or change port in docker-compose.yml
```

### Services Not Starting
```bash
# Check logs for errors
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up --build
```

### Database Connection Issues
```bash
# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

## What Gets Started

The platform starts these services:

1. **PostgreSQL Database** (port 5432)
   - Stores user profiles, schemes, applications
   - Persistent data storage

2. **Redis Cache** (port 6379)
   - Caches frequently accessed data
   - Session management

3. **SarvaSahay API** (port 8000)
   - Main application server
   - REST API endpoints
   - AI/ML eligibility engine

4. **Nginx** (ports 80/443) - Optional
   - Reverse proxy
   - Load balancing

## Next Steps After Connection

1. **Test the API**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Create a Test Profile**
   ```bash
   curl -X POST http://localhost:8000/api/v1/profiles \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "age": 35}'
   ```

3. **Run Tests**
   ```bash
   # Unit tests
   python -m pytest tests/unit/ -v

   # Integration tests (requires services running)
   python -m pytest tests/integration/ -v
   ```

4. **Explore API Documentation**
   - Open browser: http://localhost:8000/docs
   - Interactive Swagger UI with all endpoints

## Development Workflow

```bash
# 1. Start services
docker-compose up -d

# 2. Make code changes
# Edit files in your IDE

# 3. Restart to apply changes
docker-compose restart app

# 4. View logs
docker-compose logs -f app

# 5. Run tests
python -m pytest tests/

# 6. Stop when done
docker-compose down
```

## Performance Tips

- **First Start**: Takes 2-5 minutes (downloads images, builds containers)
- **Subsequent Starts**: Takes 30-60 seconds
- **Memory**: Requires ~4GB RAM minimum
- **Disk**: Requires ~10GB free space

## Support

- **Documentation**: See README.md
- **Troubleshooting**: See TROUBLESHOOTING.md
- **System Status**: See SYSTEM_VALIDATION_REPORT.md
