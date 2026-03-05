"""
Unit Tests for Performance Monitoring and Metrics
Tests metrics collection, resource monitoring, and alerting
Requirements: 9.1, 9.5
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from shared.monitoring.metrics import (
    MetricsCollector,
    get_metrics_collector,
    track_request_time,
    track_eligibility_evaluation
)
from shared.monitoring.resource_monitor import ResourceMonitor, get_resource_monitor
from shared.monitoring.alerts import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertType,
    get_alert_manager
)


class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initializes correctly"""
        collector = MetricsCollector()
        
        assert collector.registry is not None
        assert collector.request_count is not None
        assert collector.request_duration is not None
        assert collector.eligibility_evaluation_duration is not None
    
    def test_track_request(self):
        """Test request tracking"""
        collector = MetricsCollector()
        
        collector.track_request("GET", "/api/v1/profiles", 200, 0.5)
        collector.track_request("POST", "/api/v1/eligibility", 200, 1.2)
        
        # Verify metrics were recorded
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_requests_total' in metrics_text
        assert 'sarvasahay_request_duration_seconds' in metrics_text
    
    def test_track_slow_request(self):
        """Test slow request detection (>5 seconds)"""
        collector = MetricsCollector()
        
        with patch('shared.monitoring.metrics.logger') as mock_logger:
            collector.track_request("GET", "/api/v1/slow", 200, 6.5)
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Slow request detected" in call_args
            assert "6.5" in call_args
    
    def test_track_eligibility_evaluation(self):
        """Test eligibility evaluation tracking"""
        collector = MetricsCollector()
        
        collector.track_eligibility_evaluation(
            duration=2.5,
            schemes_matched=15,
            profile_type="farmer",
            status="success"
        )
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_eligibility_evaluation_seconds' in metrics_text
        assert 'sarvasahay_schemes_matched' in metrics_text
    
    def test_track_eligibility_evaluation_exceeds_threshold(self):
        """Test alert when eligibility evaluation exceeds 5 seconds"""
        collector = MetricsCollector()
        
        with patch('shared.monitoring.metrics.logger') as mock_logger:
            collector.track_eligibility_evaluation(
                duration=6.0,
                schemes_matched=30,
                status="success"
            )
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "exceeded 5s requirement" in call_args
    
    def test_track_document_processing(self):
        """Test document processing tracking"""
        collector = MetricsCollector()
        
        collector.track_document_processing(
            document_type="aadhaar",
            duration=3.5,
            status="success",
            accuracy=0.95
        )
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_document_processing_seconds' in metrics_text
        assert 'sarvasahay_documents_processed_total' in metrics_text
    
    def test_track_application_submission(self):
        """Test application submission tracking"""
        collector = MetricsCollector()
        
        collector.track_application_submission(
            scheme="pm_kisan",
            duration=5.0,
            status="success"
        )
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_applications_submitted_total' in metrics_text
    
    def test_track_gov_api_call(self):
        """Test government API call tracking"""
        collector = MetricsCollector()
        
        collector.track_gov_api_call(
            api_name="pm_kisan",
            duration=2.0,
            status="success"
        )
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_gov_api_requests_total' in metrics_text
        assert 'sarvasahay_gov_api_duration_seconds' in metrics_text
    
    def test_track_cache_operation(self):
        """Test cache operation tracking"""
        collector = MetricsCollector()
        
        collector.track_cache_operation("profile", hit=True)
        collector.track_cache_operation("profile", hit=False)
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_cache_hits_total' in metrics_text
        assert 'sarvasahay_cache_misses_total' in metrics_text
    
    def test_track_error(self):
        """Test error tracking"""
        collector = MetricsCollector()
        
        collector.track_error("ValueError", severity="error")
        collector.track_error("TimeoutError", severity="warning")
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_errors_total' in metrics_text
    
    def test_concurrent_request_tracking(self):
        """Test concurrent request counter"""
        collector = MetricsCollector()
        
        collector.increment_concurrent_requests()
        collector.increment_concurrent_requests()
        collector.decrement_concurrent_requests()
        
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_concurrent_requests' in metrics_text
    
    def test_get_metrics_summary(self):
        """Test metrics summary generation"""
        collector = MetricsCollector()
        
        # Track some metrics
        collector.track_request("GET", "/test", 200, 1.0)
        collector.track_eligibility_evaluation(2.0, 10)
        collector.track_cache_operation("test", hit=True)
        
        summary = collector.get_metrics_summary()
        
        assert "requests" in summary
        assert "eligibility" in summary
        assert "cache" in summary
    
    def test_decorator_track_request_time(self):
        """Test request time tracking decorator"""
        @track_request_time("/test", "GET")
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # Verify metrics were tracked
        collector = get_metrics_collector()
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_requests_total' in metrics_text
    
    def test_decorator_track_eligibility_evaluation(self):
        """Test eligibility evaluation tracking decorator"""
        @track_eligibility_evaluation
        def evaluate_eligibility():
            time.sleep(0.1)
            return ["scheme1", "scheme2", "scheme3"]
        
        result = evaluate_eligibility()
        assert len(result) == 3
        
        # Verify metrics were tracked
        collector = get_metrics_collector()
        metrics_text = collector.get_metrics().decode('utf-8')
        assert 'sarvasahay_eligibility_evaluation_seconds' in metrics_text


