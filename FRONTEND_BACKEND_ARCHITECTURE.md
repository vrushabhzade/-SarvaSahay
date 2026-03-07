# SarvaSahay - Frontend & Backend Architecture

## 📊 Current Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Web App (React)  │  Mobile App (React Native)  │  Admin Panel │
│  - User Portal    │  - iOS/Android              │  - Dashboard │
│  - Marathi/Hindi  │  - Offline Support          │  - Analytics │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/REST API
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / LOAD BALANCER                │
│                    (AWS ALB / API Gateway)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND LAYER                           │
│                      (FastAPI - Python)                         │
├─────────────────────────────────────────────────────────────────┤
│  Profile Service  │  Eligibility Engine  │  Document Processor │
│  Tracking Service │  Auto Application    │  Notification Svc   │
│  SMS Interface    │  Voice Interface     │  Monitoring         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL       │  Redis Cache         │  S3 Storage         │
│  (User Data)      │  (Sessions)          │  (Documents)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend (Current Implementation)

### Technology Stack
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Storage:** AWS S3
- **ML/AI:** XGBoost, Tesseract OCR, OpenCV
- **Deployment:** Docker, AWS ECS Fargate

### Backend Services (Already Implemented)

#### 1. **Profile Service**
- **Location:** `services/profile_service.py`
- **Routes:** `api/routes/profile_routes.py`
- **Features:**
  - User profile creation and management
  - Profile validation
  - Multi-language support (Marathi, Hindi, English)

#### 2. **Eligibility Engine**
- **Location:** `services/eligibility_engine.py`, `ml/models/eligibility_model.py`
- **Routes:** `api/routes/eligibility_routes.py`
- **Features:**
  - AI-powered scheme matching (XGBoost)
  - 30+ government schemes
  - <5 second response time
  - 89% accuracy

#### 3. **Document Processor**
- **Location:** `services/document_processor.py`, `services/document_validator.py`
- **Routes:** `api/routes/document_routes.py`
- **Features:**
  - OCR with Tesseract (Hindi, Marathi support)
  - Document validation (Aadhaar, PAN, etc.)
  - Image preprocessing with OpenCV

#### 4. **Auto Application Service**
- **Location:** `services/auto_application_service.py`
- **Routes:** `api/routes/application_routes.py`
- **Features:**
  - Auto-fill government forms
  - Form template management
  - Government API integration

#### 5. **Tracking & Notifications**
- **Location:** `services/tracking_service.py`, `services/notification_service.py`
- **Routes:** `api/routes/tracking_routes.py`
- **Features:**
  - Real-time application tracking
  - Multi-channel notifications (SMS, Email, Push)
  - Status updates

#### 6. **SMS Interface**
- **Location:** `services/sms_interface.py`
- **Routes:** `api/routes/sms_routes.py`
- **Features:**
  - Text-based interactions
  - Commands: CHECK, STATUS, HELP, SCHEMES
  - Low-literacy user support

#### 7. **Voice Interface**
- **Location:** `services/voice_interface.py`
- **Routes:** `api/routes/voice_routes.py`
- **Features:**
  - Voice call handling
  - Speech-to-text (Hindi, Marathi)
  - IVR integration

#### 8. **Monitoring & Analytics**
- **Location:** `shared/monitoring/`
- **Routes:** `api/routes/monitoring_routes.py`
- **Features:**
  - Performance metrics
  - Resource monitoring
  - Alert management

### Backend API Endpoints

```
Base URL: http://localhost:8000/api/v1

Authentication:
POST   /auth/login              - Login with OTP
POST   /auth/verify             - Verify OTP
POST   /auth/refresh            - Refresh token

Profiles:
POST   /profiles                - Create profile
GET    /profiles/{id}           - Get profile
PUT    /profiles/{id}           - Update profile
DELETE /profiles/{id}           - Delete profile

Eligibility:
POST   /eligibility/check       - Check eligibility
GET    /eligibility/schemes     - List schemes
GET    /eligibility/schemes/{id} - Get scheme details

Documents:
POST   /documents/upload        - Upload document
POST   /documents/ocr           - Extract text
POST   /documents/validate      - Validate document
GET    /documents/{id}          - Get document

Applications:
POST   /applications            - Submit application
GET    /applications/{id}       - Get application
PUT    /applications/{id}       - Update application
POST   /applications/auto-fill  - Auto-fill form

Tracking:
GET    /tracking/{id}           - Track application
GET    /tracking/{id}/history   - Get history
POST   /tracking/subscribe      - Subscribe to updates

SMS:
POST   /sms/send                - Send SMS
POST   /sms/receive             - Receive SMS (webhook)

Voice:
POST   /voice/call              - Initiate call
POST   /voice/webhook           - Voice webhook

Monitoring:
GET    /monitoring/health       - Health check
GET    /monitoring/metrics      - System metrics
GET    /monitoring/alerts       - Active alerts
```

---

## 🎨 Frontend (To Be Implemented)

### Recommended Technology Stack

