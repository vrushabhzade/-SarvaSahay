"""
Simple local development server startup script
This script starts the SarvaSahay platform without Docker for local testing
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    logger.info("Checking environment configuration...")
    
    # Set default values for local development if not set
    defaults = {
        'DATABASE_URL': 'sqlite:///./sarvasahay_local.db',
        'REDIS_URL': 'redis://localhost:6379/0',
        'SECRET_KEY': 'dev-secret-key-change-in-production',
        'ENCRYPTION_KEY': 'dev-encryption-key-change-in-production',
        'JWT_SECRET': 'dev-jwt-secret-change-in-production',
        'ENVIRONMENT': 'development',
        'DEBUG': 'true',
        'API_HOST': '0.0.0.0',
        'API_PORT': '8000',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"Set {key} to default value")
    
    logger.info("✓ Environment configuration complete")

def check_dependencies():
    """Check if required packages are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.error("Install them with: pip install -r requirements-dev.txt")
        return False
    
    logger.info("✓ All required packages installed")
    return True

def start_server():
    """Start the FastAPI server"""
    logger.info("Starting SarvaSahay Platform...")
    logger.info("=" * 60)
    logger.info("Server will be available at:")
    logger.info("  - Local:   http://localhost:8000")
    logger.info("  - Network: http://0.0.0.0:8000")
    logger.info("  - API Docs: http://localhost:8000/docs")
    logger.info("  - Health:  http://localhost:8000/health")
    logger.info("=" * 60)
    logger.info("Press CTRL+C to stop the server")
    logger.info("")
    
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            app,
            host=os.getenv('API_HOST', '0.0.0.0'),
            port=int(os.getenv('API_PORT', '8000')),
            reload=True,
            log_level=os.getenv('LOG_LEVEL', 'info').lower()
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         SarvaSahay Platform - Local Development           ║
║    AI-Powered Government Scheme Eligibility Platform      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check environment
    check_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
