# SarvaSahay Frontend Setup Script
Write-Host "🚀 Setting up SarvaSahay Frontend..." -ForegroundColor Green

# Navigate to web-app directory
Set-Location frontend/web-app

Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow

# Install core dependencies
npm install axios react-router-dom

# Install Material-UI
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material

# Install i18n for multi-language support
npm install react-i18next i18next

# Install Redux for state management
npm install @reduxjs/toolkit react-redux

# Install form handling
npm install react-hook-form yup @hookform/resolvers

# Install date handling
npm install date-fns

Write-Host "`n✅ Dependencies installed successfully!" -ForegroundColor Green

Write-Host "`n📝 Creating project structure..." -ForegroundColor Yellow

# Create directory structure
$directories = @(
    "src/components/common",
    "src/components/profile",
    "src/components/eligibility",
    "src/components/documents",
    "src/components/applications",
    "src/components/tracking",
    "src/pages",
    "src/services",
    "src/store/slices",
    "src/hooks",
    "src/utils",
    "src/types",
    "src/locales",
    "src/assets/images"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "✅ Project structure created!" -ForegroundColor Green

Write-Host "`n🎉 Frontend setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. cd frontend/web-app" -ForegroundColor White
Write-Host "2. npm start" -ForegroundColor White
Write-Host "`nThe app will open at http://localhost:3000" -ForegroundColor White
Write-Host "Backend API is at http://localhost:8000" -ForegroundColor White