#### 1. **Web Application**
- **Framework:** React 18 with TypeScript
- **UI Library:** Material-UI (MUI) or Chakra UI
- **State Management:** Redux Toolkit or Zustand
- **API Client:** Axios or React Query
- **Routing:** React Router v6
- **Forms:** React Hook Form + Yup validation
- **i18n:** react-i18next (Marathi, Hindi, English)
- **Build Tool:** Vite

#### 2. **Mobile Application**
- **Framework:** React Native with TypeScript
- **UI Library:** React Native Paper or NativeBase
- **Navigation:** React Navigation
- **State Management:** Redux Toolkit
- **Offline Support:** Redux Persist + AsyncStorage
- **Push Notifications:** Firebase Cloud Messaging

#### 3. **Admin Dashboard**
- **Framework:** React with TypeScript
- **UI Library:** Ant Design or Material-UI
- **Charts:** Recharts or Chart.js
- **Tables:** TanStack Table (React Table)

---

## 🚀 Frontend Implementation Plan

### Phase 1: Web Application (Priority)

#### Project Structure
```
frontend/web-app/
├── public/
│   ├── index.html
│   ├── manifest.json
│   └── locales/
│       ├── en.json
│       ├── hi.json
│       └── mr.json
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Navbar.tsx
│   │   │   └── LanguageSelector.tsx
│   │   ├── profile/
│   │   │   ├── ProfileForm.tsx
│   │   │   └── ProfileCard.tsx
│   │   ├── eligibility/
│   │   │   ├── EligibilityChecker.tsx
│   │   │   ├── SchemeCard.tsx
│   │   │   └── SchemeList.tsx
│   │   ├── documents/
│   │   │   ├── DocumentUpload.tsx
│   │   │   └── DocumentList.tsx
│   │   ├── applications/
│   │   │   ├── ApplicationForm.tsx
│   │   │   └── ApplicationStatus.tsx
│   │   └── tracking/
│   │       ├── TrackingTimeline.tsx
│   │       └── StatusCard.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Profile.tsx
│   │   ├── Eligibility.tsx
│   │   ├── Documents.tsx
│   │   ├── Applications.tsx
│   │   ├── Tracking.tsx
│   │   └── Help.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── profile.ts
│   │   ├── eligibility.ts
│   │   └── documents.ts
│   ├── store/
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── profileSlice.ts
│   │   │   └── eligibilitySlice.ts
│   │   └── store.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProfile.ts
│   │   └── useEligibility.ts
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── validators.ts
│   │   └── formatters.ts
│   ├── types/
│   │   ├── profile.ts
│   │   ├── scheme.ts
│   │   └── application.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── i18n.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

#### Key Features

**1. Home Page**
- Welcome message in user's language
- Quick eligibility check
- Featured schemes
- Success stories

**2. Profile Management**
- Multi-step form (Personal, Family, Income, Documents)
- Real-time validation
- Auto-save functionality
- Language preference

**3. Eligibility Checker**
- Simple questionnaire
- Real-time scheme matching
- Estimated benefits display
- Scheme comparison

**4. Document Upload**
- Drag-and-drop interface
- Image preview
- OCR progress indicator
- Document validation feedback

**5. Application Submission**
- Auto-filled forms
- Document attachment
- Review before submit
- Submission confirmation

**6. Application Tracking**
- Timeline view
- Status updates
- Notifications
- Download certificates

**7. Help & Support**
- FAQ in multiple languages
- Video tutorials
- SMS/Voice interface info
- Contact support

---

## 📱 Mobile App Features

### Core Screens
1. **Splash Screen** - Language selection
2. **Onboarding** - Tutorial (3-4 screens)
3. **Login/Register** - OTP-based authentication
4. **Dashboard** - Quick actions, notifications
5. **Profile** - View/edit profile
6. **Eligibility** - Check schemes
7. **Documents** - Camera integration, upload
8. **Applications** - Submit and track
9. **Notifications** - Push notifications
10. **Settings** - Language, notifications, logout

### Mobile-Specific Features
- **Offline Mode:** Cache data for offline access
- **Camera Integration:** Direct document capture
- **Push Notifications:** Real-time updates
- **Biometric Auth:** Fingerprint/Face ID
- **Voice Input:** Speech-to-text for forms
- **Share:** Share scheme info via WhatsApp

---

## 🎯 User Flows

### Flow 1: New User Registration
```
1. Open app/website
2. Select language (Marathi/Hindi/English)
3. Enter phone number
4. Verify OTP
5. Complete profile (guided form)
6. Upload documents
7. Check eligibility
8. View eligible schemes
```

### Flow 2: Check Eligibility
```
1. Login
2. Go to Eligibility page
3. Answer questions (or use saved profile)
4. View matching schemes
5. See estimated benefits
6. Apply for scheme
```

### Flow 3: Apply for Scheme
```
1. Select scheme
2. Review requirements
3. Upload missing documents
4. Review auto-filled form
5. Submit application
6. Receive confirmation
7. Track status
```

### Flow 4: Track Application
```
1. Go to Tracking page
2. View all applications
3. Click on application
4. See timeline/status
5. Receive notifications
6. Download certificate (if approved)
```

---

## 🌐 Multi-Language Support

### Supported Languages
- **Marathi (मराठी)** - Primary for Maharashtra
- **Hindi (हिंदी)** - National language
- **English** - Secondary

### Implementation
```typescript
// i18n configuration
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: require('./locales/en.json') },
      hi: { translation: require('./locales/hi.json') },
      mr: { translation: require('./locales/mr.json') }
    },
    lng: 'mr', // Default to Marathi
    fallbackLng: 'en',
    interpolation: { escapeValue: false }
  });
