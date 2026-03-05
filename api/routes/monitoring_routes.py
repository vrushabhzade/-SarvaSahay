"""
Monitoring and Metrics API Routes
Exposes performance metrics, resource monitoring, and alerts
Requirements: 9.1, 9.5
"""

from fastapi import APIRouter, Response, Query
from fastapi.responses import PlainTextResponse
from typing import Optional
import logging

from shared.monitoring import (
    get_metrics_collector,
    get_resource_monitor,
    get_alert_manager
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Get Prometheus-formatted metrics
    
    This endpoint exposes metrics in Prometheus text format for scraping
    """
    collector = get_metrics_collector()
    metrics_data = collector.get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Get human-readable metrics summary
    
    Returns:
        Dictionary with aggregated metrics
    """
    collector = get_metrics_collector()
    return collector.get_metrics_summary()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        System health status
    """
    resource_monitor = get_resource_monitor()
    alert_manager = get_alert_manager()
    
    # Get current resource usage
    summary = resource_monitor.get_summary()
    
    # Get active alerts
    critical_alerts = alert_manager.get_active_alerts(hours=1)
    
    # Determine health status
    status = "healthy"
    if summary.get('alerts'):
        status = "degraded"
    if any(a.severity.value == "critical" for a in critical_alerts):
        status = "unhealthy"
    
    return {
        "status": status,
        "timestamp": summary.get('timestamp'),
        "cpu_percent": summary.get('cpu_percent'),
        "memory_percent": summary.get('memory_percent'),
        "disk_percent": summary.get('disk_percent'),
        "active_alerts": len(critical_alerts)
    }


@router.get("/resources")
async def get_resource_metrics():
    """
    Get current system resource metrics
    
    Returns:
        Detailed resource usage information
    """
    resource_monitor = get_resource_monitor()
    return resource_monitor.get_all_metrics()


@router.get("/resources/summary")
async def get_resource_summary():
    """
    Get resource usage summary
    
    Returns:
        Simplified resource usage summary
    """
    resource_monitor = get_resource_monitor()
    return resource_monitor.get_summary()


@router.get("/resources/history")
async def get_resource_history(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to retrieve")
):
    """
    Get historical resource metrics
    
    Args:
        hours: Number of hours of history (1-24)
    
    Returns:
        Historical resource data
    """
    resource_monitor = get_resource_monitor()
    return resource_monitor.get_history(hours=hours)


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, error, critical"),
    alert_type: Optional[str] = Query(None, description="Filter by type: performance, resource, error_rate, availability"),
    hours: int = Query(default=1, ge=1, le=24, description="Time window in hours")
):
    """
    Get active alerts
    
    Args:
        severity: Filter by severity level
        alert_type: Filter by alert type
        hours: Time window in hours
    
    Returns:
        List of active alerts
    """
    from shared.monitoring.alerts import AlertSeverity, AlertType
    
    alert_manager = get_alert_manager()
    
    # Parse filters
    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity.lower())
        except ValueError:
            pass
    
    type_filter = None
    if alert_type:
        try:
            type_filter = AlertType(alert_type.lower())
        except ValueError:
            pass
    
    alerts = alert_manager.get_active_alerts(
        severity=severity_filter,
        alert_type=type_filter,
        hours=hours
    )
    
    return {
        "total": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.get("/alerts/history")
async def get_alert_history(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve")
):
    """
    Get alert history
    
    Args:
        hours: Number of hours of history (1-168)
    
    Returns:
        Historical alert data
    """
    alert_manager = get_alert_manager()
    return {
        "history": alert_manager.get_alert_history(hours=hours)
    }


@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get comprehensive dashboard data
    
    Returns:
        Aggregated data for performance dashboard including:
        - System status
        - Alert summary
        - Resource usage
        - Performance metrics
    """
    alert_manager = get_alert_manager()
    resource_monitor = get_resource_monitor()
    metrics_collector = get_metrics_collector()
    
    dashboard_data = alert_manager.get_dashboard_data()
    resource_summary = resource_monitor.get_summary()
    metrics_summary = metrics_collector.get_metrics_summary()
    
    return {
        **dashboard_data,
        "resources": {
            "cpu_percent": resource_summary.get('cpu_percent'),
            "memory_percent": resource_summary.get('memory_percent'),
            "memory_available_mb": resource_summary.get('memory_available_mb'),
            "disk_percent": resource_summary.get('disk_percent'),
            "disk_free_gb": resource_summary.get('disk_free_gb')
        },
        "metrics": metrics_summary
    }


@router.post("/monitoring/start")
async def start_monitoring():
    """
    Start background resource monitoring
    
    Returns:
        Status message
    """
    resource_monitor = get_resource_monitor()
    resource_monitor.start_monitoring()
    
    return {
        "status": "success",
        "message": "Background resource monitoring started"
    }


@router.post("/monitoring/stop")
async def stop_monitoring():
    """
    Stop background resource monitoring
    
    Returns:
        Status message
    """
    resource_monitor = get_resource_monitor()
    resource_monitor.stop_monitoring()
    
    return {
        "status": "success",
        "message": "Background resource monitoring stopped"
    }


@router.get("/performance/eligibility")
async def get_eligibility_performance():
    """
    Get eligibility engine performance metrics
    
    Returns:
        Eligibility-specific performance data
    """
    collector = get_metrics_collector()
    
    # This would aggregate from Prometheus metrics
    # For now, return summary
    return {
        "message": "Eligibility performance metrics",
        "requirement": "< 5 seconds per evaluation",
        "note": "Use /metrics endpoint for detailed Prometheus metrics"
    }


@router.get("/performance/requirements")
async def get_performance_requirements():
    """
    Get system performance requirements and current status
    
    Returns:
        Performance requirements and compliance status
    """
    alert_manager = get_alert_manager()
    
    return {
        "requirements": {
            "eligibility_evaluation_time": {
                "threshold": 5.0,
                "unit": "seconds",
                "description": "Maximum time for eligibility evaluation"
            },
            "uptime": {
                "threshold": 0.995,
                "unit": "percentage",
                "description": "Minimum uptime during business hours (99.5%)"
            },
            "concurrent_users": {
                "threshold": 1000,
                "unit": "users",
                "description": "Minimum concurrent user support"
            },
            "max_simultaneous_evaluations": {
                "threshold": 10000,
                "unit": "evaluations",
                "description": "Maximum simultaneous eligibility evaluations"
            }
        },
        "thresholds": alert_manager.thresholds
    }