class TestResourceMonitor:
    """Test resource monitoring functionality"""
    
    def test_resource_monitor_initialization(self):
        """Test resource monitor initializes correctly"""
        monitor = ResourceMonitor(interval=60)
        
        assert monitor.interval == 60
        assert not monitor.monitoring
        assert monitor.history is not None
    
    @patch('psutil.cpu_percent')
    @patch('psutil.cpu_count')
    def test_get_cpu_metrics(self, mock_cpu_count, mock_cpu_percent):
        """Test CPU metrics collection"""
        mock_cpu_percent.return_value = 45.5
        mock_cpu_count.return_value = 4
        
        monitor = ResourceMonitor()
        metrics = monitor.get_cpu_metrics()
        
        assert 'cpu_percent' in metrics
        assert 'cpu_count' in metrics
        assert metrics['cpu_count'] == 4
    
    @patch('psutil.virtual_memory')
    @patch('psutil.swap_memory')
    def test_get_memory_metrics(self, mock_swap, mock_memory):
        """Test memory metrics collection"""
        mock_memory.return_value = MagicMock(
            total=8 * 1024 * 1024 * 1024,  # 8GB
            available=4 * 1024 * 1024 * 1024,  # 4GB
            used=4 * 1024 * 1024 * 1024,  # 4GB
            percent=50.0
        )
        mock_swap.return_value = MagicMock(
            total=2 * 1024 * 1024 * 1024,
            used=0,
            percent=0
        )
        
        monitor = ResourceMonitor()
        metrics = monitor.get_memory_metrics()
        
        assert 'total_mb' in metrics
        assert 'percent' in metrics
        assert metrics['percent'] == 50.0
    
    @patch('psutil.disk_usage')
    def test_get_disk_metrics(self, mock_disk):
        """Test disk metrics collection"""
        mock_disk.return_value = MagicMock(
            total=100 * 1024 ** 3,  # 100GB
            used=50 * 1024 ** 3,  # 50GB
            free=50 * 1024 ** 3,  # 50GB
            percent=50.0
        )
        
        monitor = ResourceMonitor()
        metrics = monitor.get_disk_metrics()
        
        assert 'total_gb' in metrics
        assert 'percent' in metrics
        assert metrics['percent'] == 50.0
    
    def test_get_all_metrics(self):
        """Test getting all metrics at once"""
        monitor = ResourceMonitor()
        metrics = monitor.get_all_metrics()
        
        assert 'timestamp' in metrics
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'disk' in metrics
        assert 'network' in metrics
        assert 'process' in metrics
    
    def test_check_resource_alerts(self):
        """Test resource alert checking"""
        monitor = ResourceMonitor()
        
        # Test high CPU alert
        metrics = {
            'cpu': {'cpu_percent': 85.0},
            'memory': {'percent': 70.0},
            'disk': {'percent': 60.0}
        }
        
        alerts = monitor.check_resource_alerts(metrics)
        assert len(alerts) > 0
        assert any(a['resource'] == 'cpu' for a in alerts)
    
    def test_get_summary(self):
        """Test resource summary generation"""
        monitor = ResourceMonitor()
        summary = monitor.get_summary()
        
        assert 'timestamp' in summary
        assert 'cpu_percent' in summary
        assert 'memory_percent' in summary
        assert 'alerts' in summary


