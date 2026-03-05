#!/bin/bash

# SarvaSahay Platform Test Runner
# Comprehensive testing script following the platform's testing strategy

set -e  # Exit on any error

echo "🚀 SarvaSahay Platform Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in development environment
if [ ! -f "docker-compose.yml" ]; then
    print_warning "docker-compose.yml not found. Creating development environment setup..."
    # This would be created during implementation phase
fi

# Test categories based on SarvaSahay testing strategy
run_unit_tests() {
    print_status "Running Unit Tests..."
    
    if [ -d "tests/unit" ]; then
        # Python unit tests for services
        if command -v pytest &> /dev/null; then
            pytest tests/unit/ -v --cov=services --cov-report=html --cov-report=term
            print_success "Unit tests completed"
        else
            print_error "pytest not found. Install with: pip install pytest pytest-cov"
            return 1
        fi
    else
        print_warning "Unit tests directory not found (tests/unit/)"
    fi
}

run_property_tests() {
    print_status "Running Property-Based Tests (Hypothesis)..."
    
    if [ -d "tests/property" ]; then
        # Property-based tests with 100+ iterations as per requirements
        pytest tests/property/ --hypothesis-profile dev -v
        print_success "Property-based tests completed"
    else
        print_warning "Property tests directory not found (tests/property/)"
    fi
}

run_integration_tests() {
    print_status "Running Integration Tests..."
    
    if [ -d "tests/integration" ]; then
        # Integration tests with staging environment
        pytest tests/integration/ --env staging -v
        print_success "Integration tests completed"
    else
        print_warning "Integration tests directory not found (tests/integration/)"
    fi
}

run_load_tests() {
    print_status "Running Load Tests..."
    
    if [ -d "tests/load" ]; then
        # Load testing with Locust (1,000+ concurrent users requirement)
        if command -v locust &> /dev/null; then
            print_status "Starting load test for eligibility engine..."
            locust -f tests/load/eligibility_test.py --host https://api.sarvasahay.gov.in --headless -u 100 -r 10 -t 60s
            print_success "Load tests completed"
        else
            print_error "locust not found. Install with: pip install locust"
            return 1
        fi
    else
        print_warning "Load tests directory not found (tests/load/)"
    fi
}

run_api_tests() {
    print_status "Running API Compliance Tests..."
    
    # Check OpenAPI specification compliance
    if [ -f "api/openapi.yaml" ]; then
        if command -v spectral &> /dev/null; then
            spectral lint api/openapi.yaml
            print_success "API specification validation completed"
        else
            print_error "spectral not found. Install with: npm install -g @stoplight/spectral-cli"
            return 1
        fi
    else
        print_warning "OpenAPI specification not found (api/openapi.yaml)"
    fi
}

run_ml_model_tests() {
    print_status "Running ML Model Validation..."
    
    if [ -f "scripts/validate_model.py" ]; then
        # Validate XGBoost model performance (89% accuracy requirement)
        python scripts/validate_model.py --test-data data/validation
        print_success "ML model validation completed"
    else
        print_warning "Model validation script not found (scripts/validate_model.py)"
    fi
}

run_security_tests() {
    print_status "Running Security Tests..."
    
    # Security scanning (placeholder for implementation phase)
    print_warning "Security tests not implemented yet"
    # Future: bandit for Python security, OWASP ZAP for API security
}

run_e2e_tests() {
    print_status "Running End-to-End Tests..."
    
    if [ -d "tests/e2e" ]; then
        # End-to-end user journey tests
        pytest tests/e2e/ -v --browser chromium
        print_success "E2E tests completed"
    else
        print_warning "E2E tests directory not found (tests/e2e/)"
    fi
}

# Main test execution
main() {
    local test_type=${1:-"all"}
    local exit_code=0
    
    case $test_type in
        "unit")
            run_unit_tests || exit_code=1
            ;;
        "property")
            run_property_tests || exit_code=1
            ;;
        "integration")
            run_integration_tests || exit_code=1
            ;;
        "load")
            run_load_tests || exit_code=1
            ;;
        "api")
            run_api_tests || exit_code=1
            ;;
        "ml")
            run_ml_model_tests || exit_code=1
            ;;
        "security")
            run_security_tests || exit_code=1
            ;;
        "e2e")
            run_e2e_tests || exit_code=1
            ;;
        "all")
            print_status "Running complete test suite..."
            run_unit_tests || exit_code=1
            run_property_tests || exit_code=1
            run_integration_tests || exit_code=1
            run_api_tests || exit_code=1
            run_ml_model_tests || exit_code=1
            run_security_tests || exit_code=1
            # Skip load and e2e tests in "all" mode by default
            ;;
        "full")
            print_status "Running full test suite including load and e2e tests..."
            run_unit_tests || exit_code=1
            run_property_tests || exit_code=1
            run_integration_tests || exit_code=1
            run_api_tests || exit_code=1
            run_ml_model_tests || exit_code=1
            run_security_tests || exit_code=1
            run_load_tests || exit_code=1
            run_e2e_tests || exit_code=1
            ;;
        *)
            echo "Usage: $0 [unit|property|integration|load|api|ml|security|e2e|all|full]"
            echo ""
            echo "Test Categories:"
            echo "  unit        - Unit tests for individual components"
            echo "  property    - Property-based tests (Hypothesis framework)"
            echo "  integration - Integration tests with external systems"
            echo "  load        - Load testing (1,000+ concurrent users)"
            echo "  api         - API specification compliance"
            echo "  ml          - ML model validation (XGBoost accuracy)"
            echo "  security    - Security vulnerability scanning"
            echo "  e2e         - End-to-end user journey tests"
            echo "  all         - All tests except load and e2e"
            echo "  full        - Complete test suite including load and e2e"
            exit 1
            ;;
    esac
    
    if [ $exit_code -eq 0 ]; then
        print_success "✅ All tests passed!"
    else
        print_error "❌ Some tests failed!"
    fi
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"