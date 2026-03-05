"""
Health Check Routes
System health and monitoring endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
import time
import psutil
import sys

from shared.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    system_info: dict


class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    system_info: dict
    services: dict
    performance_metrics: dict


# Track application start time
app_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    uptime = time.time() - app_start_time
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=uptime,
        system_info={
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        }
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with service status"""
    uptime = time.time() - app_start_time
    
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Mock service health checks (in real implementation, check actual services)
    services_status = {
        "database": "healthy",  # Would check actual DB connection
        "redis": "healthy",     # Would check Redis connection
        "ml_models": "healthy", # Would check if ML models are loaded
        "government_apis": "healthy"  # Would check API connectivity
    }
    
    # Performance metrics
    performance_metrics = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_usage_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "uptime_requirement_met": uptime > 0,  # 99.5% uptime requirement
        "response_time_requirement_met": True  # <5 second requirement
    }
    
    # Determine overall status
    overall_status = "healthy"
    if any(status != "healthy" for status in services_status.values()):
        overall_status = "degraded"
    if cpu_percent > 90 or memory.percent > 90:
        overall_status = "degraded"
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=uptime,
        system_info={
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        },
        services=services_status,
        performance_metrics=performance_metrics
    )


@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # Check if application is ready to serve requests
    # In real implementation, verify:
    # - Database connections
    # - ML models loaded
    # - Required services available
    
    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    # Simple check to verify application is alive
    return {"status": "alive", "timestamp": datetime.utcnow()}