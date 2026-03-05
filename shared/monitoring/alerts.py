"""
Alert Management Module
Implements performance dashboards and alerting system
Requirements: 9.1, 9.5
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"
    SECURITY = "security"


class Alert:
    """Represents a system alert"""
    
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
        current_value: Optional[float] = None
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.threshold = threshold
        self.current_value = current_value
        self.timestamp = datetime.utcnow()
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'type': self.alert_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.alert_type.value}: {self.message}"


class AlertManager:
    """
    Alert management system for SarvaSahay Platform
    
    Features:
    - Configurable alert thresholds
    - Alert history and tracking
    - Alert notification handlers
    - Dashboard data aggregation
    """
    
    def __init__(self):
        """Initialize alert manager"""
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        
        # Alert thresholds (Requirements 9.1, 9.5)
        self.thresholds = {
            'eligibility_evaluation_time': 5.0,  # seconds (Requirement 9.1)
            'request_duration': 5.0,  # seconds
            'cpu_usage': 80.0,  # percent
            'memory_usage': 85.0,  # percent
            'disk_usage': 90.0,  # percent
            'error_rate': 0.05,  # 5% error rate
            'uptime': 0.995,  # 99.5% uptime (Requirement 9.5)
            'concurrent_users': 1000,  # max concurrent users
            'api_failure_rate': 0.10  # 10% API failure rate
        }
        
        # Alert history retention
        self.max_alert_history = 1000
        self.alert_retention_hours = 24
        
        logger.info("AlertManager initialized")
    
    def set_threshold(self, metric: str, value: float):
        """Set alert threshold for a metric"""
        self.thresholds[metric] = value
        logger.info(f"Alert threshold set: {metric} = {value}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        Add alert notification handler
        
        Args:
            handler: Callable that receives Alert objects
        """
        self.alert_handlers.append(handler)
        logger.info(f"Alert handler added: {handler.__name__}")
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
        current_value: Optional[float] = None
    ) -> Alert:
        """Create and process a new alert"""
        alert = Alert(alert_type, severity, message, details, threshold, current_value)
        
        # Add to history
        self.alerts.append(alert)
        
        # Trim history if needed
        if len(self.alerts) > self.max_alert_history:
            self.alerts = self.alerts[-self.max_alert_history:]
        
        # Log alert
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(severity, logger.info)
        
        log_method(str(alert))
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        return alert
    
    def check_performance_threshold(
        self,
        metric_name: str,
        current_value: float,
        operation: str = "eligibility_evaluation"
    ):
        """Check if performance metric exceeds threshold"""
        threshold = self.thresholds.get(metric_name)
        
        if threshold and current_value > threshold:
            self.create_alert(
                alert_type=AlertType.PERFORMANCE,
                severity=AlertSeverity.WARNING if current_value < threshold * 1.5 else AlertSeverity.ERROR,
                message=f"{operation} exceeded {metric_name} threshold",
                details={
                    'operation': operation,
                    'metric': metric_name
                },
                threshold=threshold,
                current_value=current_value
            )
    
    def check_resource_threshold(
        self,
        resource_name: str,
        current_value: float
    ):
        """Check if resource usage exceeds threshold"""
        threshold_key = f"{resource_name}_usage"
        threshold = self.thresholds.get(threshold_key)
        
        if threshold and current_value > threshold:
            severity = AlertSeverity.CRITICAL if current_value > 95 else AlertSeverity.WARNING
            
            self.create_alert(
                alert_type=AlertType.RESOURCE,
                severity=severity,
                message=f"High {resource_name} usage detected",
                details={'resource': resource_name},
                threshold=threshold,
                current_value=current_value
            )
    
    def check_error_rate(
        self,
        total_requests: int,
        error_count: int,
        time_window: str = "1m"
    ):
        """Check if error rate exceeds threshold"""
        if total_requests == 0:
            return
        
        error_rate = error_count / total_requests
        threshold = self.thresholds.get('error_rate', 0.05)
        
        if error_rate > threshold:
            self.create_alert(
                alert_type=AlertType.ERROR_RATE,
                severity=AlertSeverity.ERROR,
                message=f"High error rate in last {time_window}",
                details={
                    'total_requests': total_requests,
                    'error_count': error_count,
                    'time_window': time_window
                },
                threshold=threshold,
                current_value=error_rate
            )
    
    def check_uptime(self, uptime_percentage: float):
        """Check if uptime meets requirement (99.5%)"""
        threshold = self.thresholds.get('uptime', 0.995)
        
        if uptime_percentage < threshold:
            self.create_alert(
                alert_type=AlertType.AVAILABILITY,
                severity=AlertSeverity.CRITICAL,
                message=f"Uptime below requirement: {uptime_percentage:.2%}",
                details={'uptime_percentage': uptime_percentage},
                threshold=threshold,
                current_value=uptime_percentage
            )
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        hours: int = 1
    ) -> List[Alert]:
        """
        Get active alerts within time window
        
        Args:
            severity: Filter by severity level
            alert_type: Filter by alert type
            hours: Time window in hours
        
        Returns:
            List of matching alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time and not alert.acknowledged
        ]
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
        
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a.alert_type == alert_type]
        
        return filtered_alerts
    
    def acknowledge_alert(self, alert: Alert):
        """Mark alert as acknowledged"""
        alert.acknowledged = True
        logger.info(f"Alert acknowledged: {alert}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get aggregated data for performance dashboard
        
        Returns:
            Dashboard data including alerts, metrics, and status
        """
        now = datetime.utcnow()
        
        # Get alerts from last hour
        recent_alerts = self.get_active_alerts(hours=1)
        
        # Count by severity
        alert_counts = {
            'critical': len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
            'error': len([a for a in recent_alerts if a.severity == AlertSeverity.ERROR]),
            'warning': len([a for a in recent_alerts if a.severity == AlertSeverity.WARNING]),
            'info': len([a for a in recent_alerts if a.severity == AlertSeverity.INFO])
        }
        
        # Count by type
        alert_types = {
            'performance': len([a for a in recent_alerts if a.alert_type == AlertType.PERFORMANCE]),
            'resource': len([a for a in recent_alerts if a.alert_type == AlertType.RESOURCE]),
            'error_rate': len([a for a in recent_alerts if a.alert_type == AlertType.ERROR_RATE]),
            'availability': len([a for a in recent_alerts if a.alert_type == AlertType.AVAILABILITY])
        }
        
        # Overall system status
        system_status = "healthy"
        if alert_counts['critical'] > 0:
            system_status = "critical"
        elif alert_counts['error'] > 0:
            system_status = "degraded"
        elif alert_counts['warning'] > 0:
            system_status = "warning"
        
        return {
            'timestamp': now.isoformat(),
            'system_status': system_status,
            'alert_summary': {
                'total_active': len(recent_alerts),
                'by_severity': alert_counts,
                'by_type': alert_types
            },
            'recent_alerts': [alert.to_dict() for alert in recent_alerts[:10]],
            'thresholds': self.thresholds
        }
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified time window"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        historical_alerts = [
            alert.to_dict()
            for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        return historical_alerts
    
    def clear_old_alerts(self):
        """Remove alerts older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.alert_retention_hours)
        
        original_count = len(self.alerts)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        removed_count = original_count - len(self.alerts)
        if removed_count > 0:
            logger.info(f"Cleared {removed_count} old alerts")


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


# Example alert handler for logging
def log_alert_handler(alert: Alert):
    """Simple alert handler that logs to file"""
    logger.info(f"Alert triggered: {alert.to_dict()}")


# Example alert handler for notifications
def notification_alert_handler(alert: Alert):
    """Alert handler that sends notifications for critical alerts"""
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR]:
        # In production, integrate with notification service
        logger.critical(f"CRITICAL ALERT: {alert.message}")
