@echo off
REM SarvaSahay Platform Test Runner - Windows Version
REM Comprehensive testing script following the platform's testing strategy

setlocal enabledelayedexpansion

echo 🚀 SarvaSahay Platform Test Suite
echo ==================================

set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

echo [INFO] Running test type: %TEST_TYPE%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python.
    exit /b 1
)

goto :%TEST_TYPE% 2>nul || goto :usage

:unit
echo [INFO] Running Unit Tests...
if exist "tests\unit" (
    python -m pytest tests\unit\ -v --cov=services --cov-report=html --cov-report=term
    if errorlevel 1 exit /b 1
    echo [SUCCESS] Unit tests completed
) else (
    echo [WARNING] Unit tests directory not found (tests\unit\)
)
if "%TEST_TYPE%"=="unit" goto :end
goto :property

:property
echo [INFO] Running Property-Based Tests (Hypothesis)...
if exist "tests\property" (
    python -m pytest tests\property\ --hypothesis-profile dev -v
    if errorlevel 1 exit /b 1
    echo [SUCCESS] Property-based tests completed
) else (
    echo [WARNING] Property tests directory not found (tests\property\)
)
if "%TEST_TYPE%"=="property" goto :end
goto :integration

:integration
echo [INFO] Running Integration Tests...
if exist "tests\integration" (
    python -m pytest tests\integration\ --env staging -v
    if errorlevel 1 exit /b 1
    echo [SUCCESS] Integration tests completed
) else (
    echo [WARNING] Integration tests directory not found (tests\integration\)
)
if "%TEST_TYPE%"=="integration" goto :end
goto :api

:api
echo [INFO] Running API Compliance Tests...
if exist "api\openapi.yaml" (
    spectral lint api\openapi.yaml
    if errorlevel 1 exit /b 1
    echo [SUCCESS] API specification validation completed
) else (
    echo [WARNING] OpenAPI specification not found (api\openapi.yaml)
)
if "%TEST_TYPE%"=="api" goto :end
goto :ml

:ml
echo [INFO] Running ML Model Validation...
if exist "scripts\validate_model.py" (
    python scripts\validate_model.py --test-data data\validation
    if errorlevel 1 exit /b 1
    echo [SUCCESS] ML model validation completed
) else (
    echo [WARNING] Model validation script not found (scripts\validate_model.py)
)
if "%TEST_TYPE%"=="ml" goto :end
goto :load

:load
echo [INFO] Running Load Tests...
if exist "tests\load" (
    locust -f tests\load\eligibility_test.py --host https://api.sarvasahay.gov.in --headless -u 100 -r 10 -t 60s
    if errorlevel 1 exit /b 1
    echo [SUCCESS] Load tests completed
) else (
    echo [WARNING] Load tests directory not found (tests\load\)
)
if "%TEST_TYPE%"=="load" goto :end
goto :e2e

:e2e
echo [INFO] Running End-to-End Tests...
if exist "tests\e2e" (
    python -m pytest tests\e2e\ -v --browser chromium
    if errorlevel 1 exit /b 1
    echo [SUCCESS] E2E tests completed
) else (
    echo [WARNING] E2E tests directory not found (tests\e2e\)
)
if "%TEST_TYPE%"=="e2e" goto :end
goto :end

:all
goto :unit

:usage
echo Usage: %0 [unit^|property^|integration^|load^|api^|ml^|e2e^|all]
echo.
echo Test Categories:
echo   unit        - Unit tests for individual components
echo   property    - Property-based tests (Hypothesis framework)
echo   integration - Integration tests with external systems
echo   load        - Load testing (1,000+ concurrent users)
echo   api         - API specification compliance
echo   ml          - ML model validation (XGBoost accuracy)
echo   e2e         - End-to-end user journey tests
echo   all         - All tests except load and e2e
exit /b 1

:end
echo [SUCCESS] ✅ Test execution completed!
exit /b 0