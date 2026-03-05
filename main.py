"""
SarvaSahay Platform Main Application
FastAPI application with microservices architecture
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from shared.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize monitoring
    from shared.monitoring import get_resource_monitor, get_alert_manager
    resource_monitor = get_resource_monitor()
    resource_monitor.start_monitoring()
    logger.info("Resource monitoring started")
    
    # Initialize alert handlers
    alert_manager = get_alert_manager()
    from shared.monitoring.alerts import log_alert_handler, notification_alert_handler
    alert_manager.add_alert_handler(log_alert_handler)
    alert_manager.add_alert_handler(notification_alert_handler)
    logger.info("Alert handlers configured")
    
    # Initialize services here (database, redis, ML models, etc.)
    # await initialize_database()
    # await initialize_redis()
    # await load_ml_models()
    
    yield
    
    # Shutdown
    logger.info("Shutting down SarvaSahay Platform")
    resource_monitor.stop_monitoring()
    logger.info("Resource monitoring stopped")
    # Cleanup resources here


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered government scheme eligibility and enrollment platform for rural Indian citizens",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else ["sarvasahay.gov.in", "*.sarvasahay.gov.in"]
    )
    
    # Add custom middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add processing time header for performance monitoring"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests (>5 seconds violates our requirement)
        if process_time > 5.0:
            logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
        
        return response
    
    @app.middleware("http")
    async def rate_limiting_middleware(request: Request, call_next):
        """Basic rate limiting middleware"""
        # In production, use Redis-based rate limiting
        # For now, just log requests
        client_ip = request.client.host
        logger.debug(f"Request from {client_ip}: {request.method} {request.url}")
        
        response = await call_next(request)
        return response
    
    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom HTTP exception handler"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "timestamp": time.time(),
                    "path": str(request.url)
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """General exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "timestamp": time.time(),
                    "path": str(request.url)
                }
            }
        )
    
    # Import and include routers
    try:
        from api.routes import (
            health_routes, 
            profile_routes, 
            eligibility_routes,
            document_routes,
            application_routes,
            tracking_routes,
            sms_routes,
            voice_routes,
            monitoring_routes
        )
        
        app.include_router(health_routes.router, prefix=settings.api_prefix, tags=["Health"])
        app.include_router(profile_routes.router, prefix=settings.api_prefix, tags=["Profiles"])
        app.include_router(eligibility_routes.router, prefix=settings.api_prefix, tags=["Eligibility"])
        app.include_router(document_routes.router, prefix=settings.api_prefix, tags=["Documents"])
        app.include_router(application_routes.router, prefix=settings.api_prefix, tags=["Applications"])
        app.include_router(tracking_routes.router, prefix=settings.api_prefix, tags=["Tracking"])
        app.include_router(sms_routes.router, prefix=settings.api_prefix, tags=["SMS Interface"])
        app.include_router(voice_routes.router, prefix=settings.api_prefix, tags=["Voice Interface"])
        app.include_router(monitoring_routes.router, prefix=settings.api_prefix, tags=["Monitoring"])
    except ImportError as e:
        logger.warning(f"Could not import routes: {e}")
    
    return app


# Create the application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SarvaSahay Platform",
        "description": "AI-powered government scheme eligibility and enrollment platform",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.logging.level.lower()
    )