```

### Translation Keys
```json
{
  "welcome": "Welcome to SarvaSahay",
  "checkEligibility": "Check Eligibility",
  "myProfile": "My Profile",
  "myApplications": "My Applications",
  "schemes": "Government Schemes",
  "documents": "My Documents",
  "help": "Help & Support"
}
```

---

## 🔐 Authentication Flow

### Backend (Already Implemented)
```python
# OTP-based authentication
POST /api/v1/auth/login
{
  "phone": "+91-9876543210"
}

# Response: OTP sent via SMS

POST /api/v1/auth/verify
{
  "phone": "+91-9876543210",
  "otp": "123456"
}

# Response: JWT token
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": { ... }
}
```

### Frontend Implementation
```typescript
// Auth service
export const authService = {
  async login(phone: string) {
    const response = await api.post('/auth/login', { phone });
    return response.data;
  },
  
  async verifyOTP(phone: string, otp: string) {
    const response = await api.post('/auth/verify', { phone, otp });
    localStorage.setItem('token', response.data.access_token);
    return response.data;
  },
  
  async logout() {
    localStorage.removeItem('token');
  }
};
```

---

## 📊 State Management

### Redux Store Structure
```typescript
{
  auth: {
    user: User | null,
    token: string | null,
    isAuthenticated: boolean,
    loading: boolean
  },
  profile: {
    data: Profile | null,
    loading: boolean,
    error: string | null
  },
  eligibility: {
    schemes: Scheme[],
    eligibleSchemes: Scheme[],
    loading: boolean
  },
  applications: {
    list: Application[],
    current: Application | null,
    loading: boolean
  },
  documents: {
    list: Document[],
    uploading: boolean
  }
}
```

---

## 🎨 UI/UX Design Principles

### For Rural Users
1. **Simple Navigation:** Large buttons, clear labels
2. **Visual Feedback:** Loading indicators, success messages
3. **Minimal Text:** Use icons and images
4. **Voice Support:** Voice input for forms
5. **Offline Support:** Work without internet
6. **Low Bandwidth:** Optimized images, lazy loading

### Color Scheme
- **Primary:** #2E7D32 (Green - Government)
- **Secondary:** #FF6F00 (Orange - India)
- **Success:** #4CAF50
- **Error:** #F44336
- **Warning:** #FF9800
- **Info:** #2196F3

---

## 📦 Deployment Architecture

### Frontend Deployment Options

#### Option 1: AWS S3 + CloudFront (Static Hosting)
```bash
# Build frontend
npm run build

# Deploy to S3
aws s3 sync dist/ s3://sarvasahay-frontend

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

#### Option 2: Vercel (Recommended for Quick Deploy)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### Option 3: AWS Amplify
```bash
# Connect GitHub repo
# Auto-deploy on push to main branch
```

### Mobile App Deployment
- **iOS:** App Store (requires Apple Developer account)
- **Android:** Google Play Store
- **Beta Testing:** TestFlight (iOS), Firebase App Distribution (Android)

---

## 🔗 API Integration

### API Client Setup
```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 📈 Performance Optimization

### Frontend
- Code splitting with React.lazy()
- Image optimization (WebP format)
- Lazy loading for images
- Service Worker for caching
- Bundle size optimization
- CDN for static assets

### Backend (Already Optimized)
- Redis caching
- Database query optimization
- Connection pooling
- Async processing
- Load balancing

---

## 🧪 Testing Strategy

### Frontend Testing
```bash
# Unit tests (Jest + React Testing Library)
npm run test

# E2E tests (Cypress)
npm run test:e2e

# Coverage
npm run test:coverage
```

### Backend Testing (Already Implemented)
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Property-based tests: `tests/property/`
- E2E tests: `tests/e2e/`

---

## 📝 Next Steps

### Immediate Actions
1. ✅ Backend is complete and running
2. ⏳ Create React web application
3. ⏳ Implement authentication flow
4. ⏳ Build profile management UI
5. ⏳ Create eligibility checker interface
6. ⏳ Implement document upload UI
7. ⏳ Build application tracking dashboard

### Future Enhancements
- Progressive Web App (PWA)
- React Native mobile app
- Admin dashboard
- Analytics dashboard
- WhatsApp integration
- Chatbot interface

---

## 🔗 Resources

- **Backend API Docs:** http://localhost:8000/docs
- **GitHub Repository:** https://github.com/vrushabhzade/-SarvaSahay.git
- **API Guide:** [API_INTERFACE_GUIDE.md](./API_INTERFACE_GUIDE.md)
- **Deployment Guide:** [AWS_DEPLOYMENT_STEP_BY_STEP.md](./AWS_DEPLOYMENT_STEP_BY_STEP.md)
