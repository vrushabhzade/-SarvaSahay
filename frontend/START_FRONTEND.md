# Start SarvaSahay Frontend

## ✅ Setup Complete!

All dependencies are installed and the SarvaSahay interface is ready.

## Quick Start

### Option 1: Using the startup script (Recommended)

```powershell
# From the root directory
.\start-frontend.ps1
```

### Option 2: Manual start

```bash
# Navigate to frontend directory
cd frontend/web-app

# Start the development server
npm start
```

The app will automatically open in your browser at: **http://localhost:3000**

---

## What You Should See

When the app loads, you should see:

1. **🇮🇳 SarvaSahay Platform** header with green navigation bar
2. **Welcome message** in English, Hindi (हिंदी), and Marathi (मराठी)
3. **Four feature cards**:
   - Check Eligibility (पात्रता जांचें)
   - Upload Documents (दस्तावेज़ अपलोड करें)
   - Apply for Schemes (योजनाओं के लिए आवेदन करें)
   - Track Applications (आवेदन ट्रैक करें)
4. **Stats section** showing:
   - 30+ Government Schemes
   - 89% AI Accuracy
   - <5s Response Time
5. **Multi-channel access** buttons (SMS, Call, Help)
6. **Footer** with links and contact info

---

## Backend Connection Status

The navbar shows the backend connection status:
- **Green "Online"** chip = Backend connected (http://localhost:8000)
- **Red "Offline"** chip = Backend not running
- **Gray "Checking..."** = Connecting to backend

### To start the backend:

```bash
# In a separate terminal
docker-compose up -d
```

Or use the all-in-one script:

```powershell
.\start-sarvasahay.ps1
```

---

## Available Routes

Once the app is running, you can navigate to:

- **/** - Home page
- **/login** - Login with OTP
- **/profile** - User profile (requires login)
- **/eligibility** - Check scheme eligibility (requires login)
- **/documents** - Upload documents (requires login)
- **/applications** - View applications (requires login)
- **/tracking** - Track application status (requires login)
- **/help** - Help and FAQ

---

## Troubleshooting

### Issue: Port 3000 already in use

```bash
# Find and kill the process
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use a different port
set PORT=3001
npm start
```

### Issue: Still seeing default React app

1. **Clear browser cache:**
   - Press F12 to open DevTools
   - Right-click refresh button
   - Select "Empty Cache and Hard Reload"

2. **Or open in incognito mode:**
   - Chrome: Ctrl+Shift+N
   - Firefox: Ctrl+Shift+P
   - Edge: Ctrl+Shift+N

### Issue: Compilation errors

```bash
# Reinstall dependencies
cd frontend/web-app
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm start
```

### Issue: Backend not connecting

1. Check if Docker containers are running:
```bash
docker ps
```

2. Start backend if not running:
```bash
docker-compose up -d
```

3. Test backend directly:
```bash
curl http://localhost:8000/
```

---

## Development Tips

### Hot Reload
The app uses React hot reload - any changes you make to the code will automatically refresh in the browser.

### API Testing
- Backend API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Language Switching
Click the language icon (🌐) in the navbar to switch between:
- English
- हिंदी (Hindi)
- मराठी (Marathi)

Note: Full translations will be implemented in the next phase.

---

## Next Steps

The frontend is now running with:
- ✅ React 18 + TypeScript
- ✅ Material-UI components
- ✅ React Router for navigation
- ✅ Axios for API calls
- ✅ Multi-language support structure
- ✅ Authentication flow
- ✅ All 8 pages created

### To implement:
1. Complete profile form with all fields
2. Implement eligibility checker with AI integration
3. Add document upload with OCR preview
4. Build application submission forms
5. Create real-time tracking dashboard
6. Add Redux state management
7. Implement full i18n translations
8. Add form validation with React Hook Form

---

## Color Scheme

The app uses government-inspired colors:
- **Primary Green**: #2E7D32 (Government)
- **Secondary Orange**: #FF6F00 (India)
- **Success**: #4CAF50
- **Error**: #F44336
- **Warning**: #FF9800
- **Info**: #2196F3

---

## Support

If you encounter any issues:
1. Check the browser console (F12) for errors
2. Check the terminal for compilation errors
3. Verify backend is running on port 8000
4. Ensure all dependencies are installed

For more help, see: `frontend/web-app/FIX_INSTRUCTIONS.md`
