"""
SarvaSahay Platform - Diagnostic Tool
Checks for common issues preventing the server from starting
"""

import os
import sys
import subprocess
import socket

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_status(check, status, message=""):
    """Print check status"""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    
    status_text = "PASS" if status else "FAIL"
    print(f"{color}{symbol} {check}: {status_text}{reset}")
    if message:
        print(f"  → {message}")

def check_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    
    version = sys.version_info
    required = (3, 11)
    
    current = f"{version.major}.{version.minor}.{version.micro}"
    required_str = f"{required[0]}.{required[1]}+"
    
    is_valid = version >= required
    
    print(f"Current version: {current}")
    print(f"Required version: {required_str}")
    print_status("Python Version", is_valid)
    
    return is_valid

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Dependency Check")
    
    required = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'pydantic': 'Data validation',
        'sqlalchemy': 'Database ORM',
        'redis': 'Redis client',
        'psycopg2': 'PostgreSQL driver (optional)',
        'xgboost': 'ML model',
        'opencv-python': 'Image processing',
        'pytesseract': 'OCR engine'
    }
    
    installed = []
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package.replace('-', '_'))
            installed.append(package)
            print_status(f"{package}", True, description)
        except ImportError:
            missing.append(package)
            print_status(f"{package}", False, f"{description} - NOT INSTALLED")
    
    print(f"\nInstalled: {len(installed)}/{len(required)}")
    
    if missing:
        print(f"\nTo install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        print(f"\nOr install all dependencies:")
        print(f"  pip install -r requirements-dev.txt")
    
    return len(missing) == 0

def check_port_availability():
    """Check if port 8000 is available"""
    print_header("Port Availability Check")
    
    port = 8000
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print_status(f"Port {port}", False, f"Port {port} is already in use")
            print(f"\nTo find what's using the port:")
            print(f"  Windows: netstat -ano | findstr :{port}")
            print(f"  Linux/Mac: lsof -i :{port}")
            return False
        else:
            print_status(f"Port {port}", True, f"Port {port} is available")
            return True
    except Exception as e:
        print_status(f"Port {port}", False, f"Error checking port: {e}")
        return False

def check_environment_variables():
    """Check environment variables"""
    print_header("Environment Variables Check")
    
    optional_vars = {
        'DATABASE_URL': 'Database connection string',
        'REDIS_URL': 'Redis connection string',
        'SECRET_KEY': 'Application secret key',
        'ENCRYPTION_KEY': 'Data encryption key',
        'JWT_SECRET': 'JWT token secret'
    }
    
    set_vars = []
    unset_vars = []
    
    for var, description in optional_vars.items():
        if var in os.environ:
            set_vars.append(var)
            value = os.environ[var]
            masked = value[:10] + "..." if len(value) > 10 else value
            print_status(var, True, f"{description} - Set ({masked})")
        else:
            unset_vars.append(var)
            print_status(var, False, f"{description} - Not set (will use defaults)")
    
    print(f"\nSet: {len(set_vars)}/{len(optional_vars)}")
    
    if unset_vars:
        print(f"\nNote: Unset variables will use default values for local development")
        print(f"For production, create a .env file with proper values")
    
    return True  # Not critical for local development

def check_file_structure():
    """Check if required files exist"""
    print_header("File Structure Check")
    
    required_files = [
        'main.py',
        'shared/config/settings.py',
        'api/routes/__init__.py',
        'api/routes/health_routes.py'
    ]
    
    all_exist = True
    
    for file in required_files:
        exists = os.path.exists(file)
        print_status(file, exists)
        if not exists:
            all_exist = False
    
    return all_exist

def check_database_connection():
    """Check database connection (optional)"""
    print_header("Database Connection Check (Optional)")
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./sarvasahay_local.db')
    
    print(f"Database URL: {db_url}")
    
    if db_url.startswith('sqlite'):
        print_status("SQLite", True, "Using SQLite for local development")
        return True
    elif db_url.startswith('postgresql'):
        try:
            import psycopg2
            # Try to parse connection string
            print_status("PostgreSQL", True, "PostgreSQL driver installed")
            print("  Note: Connection will be tested when server starts")
            return True
        except ImportError:
            print_status("PostgreSQL", False, "psycopg2 not installed")
            print("  Install with: pip install psycopg2-binary")
            return False
    else:
        print_status("Database", False, f"Unknown database type: {db_url}")
        return False

def check_redis_connection():
    """Check Redis connection (optional)"""
    print_header("Redis Connection Check (Optional)")
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    print(f"Redis URL: {redis_url}")
    
    try:
        import redis
        print_status("Redis Client", True, "Redis client installed")
        
        # Try to connect
        try:
            r = redis.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            print_status("Redis Connection", True, "Successfully connected to Redis")
            return True
        except Exception as e:
            print_status("Redis Connection", False, f"Cannot connect: {e}")
            print("  Note: Server will start but caching will be disabled")
            return False
    except ImportError:
        print_status("Redis Client", False, "Redis client not installed")
        print("  Install with: pip install redis")
        return False

def main():
    """Run all diagnostic checks"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      SarvaSahay Platform - Diagnostic Tool                ║
║      Checking for common issues...                        ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("Python Version", check_python_version, True),
        ("Dependencies", check_dependencies, True),
        ("Port Availability", check_port_availability, True),
        ("Environment Variables", check_environment_variables, False),
        ("File Structure", check_file_structure, True),
        ("Database Connection", check_database_connection, False),
        ("Redis Connection", check_redis_connection, False)
    ]
    
    results = []
    critical_failed = False
    
    for name, check_func, is_critical in checks:
        try:
            result = check_func()
            results.append((name, result, is_critical))
            if is_critical and not result:
                critical_failed = True
        except Exception as e:
            print(f"\nError running {name} check: {e}")
            results.append((name, False, is_critical))
            if is_critical:
                critical_failed = True
    
    # Summary
    print_header("Diagnostic Summary")
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    critical = sum(1 for _, _, is_critical in results if is_critical)
    critical_passed = sum(1 for _, result, is_critical in results if result and is_critical)
    
    print(f"Total checks: {passed}/{total} passed")
    print(f"Critical checks: {critical_passed}/{critical} passed")
    
    if critical_failed:
        print("\n❌ CRITICAL ISSUES FOUND")
        print("The server may not start properly. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  1. Install dependencies: pip install -r requirements-dev.txt")
        print("  2. Check if port 8000 is available")
        print("  3. Ensure all required files exist")
        return 1
    else:
        print("\n✅ ALL CRITICAL CHECKS PASSED")
        print("The server should start successfully.")
        print("\nTo start the server:")
        print("  Windows: start_local.bat")
        print("  Linux/Mac: python start_local.py")
        print("  Or: python main.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())
