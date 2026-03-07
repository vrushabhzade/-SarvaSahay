# Fix SarvaSahay Frontend - Quick Guide

## Problem
When you open http://localhost:3000, you see the default React app instead of SarvaSahay.

## Solution

The issue is that some page files are missing or not properly imported. Follow these steps:

### Step 1: Stop the current server
```bash
# Press Ctrl+C in the terminal where npm start is running
```

### Step 2: Navigate to the frontend directory
```bash
cd frontend/web-app
```

### Step 3: Check for errors
```bash
npm start
```

Look for any compilation errors in the terminal. Common issues:

1. **Missing imports** - Some pages might not be created yet
2. **TypeScript errors** - Type mismatches
3. **Module not found** - Missing dependencies

### Step 4: If you see "Module not found" errors

The placeholder pages need to be created. Run this command:

```bash
# Create all missing page files
echo "import React from 'react'; import { Container, Typography, Paper, Box } from '@mui/material'; const ProfilePage: React.FC = () => { return ( <Container maxWidth=\"md\"><Box sx={{ mt: 4 }}><Paper sx={{ p: 4 }}><Typography variant=\"h4\" gutterBottom>My Profile</Typography><Typography>Profile management coming soon...</Typography></Paper></Box></Container> ); }; export default ProfilePage;" > src/pages/ProfilePage.tsx

echo "import React from 'react'; import { Container, Typography, Paper, Box } from '@mui/material'; const EligibilityPage: React.FC = () => { return ( <Container maxWidth=\"md\"><Box sx={{ mt: 4 }}><Paper sx={{ p: 4 }}><Typography variant=\"h4\" gutterBottom>Check Eligibility</Typography><Typography>Eligibility checker coming soon...</Typography></Paper></Box></Container> ); }; export default EligibilityPage;" > src/pages/EligibilityPage.tsx

echo "import React from 'react'; import { Container, Typography, Paper, Box } from '@mui/material'; const DocumentsPage: React.FC = () => { return ( <Container maxWidth=\"md\"><Box sx={{ mt: 4 }}><Paper sx={{ p: 4 }}><Typography variant=\"h4\" gutterBottom>My Documents</Typography><Typography>Document management coming soon...</Typography></Paper></Box></Container> ); }; export default DocumentsPage;" > src/pages/DocumentsPage.tsx

echo "import React from 'react'; import { Container, Typography, Paper, Box } from '@mui/material'; const ApplicationsPage: React.FC = () => { return ( <Container maxWidth=\"md\"><Box sx={{ mt: 4 }}><Paper sx={{ p: 4 }}><Typography variant=\"h4\" gutterBottom>My Applications</Typography><Typography>Application management coming soon...</Typography></Paper></Box></Container> ); }; export default ApplicationsPage;" > src/pages/ApplicationsPage.tsx

echo "import React from 'react'; import { Container, Typography, Paper, Box } from '@mui/material'; const TrackingPage: React.FC = () => { return ( <Container maxWidth=\"md\"><Box sx={{ mt: 4 }}><Paper sx={{ p: 4 }}><Typography variant=\"h4\" gutterBottom>Track Applications</Typography><Typography>Application tracking coming soon...</Typography></Paper></Box></Container> ); }; export default TrackingPage;" > src/pages/TrackingPage.tsx
```

### Step 5: Install missing dependencies

If Material-UI is not installed:

```bash
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
npm install axios react-router-dom
```

### Step 6: Restart the server

```bash
npm start
```

### Step 7: Clear browser cache

If you still see the old app:
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

Or try opening in incognito/private mode:
```
http://localhost:3000
```

---

## Quick Fix Script

Run this PowerShell script to fix everything:

```powershell
# Navigate to frontend
cd frontend/web-app

# Install dependencies
npm install

# Start the app
npm start
```

---

## Expected Result

After fixing, you should see:
- 🇮🇳 SarvaSahay Platform header
- Welcome message in English, Hindi, Marathi
- 4 feature cards
- Stats section
- Green and orange color scheme

---

## Still Not Working?

### Check 1: Verify files exist
```bash
ls src/pages/
# Should show: HomePage.tsx, LoginPage.tsx, etc.

ls src/components/common/
# Should show: Navbar.tsx, Footer.tsx
```

### Check 2: Check for TypeScript errors
```bash
npm run build
# This will show all compilation errors
```

### Check 3: Check browser console
1. Open http://localhost:3000
2. Press F12 to open DevTools
3. Check Console tab for errors
4. Check Network tab to see if files are loading

### Check 4: Verify backend is running
```bash
# In a new terminal
curl http://localhost:8000/
# Should return: {"message":"Welcome to SarvaSahay Platform"...}
```

---

## Manual Fix (If script doesn't work)

1. **Delete node_modules and reinstall:**
```bash
cd frontend/web-app
rm -rf node_modules package-lock.json
npm install
npm start
```

2. **Use a different port:**
```bash
# If port 3000 is in use
set PORT=3001
npm start
```

3. **Check if another React app is running:**
```bash
# Windows
netstat -ano | findstr :3000
# Kill the process if found
taskkill /PID <PID> /F
```

---

## Contact for Help

If none of these work, the issue might be:
1. Another app is running on port 3000
2. Browser cache is stuck
3. Node modules are corrupted
4. TypeScript compilation errors

Check the terminal output when running `npm start` for specific error messages.