class TestAlertManager:
    """Test alert management functionality"""
    
    def test_alert_creation(self):
        """Test creating an alert"""
        alert = Alert(
            alert_type=AlertType.PERFORMANCE,
            severity=AlertSeverity.WARNING,
            message="High response time detected",
            threshold=5.0,
            current_value=6.5
        )
        
        assert alert.alert_type == AlertType.PERFORMANCE
        assert alert.severity == AlertSeverity.WARNING
        assert alert.message == "High response time detected"
        assert not alert.acknowledged
    
    def test_alert_to_dict(self):
        """Test alert serialization"""
        alert = Alert(
            alert_type=AlertType.RESOURCE,
            severity=AlertSeverity.ERROR,
            message="High memory usage"
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict['type'] == 'resource'
        assert alert_dict['severity'] == 'error'
        assert alert_dict['message'] == 'High memory usage'
        assert 'timestamp' in alert_dict
    
    def test_alert_manager_initialization(self):
        """Test alert manager initializes correctly"""
        manager = AlertManager()
        
        assert manager.thresholds is not None
        assert manager.thresholds['eligibility_evaluation_time'] == 5.0
        assert manager.thresholds['uptime'] == 0.995
    
    def test_set_threshold(self):
        """Test setting alert threshold"""
        manager = AlertManager()
        
        manager.set_threshold('custom_metric', 10.0)
        assert manager.thresholds['custom_metric'] == 10.0
    
    def test_create_alert(self):
        """Test creating and storing alert"""
        manager = AlertManager()
        
        alert = manager.create_alert(
            alert_type=AlertType.PERFORMANCE,
            severity=AlertSeverity.WARNING,
            message="Test alert"
        )
        
        assert alert in manager.alerts
        assert len(manager.alerts) > 0
    
    def test_check_performance_threshold(self):
        """Test performance threshold checking"""
        manager = AlertManager()
        
        # Should create alert when exceeding threshold
        manager.check_performance_threshold(
            'eligibility_evaluation_time',
            6.0,
            'eligibility_check'
        )
        
        assert len(manager.alerts) > 0
        assert manager.alerts[-1].alert_type == AlertType.PERFORMANCE
    
    def test_check_resource_threshold(self):
        """Test resource threshold checking"""
        manager = AlertManager()
        
        # Should create alert for high CPU
        manager.check_resource_threshold('cpu', 85.0)
        
        assert len(manager.alerts) > 0
        assert manager.alerts[-1].alert_type == AlertType.RESOURCE
    
    def test_check_error_rate(self):
        """Test error rate checking"""
        manager = AlertManager()
        
        # 10% error rate should trigger alert (threshold is 5%)
        manager.check_error_rate(
            total_requests=100,
            error_count=10,
            time_window="1m"
        )
        
        assert len(manager.alerts) > 0
        assert manager.alerts[-1].alert_type == AlertType.ERROR_RATE
    
    def test_check_uptime(self):
        """Test uptime requirement checking (99.5%)"""
        manager = AlertManager()
        
        # 99.0% uptime should trigger alert (requirement is 99.5%)
        manager.check_uptime(0.990)
        
        assert len(manager.alerts) > 0
        assert manager.alerts[-1].alert_type == AlertType.AVAILABILITY
        assert manager.alerts[-1].severity == AlertSeverity.CRITICAL
    
    def test_get_active_alerts(self):
        """Test retrieving active alerts"""
        manager = AlertManager()
        
        # Create some alerts
        manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.WARNING,
            "Alert 1"
        )
        manager.create_alert(
            AlertType.RESOURCE,
            AlertSeverity.ERROR,
            "Alert 2"
        )
        
        active_alerts = manager.get_active_alerts(hours=1)
        assert len(active_alerts) == 2
    
    def test_get_active_alerts_with_filters(self):
        """Test filtering active alerts"""
        manager = AlertManager()
        
        manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.WARNING,
            "Warning alert"
        )
        manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.ERROR,
            "Error alert"
        )
        
        # Filter by severity
        warnings = manager.get_active_alerts(severity=AlertSeverity.WARNING)
        assert len(warnings) == 1
        assert warnings[0].severity == AlertSeverity.WARNING
    
    def test_acknowledge_alert(self):
        """Test acknowledging alerts"""
        manager = AlertManager()
        
        alert = manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.WARNING,
            "Test alert"
        )
        
        assert not alert.acknowledged
        
        manager.acknowledge_alert(alert)
        assert alert.acknowledged
    
    def test_get_dashboard_data(self):
        """Test dashboard data generation"""
        manager = AlertManager()
        
        # Create some alerts
        manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.WARNING,
            "Alert 1"
        )
        manager.create_alert(
            AlertType.RESOURCE,
            AlertSeverity.CRITICAL,
            "Alert 2"
        )
        
        dashboard = manager.get_dashboard_data()
        
        assert 'system_status' in dashboard
        assert 'alert_summary' in dashboard
        assert 'recent_alerts' in dashboard
        assert dashboard['system_status'] == 'critical'  # Due to critical alert
    
    def test_alert_handler(self):
        """Test alert handler registration and execution"""
        manager = AlertManager()
        
        handler_called = []
        
        def test_handler(alert: Alert):
            handler_called.append(alert)
        
        manager.add_alert_handler(test_handler)
        
        alert = manager.create_alert(
            AlertType.PERFORMANCE,
            AlertSeverity.WARNING,
            "Test alert"
        )
        
        assert len(handler_called) == 1
        assert handler_called[0] == alert


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
