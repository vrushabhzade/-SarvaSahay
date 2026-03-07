# SarvaSahay Platform - API Interface Guide

## 🌐 Access URLs

### Local Development
- **Base URL:** http://localhost:8000
- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

### Production (After AWS Deployment)
- **Base URL:** https://api.sarvasahay.gov.in
- **API Version:** v1 (prefix: `/api/v1`)

---

## 📱 Available API Interfaces

### 1. Health & Monitoring
**Base Path:** `/api/v1/health`

- `GET /api/v1/health` - System health check
- `GET /api/v1/health/detailed` - Detailed health status
- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/alerts` - Active alerts

### 2. User Profile Management
**Base Path:** `/api/v1/profiles`

- `POST /api/v1/profiles` - Create user profile
- `GET /api/v1/profiles/{profile_id}` - Get profile details
- `PUT /api/v1/profiles/{profile_id}` - Update profile
- `DELETE /api/v1/profiles/{profile_id}` - Delete profile
- `GET /api/v1/profiles/{profile_id}/schemes` - Get eligible schemes

**Example Profile Data:**
```json
{
  "name": "राज कुमार",
  "age": 35,
  "gender": "male",
  "state": "Maharashtra",
  "district": "Pune",
  "income": 50000,
  "caste": "OBC",
  "occupation": "farmer",
  "land_holding": 2.5,
  "family_size": 5,
  "phone": "+91-9876543210",
  "language": "marathi"
}
```

### 3. Eligibility Engine
**Base Path:** `/api/v1/eligibility`

- `POST /api/v1/eligibility/check` - Check scheme eligibility
- `GET /api/v1/eligibility/schemes` - List all schemes
- `GET /api/v1/eligibility/schemes/{scheme_id}` - Get scheme details
- `POST /api/v1/eligibility/bulk-check` - Bulk eligibility check

**Example Request:**
```json
{
  "profile_id": "user_123",
  "schemes": ["PM-KISAN", "PMAY", "MGNREGA"]
}
```

**Example Response:**
```json
{
  "profile_id": "user_123",
  "eligible_schemes": [
    {
      "scheme_id": "PM-KISAN",
      "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
      "eligibility_score": 0.95,
      "estimated_benefit": "₹6,000/year",
      "requirements": ["Aadhaar", "Land Records"],
      "application_deadline": "2026-03-31"
    }
  ],
  "processing_time": "2.3s"
}
```

### 4. Document Processing
**Base Path:** `/api/v1/documents`

- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/{document_id}` - Get document details
- `POST /api/v1/documents/ocr` - Extract text from document
- `POST /api/v1/documents/validate` - Validate document
- `DELETE /api/v1/documents/{document_id}` - Delete document

**Supported Documents:**
- Aadhaar Card
- PAN Card
- Ration Card
- Land Records (7/12)
- Income Certificate
- Caste Certificate
- Bank Passbook

### 5. Auto Application Service
**Base Path:** `/api/v1/applications`

- `POST /api/v1/applications` - Submit application
- `GET /api/v1/applications/{application_id}` - Get application status
- `PUT /api/v1/applications/{application_id}` - Update application
- `POST /api/v1/applications/auto-fill` - Auto-fill application form
- `GET /api/v1/applications/user/{user_id}` - Get user applications

**Example Application:**
```json
{
  "profile_id": "user_123",
  "scheme_id": "PM-KISAN",
  "documents": ["doc_aadhaar_123", "doc_land_456"],
  "auto_submit": true
}
```

### 6. Tracking & Notifications
**Base Path:** `/api/v1/tracking`

- `GET /api/v1/tracking/{application_id}` - Track application
- `GET /api/v1/tracking/{application_id}/history` - Application history
- `POST /api/v1/tracking/subscribe` - Subscribe to updates
- `GET /api/v1/tracking/notifications` - Get notifications

**Status Updates:**
- Submitted
- Under Review
- Documents Verified
- Approved
- Rejected
- Payment Processed

### 7. SMS Interface
**Base Path:** `/api/v1/sms`

- `POST /api/v1/sms/send` - Send SMS
- `POST /api/v1/sms/receive` - Receive SMS (webhook)
- `GET /api/v1/sms/status/{message_id}` - Check SMS status

**SMS Commands:**
- `CHECK` - Check eligibility
- `STATUS <app_id>` - Check application status
- `HELP` - Get help
- `SCHEMES` - List schemes

### 8. Voice Interface
**Base Path:** `/api/v1/voice`

- `POST /api/v1/voice/call` - Initiate voice call
- `POST /api/v1/voice/webhook` - Voice webhook handler
- `POST /api/v1/voice/speech-to-text` - Convert speech to text
- `GET /api/v1/voice/session/{session_id}` - Get voice session

**Supported Languages:**
- Hindi (हिंदी)
- Marathi (मराठी)
- English

---

## 🔐 Authentication

All API endpoints (except health checks) require authentication:

```http
Authorization: Bearer <your_jwt_token>
```

**Get Token:**
```bash
POST /api/v1/auth/login
{
  "phone": "+91-9876543210",
  "otp": "123456"
}
```

---

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-07T00:00:00Z",
  "processing_time": "1.2s"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Invalid profile data",
    "details": { ... },
    "timestamp": "2026-03-07T00:00:00Z"
  }
}
```

---

## 🚀 Quick Start Examples

### 1. Check Eligibility (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/eligibility/check \
  -H "Content-Type: application/json" \
  -d '{
    "name": "राज कुमार",
    "age": 35,
    "state": "Maharashtra",
    "income": 50000,
    "occupation": "farmer"
  }'
```

### 2. Upload Document (Python)
```python
import requests

url = "http://localhost:8000/api/v1/documents/upload"
files = {"file": open("aadhaar.jpg", "rb")}
data = {"document_type": "aadhaar", "profile_id": "user_123"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 3. Track Application (JavaScript)
```javascript
fetch('http://localhost:8000/api/v1/tracking/app_123')
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 📱 Interactive Testing

Visit **http://localhost:8000/docs** to:
- Browse all endpoints
- Test APIs interactively
- View request/response schemas
- Generate code samples

---

## 🌍 Multi-Language Support

The platform supports multiple languages for user interfaces:

- **Marathi:** मराठी
- **Hindi:** हिंदी
- **English:** English

Set language in request header:
```http
Accept-Language: mr-IN
```

---

## 📈 Performance Metrics

- **Eligibility Check:** < 5 seconds (30+ schemes)
- **Document OCR:** < 3 seconds
- **API Response Time:** < 1 second
- **Concurrent Users:** 1,000+
- **Uptime:** 99.5%

---

## 🔗 Related Documentation

- [Deployment Guide](DEPLOY_PRODUCTION_ARCHITECTURE.md)
- [AWS Configuration](AWS_CONFIGURATION_COMPLETE.md)
- [Quick Start](QUICK_START.md)
- [GitHub Repository](https://github.com/vrushabhzade/-SarvaSahay.git)
