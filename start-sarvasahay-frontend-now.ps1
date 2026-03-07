#!/usr/bin/env pwsh
# Start SarvaSahay Frontend - Quick Fix Script

Write-Host "🛑 Stopping any running React apps (TradeLink, etc.)..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ Starting SarvaSahay Frontend..." -ForegroundColor Green
Write-Host ""
Write-Host "Location: frontend/web-app" -ForegroundColor Cyan
Write-Host "URL: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "You should see:" -ForegroundColor Yellow
Write-Host "  🇮🇳 SarvaSahay Platform (NOT TradeLink!)" -ForegroundColor White
Write-Host "  सरवसहाय मंच" -ForegroundColor White
Write-Host "  AI-powered government scheme eligibility" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Set-Location frontend/web-app
npm start
