# ⚠️ IMPORTANT: Starting SarvaSahay Frontend

## Problem You Just Encountered

You saw "TradeLink" app instead of SarvaSahay because:
1. A different React app (TradeLink) was running on port 3000
2. You need to stop that app first
3. Then start SarvaSahay from the correct directory

---

## Solution: Start SarvaSahay Frontend

### Step 1: Stop Any Running React Apps

```powershell
# Find Node processes
Get-Process -Name node -ErrorAction SilentlyContinue

# Stop all Node processes (this stops TradeLink or any other React app)
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 2: Navigate to Correct Directory

Make sure you're in the **"Rural Ai prototype"** directory (the parent folder), NOT in `-SarvaSahay` subfolder.

```powershell
# Check current location
pwd

# Should show: C:\Users\VRUSHABH\OneDrive\Music\Desktop\KIRO PROJECT\Rural Ai prototype
```

### Step 3: Start SarvaSahay Frontend

```powershell
# Navigate to frontend
cd frontend/web-app

# Start the app
npm start
```

The browser will automatically open at: **http://localhost:3000**

---

## What You Should See

### ✅ CORRECT - SarvaSahay:
```
┌────────────────────────────────────────────────────┐
│ 🇮🇳 SarvaSahay  [Home] [Eligibility] [Documents]  │ ← Green navbar
│                                    🌐 [Login]      │
├────────────────────────────────────────────────────┤
│         🇮🇳 SarvaSahay Platform                    │
│            सरवसहाय मंच                             │
│  AI-powered government scheme eligibility          │
└────────────────────────────────────────────────────┘
```

### ❌ WRONG - TradeLink:
```
┌────────────────────────────────────────────────────┐
│ TradeLink  [Products] [Login] [Sign Up]           │
│                                                    │
│         Welcome to TradeLink                       │
│  AI-powered local trade marketplace...            │
└────────────────────────────────────────────────────┘
```

---

## Directory Structure Explanation

Your workspace has this structure:

```
Rural Ai prototype/                    ← YOU ARE HERE (correct location)
├── frontend/
│   └── web-app/                      ← SarvaSahay frontend
│       ├── src/
│       │   ├── App.tsx              ← SarvaSahay app
│       │   └── pages/
│       └── package.json
│
├── -SarvaSahay/                      ← Backend only (no frontend here!)
│   ├── services/
│   ├── api/
│   ├── docker-compose.yml
│   └── main.py
│
└── [Other projects like TradeLink]   ← Different apps
```

**Key Point:** The SarvaSahay frontend is in `frontend/web-app` at the ROOT level, not inside `-SarvaSahay` folder!

---

## Quick Commands

### Stop TradeLink (or any other React app):
```powershell
Get-Process -Name node | Stop-Process -Force
```

### Start SarvaSahay:
```powershell
# From "Rural Ai prototype" directory
cd frontend/web-app
npm start
```

### Start SarvaSahay Backend:
```powershell
# From "Rural Ai prototype/-SarvaSahay" directory
cd -SarvaSahay
docker-compose up -d
```

---

## Troubleshooting

### Issue: Still seeing TradeLink

**Solution 1: Clear browser cache**
```
1. Press Ctrl+Shift+Delete
2. Clear cached files
3. Refresh (Ctrl+R)
```

**Solution 2: Hard reload**
```
Press Ctrl+Shift+R
```

**Solution 3: Incognito mode**
```
Press Ctrl+Shift+N
Navigate to http://localhost:3000
```

### Issue: Port 3000 already in use

**Solution:**
```powershell
# Find what's using port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess

# Stop it
Stop-Process -Id <PID> -Force
```

### Issue: Wrong directory

**Check where you are:**
```powershell
pwd
# Should show: ...Rural Ai prototype

# NOT: ...Rural Ai prototype\-SarvaSahay
```

**Navigate to correct location:**
```powershell
# If you're in -SarvaSahay, go up one level
cd ..

# Verify frontend exists
Test-Path frontend/web-app
# Should return: True
```

---

## Summary

1. **Stop TradeLink**: `Get-Process -Name node | Stop-Process -Force`
2. **Go to correct directory**: `cd "Rural Ai prototype"` (parent folder)
3. **Start SarvaSahay**: `cd frontend/web-app; npm start`
4. **Open browser**: http://localhost:3000
5. **Verify**: You should see "🇮🇳 SarvaSahay Platform" NOT "TradeLink"

---

## Backend Connection

To connect frontend to backend:

```powershell
# In a separate terminal, navigate to backend
cd "Rural Ai prototype/-SarvaSahay"

# Start backend
docker-compose up -d

# Verify backend is running
curl http://localhost:8000/
```

The frontend will show "Online" status in the navbar when backend is connected.

---

## Need Help?

If you're still seeing TradeLink:
1. Make sure you stopped ALL Node processes
2. Make sure you're in the correct directory (parent "Rural Ai prototype")
3. Clear your browser cache completely
4. Try opening in incognito mode

The SarvaSahay app is ready and working - you just need to start it from the correct location!
