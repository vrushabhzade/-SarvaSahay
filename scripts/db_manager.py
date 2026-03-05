"""
Database and cache management utility script
Provides commands for database migrations, cache management, and health checks
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database.base import init_db, engine, SessionLocal
from shared.cache.redis_client import get_redis_cache
from shared.config.settings import get_settings
from sqlalchemy import text


def check_database_connection():
    """Check if database is accessible"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        cache = get_redis_cache()
        if cache.ping():
            print("✓ Redis connection successful")
            stats = cache.get_cache_stats()
            print(f"  - Connected clients: {stats.get('connected_clients', 'N/A')}")
            print(f"  - Used memory: {stats.get('used_memory', 'N/A')}")
            print(f"  - Total keys: {stats.get('total_keys', 'N/A')}")
            return True
        else:
            print("✗ Redis connection failed")
            return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


def initialize_database():
    """Initialize database by creating all tables"""
    try:
        print("Initializing database...")
        init_db()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def clear_cache():
    """Clear all cached data"""
    try:
        cache = get_redis_cache()
        if cache.flush_all():
            print("✓ Cache cleared successfully")
            return True
        else:
            print("✗ Failed to clear cache")
            return False
    except Exception as e:
        print(f"✗ Cache clear failed: {e}")
        return False


def show_config():
    """Display current configuration"""
    settings = get_settings()
    print("\n=== Configuration ===")
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database.url}")
    print(f"Redis URL: {settings.redis.url}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"Debug Mode: {settings.debug}")


def health_check():
    """Perform comprehensive health check"""
    print("\n=== Health Check ===")
    db_ok = check_database_connection()
    redis_ok = check_redis_connection()
    
    if db_ok and redis_ok:
        print("\n✓ All systems operational")
        return 0
    else:
        print("\n✗ Some systems are not operational")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Database and cache management utility for SarvaSahay Platform"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health check command
    subparsers.add_parser("health", help="Check database and Redis connectivity")
    
    # Database commands
    subparsers.add_parser("init-db", help="Initialize database (create all tables)")
    subparsers.add_parser("check-db", help="Check database connection")
    
    # Cache commands
    subparsers.add_parser("check-cache", help="Check Redis connection")
    subparsers.add_parser("clear-cache", help="Clear all cached data")
    
    # Config command
    subparsers.add_parser("config", help="Show current configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "health":
        return health_check()
    elif args.command == "init-db":
        return 0 if initialize_database() else 1
    elif args.command == "check-db":
        return 0 if check_database_connection() else 1
    elif args.command == "check-cache":
        return 0 if check_redis_connection() else 1
    elif args.command == "clear-cache":
        return 0 if clear_cache() else 1
    elif args.command == "config":
        show_config()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
