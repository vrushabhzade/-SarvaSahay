"""
Simple server runner - no reload, just start
"""
import os
import uvicorn

# Set defaults
os.environ.setdefault('DATABASE_URL', 'sqlite:///./sarvasahay_local.db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')
os.environ.setdefault('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
os.environ.setdefault('JWT_SECRET', 'dev-jwt-secret-change-in-production')
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('DEBUG', 'true')

print("=" * 60)
print("  SarvaSahay Platform - Starting Server")
print("=" * 60)
print()
print("Server will be available at:")
print("  - http://localhost:8000")
print("  - API Docs: http://localhost:8000/docs")
print("  - Health: http://localhost:8000/health")
print()
print("Press CTRL+C to stop")
print("=" * 60)
print()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
