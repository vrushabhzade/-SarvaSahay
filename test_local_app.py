"""
Local Application Testing Script
Tests all major endpoints and functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, status, message=""):
    """Print test result with color"""
    if status:
        print(f"{Colors.GREEN}✓{Colors.END} {name}")
        if message:
            print(f"  {Colors.BLUE}{message}{Colors.END}")
    else:
        print(f"{Colors.RED}✗{Colors.END} {name}")
        if message:
            print(f"  {Colors.RED}{message}{Colors.END}")

def test_root_endpoint():
    """Test root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        
        success = (
            response.status_code == 200 and
            "message" in data and
            "version" in data
        )
        
        print_test(
            "Root Endpoint",
            success,
            f"Version: {data.get('version')}, Environment: {data.get('environment')}"
        )
        return success
    except Exception as e:
        print_test("Root Endpoint", False, str(e))
        return False

def test_docs_endpoint():
    """Test API documentation endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        success = response.status_code == 200
        print_test("API Documentation", success, "Swagger UI accessible")
        return success
    except Exception as e:
        print_test("API Documentation", False, str(e))
        return False

def test_openapi_spec():
    """Test OpenAPI specification"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        data = response.json()
        
        success = (
            response.status_code == 200 and
            "openapi" in data and
            "info" in data
        )
        
        print_test(
            "OpenAPI Specification",
            success,
            f"OpenAPI Version: {data.get('openapi')}"
        )
        return success
    except Exception as e:
        print_test("OpenAPI Specification", False, str(e))
        return False

def test_response_time():
    """Test API response time"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/")
        elapsed = time.time() - start
        
        # Should be under 1 second for simple endpoint
        success = elapsed < 1.0
        
        print_test(
            "Response Time",
            success,
            f"{elapsed:.3f}s (Target: <1s)"
        )
        return success
    except Exception as e:
        print_test("Response Time", False, str(e))
        return False

def test_cors_headers():
    """Test CORS headers"""
    try:
        response = requests.get(f"{BASE_URL}/")
        headers = response.headers
        
        # Check for CORS headers
        has_cors = 'access-control-allow-origin' in [h.lower() for h in headers.keys()]
        
        print_test(
            "CORS Configuration",
            has_cors,
            "CORS headers present" if has_cors else "CORS headers missing"
        )
        return has_cors
    except Exception as e:
        print_test("CORS Configuration", False, str(e))
        return False

def test_process_time_header():
    """Test custom process time header"""
    try:
        response = requests.get(f"{BASE_URL}/")
        headers = response.headers
        
        has_header = 'x-process-time' in [h.lower() for h in headers.keys()]
        
        if has_header:
            process_time = headers.get('x-process-time', headers.get('X-Process-Time'))
            print_test(
                "Process Time Header",
                True,
                f"Process time: {process_time}s"
            )
        else:
            print_test("Process Time Header", False, "Header not found")
        
        return has_header
    except Exception as e:
        print_test("Process Time Header", False, str(e))
        return False

def test_docker_services():
    """Test Docker services connectivity"""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        services = result.stdout
        required_services = ["sarvasahay-app", "sarvasahay-postgres", "sarvasahay-redis"]
        
        all_running = all(service in services for service in required_services)
        
        print_test(
            "Docker Services",
            all_running,
            "All services running" if all_running else "Some services missing"
        )
        
        if all_running:
            for line in services.split('\n'):
                if 'sarvasahay' in line:
                    print(f"  {Colors.BLUE}{line}{Colors.END}")
        
        return all_running
    except Exception as e:
        print_test("Docker Services", False, str(e))
        return False

def test_concurrent_requests():
    """Test concurrent request handling"""
    import concurrent.futures
    
    try:
        def make_request():
            response = requests.get(f"{BASE_URL}/")
            return response.status_code == 200
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        success = success_rate == 1.0
        
        print_test(
            "Concurrent Requests",
            success,
            f"Success rate: {success_rate*100:.0f}% (10 concurrent requests)"
        )
        return success
    except Exception as e:
        print_test("Concurrent Requests", False, str(e))
        return False

def test_error_handling():
    """Test error handling"""
    try:
        # Test 404 error
        response = requests.get(f"{BASE_URL}/nonexistent-endpoint")
        
        success = response.status_code == 404
        
        if success and response.headers.get('content-type') == 'application/json':
            data = response.json()
            has_error_structure = 'detail' in data or 'error' in data
            success = success and has_error_structure
        
        print_test(
            "Error Handling",
            success,
            "404 errors handled correctly"
        )
        return success
    except Exception as e:
        print_test("Error Handling", False, str(e))
        return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}SarvaSahay Platform - Local Testing{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    print(f"{Colors.YELLOW}Testing Base URL: {BASE_URL}{Colors.END}\n")
    
    tests = [
        ("Basic Functionality", [
            test_root_endpoint,
            test_docs_endpoint,
            test_openapi_spec,
        ]),
        ("Performance", [
            test_response_time,
            test_concurrent_requests,
        ]),
        ("Configuration", [
            test_cors_headers,
            test_process_time_header,
        ]),
        ("Infrastructure", [
            test_docker_services,
        ]),
        ("Error Handling", [
            test_error_handling,
        ]),
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category, test_functions in tests:
        print(f"\n{Colors.YELLOW}[{category}]{Colors.END}")
        for test_func in test_functions:
            total_tests += 1
            if test_func():
                passed_tests += 1
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    success_rate = (passed_tests / total_tests) * 100
    
    if success_rate == 100:
        color = Colors.GREEN
    elif success_rate >= 80:
        color = Colors.YELLOW
    else:
        color = Colors.RED
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"{color}Passed: {passed_tests}{Colors.END}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"{color}Success Rate: {success_rate:.1f}%{Colors.END}\n")
    
    # Application Info
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Application Access{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    print(f"API Base URL:        {Colors.GREEN}{BASE_URL}{Colors.END}")
    print(f"API Documentation:   {Colors.GREEN}{BASE_URL}/docs{Colors.END}")
    print(f"Alternative Docs:    {Colors.GREEN}{BASE_URL}/redoc{Colors.END}")
    print(f"OpenAPI Spec:        {Colors.GREEN}{BASE_URL}/openapi.json{Colors.END}")
    print(f"\nGitHub Repository:   {Colors.GREEN}https://github.com/vrushabhzade/-SarvaSahay.git{Colors.END}\n")
    
    return success_rate == 100

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing interrupted by user{Colors.END}\n")
        exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Testing failed with error: {e}{Colors.END}\n")
        exit(1)
