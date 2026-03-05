# SarvaSahay Platform - Troubleshooting Guide

## Quick Fixes for "Localhost Not Working"

### Step 1: Run Diagnostic Tool

```bash
python diagnose.py
```

This will check for common issues and provide specific fixes.

### Step 2: Try Simple Startup

**Windows:**
```cmd
start_local.bat
```

**Linux/Mac:**
```bash
python start_local.py
```

**Or directly:**
```bash
python main.py
```

---

## Common Issues and Solutions

### Issue 1: Port 8000 Already in Use

**Symptoms:**
- Error: "Address already in use"
- Cannot bind to port 8000

**Solution:**

**Windows:**
```cmd
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Alternative:** Change the port in `.env`:
```env
API_PORT=8001
```

---

### Issue 2: Missing Dependencies

**Symptoms:**
- ImportError: No module named 'fastapi'
- ModuleNotFoundError

**Solution:**

```bash
# Activate virtual environment first
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Or install minimal dependencies
pip install fastapi uvicorn pydantic sqlalchemy
```

---

### Issue 3: Python Version Too Old

**Symptoms:**
- SyntaxError in code
- "Python 3.11+ required"

**Solution:**

1. Check your Python version:
```bash
python --version
```

2. If < 3.11, install Python 3.11 or higher from [python.org](https://www.python.org/downloads/)

3. Create new virtual environment:
```bash
python3.11 -m venv .venv
```

---

### Issue 4: Database Connection Failed

**Symptoms:**
- "Could not connect to database"
- SQLAlchemy errors

**Solution:**

For local development, use SQLite (no setup required):

```env
# In .env file
DATABASE_URL=sqlite:///./sarvasahay_local.db
```

For PostgreSQL:
```bash
# Start PostgreSQL with Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:14

# Update .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/sarvasahay_db
```

---

### Issue 5: Redis Connection Failed

**Symptoms:**
- "Could not connect to Redis"
- Connection refused on port 6379

**Solution:**

Redis is optional for local development. The server will start without it.

To use Redis:
```bash
# Start Redis with Docker
docker run -d -p 6379:6379 redis:7-alpine

# Update .env
REDIS_URL=redis://localhost:6379/0
```

---

### Issue 6: Import Errors from Routes

**Symptoms:**
- "Could not import routes"
- ModuleNotFoundError for api.routes

**Solution:**

1. Ensure you're in the project root directory
2. Check if `api/routes/__init__.py` exists
3. Try running from project root:

```bash
# Make sure you're in the right directory
cd path/to/sarvasahay-platform

# Run the server
python main.py
```

---

### Issue 7: Environment Variables Not Set

**Symptoms:**
- "SECRET_KEY not set"
- Configuration errors

**Solution:**

Create `.env` file in project root:

```env
# Minimal configuration for local development
DATABASE_URL=sqlite:///./sarvasahay_local.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

---

### Issue 8: Permission Denied

**Symptoms:**
- "Permission denied" when starting server
- Cannot bind to port

**Solution:**

**Windows:** Run as Administrator

**Linux/Mac:**
```bash
# Don't use port 80 or 443 (requires root)
# Use port 8000 instead

# Or use sudo (not recommended)
sudo python main.py
```

---

### Issue 9: Firewall Blocking

**Symptoms:**
- Server starts but cannot access from browser
- Connection timeout

**Solution:**

**Windows:**
1. Open Windows Defender Firewall
2. Allow Python through firewall
3. Or temporarily disable firewall for testing

**Linux:**
```bash
# Allow port 8000
sudo ufw allow 8000
```

---

### Issue 10: Virtual Environment Not Activated

**Symptoms:**
- Packages installed but still getting ImportError
- Wrong Python version

**Solution:**

Always activate virtual environment first:

**Windows:**
```cmd
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

---

## Testing the Server

Once the server starts, test these endpoints:

### 1. Root Endpoint
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Welcome to SarvaSahay Platform",
  "version": "1.0.0",
  "environment": "development"
}
```

### 2. Health Check
```bash
curl http://localhost:8000/health
```

### 3. API Documentation
Open in browser: http://localhost:8000/docs

---

## Still Not Working?

### Collect Debug Information

Run these commands and share the output:

```bash
# 1. Python version
python --version

# 2. Installed packages
pip list

# 3. Environment check
python diagnose.py

# 4. Try starting with verbose logging
python main.py

# 5. Check if server is actually running
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000
```

### Check Logs

Look for error messages in:
- Terminal output
- `logs/` directory (if exists)
- System logs

### Common Error Messages

**"No module named 'shared'"**
- You're not in the project root directory
- Solution: `cd` to project root

**"Address already in use"**
- Port 8000 is taken
- Solution: Kill the process or change port

**"Cannot connect to database"**
- Database not running
- Solution: Use SQLite or start PostgreSQL

**"Permission denied"**
- Port requires elevated privileges
- Solution: Use port 8000 or higher

---

## Alternative: Docker Deployment

If local setup is too complex, use Docker:

```bash
# Create .env file first
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Access at http://localhost:8000
```

---

## Getting Help

If you're still stuck:

1. Run `python diagnose.py` and share the output
2. Share the exact error message
3. Share your Python version: `python --version`
4. Share your OS: Windows/Linux/Mac
5. Check the [SYSTEM_VALIDATION_REPORT.md](SYSTEM_VALIDATION_REPORT.md) for known issues

---

## Quick Reference

### Start Server
```bash
# Simple
python main.py

# With startup script
python start_local.py

# Windows batch file
start_local.bat
```

### Check Status
```bash
# Diagnostic tool
python diagnose.py

# Health check
curl http://localhost:8000/health
```

### Stop Server
- Press `CTRL+C` in terminal
- Or kill the process

### View Logs
- Check terminal output
- Look in `logs/` directory

---

*Last Updated: March 2, 2026*
