"""
System Resource Monitoring Module
Tracks CPU, memory, disk, and network usage
Requirements: 9.1, 9.5
"""

import psutil
import time
import logging
from typing import Dict, Any, Optional
from threading import Thread, Event
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    System resource monitoring for SarvaSahay Platform
    
    Monitors:
    - CPU usage and load average
    - Memory usage (RAM)
    - Disk I/O and space
    - Network I/O
    - Process-specific metrics
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize resource monitor
        
        Args:
            interval: Monitoring interval in seconds (default: 60)
        """
        self.interval = interval
        self.monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        # Historical data storage (last 24 hours)
        self.max_history_points = 1440  # 24 hours at 1-minute intervals
        self.history: Dict[str, list] = {
            'timestamps': [],
            'cpu_percent': [],
            'memory_percent': [],
            'disk_usage_percent': [],
            'network_bytes_sent': [],
            'network_bytes_recv': []
        }
        
        logger.info(f"ResourceMonitor initialized with {interval}s interval")
    
    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get current CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_average_1m': load_avg[0],
                'load_average_5m': load_avg[1],
                'load_average_15m': load_avg[2],
                'per_cpu': psutil.cpu_percent(percpu=True)
            }
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {}
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent': memory.percent,
                'swap_total_mb': swap.total / (1024 * 1024),
                'swap_used_mb': swap.used / (1024 * 1024),
                'swap_percent': swap.percent
            }
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {}
    
    def get_disk_metrics(self) -> Dict[str, Any]:
        """Get current disk metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            metrics = {
                'total_gb': disk_usage.total / (1024 ** 3),
                'used_gb': disk_usage.used / (1024 ** 3),
                'free_gb': disk_usage.free / (1024 ** 3),
                'percent': disk_usage.percent
            }
            
            if disk_io:
                metrics.update({
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                })
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting disk metrics: {e}")
            return {}
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get current network metrics"""
        try:
            net_io = psutil.net_io_counters()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'drops_in': net_io.dropin,
                'drops_out': net_io.dropout
            }
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {}
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """Get current process-specific metrics"""
        try:
            process = psutil.Process()
            
            with process.oneshot():
                return {
                    'pid': process.pid,
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / (1024 * 1024),
                    'memory_percent': process.memory_percent(),
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                    'connections': len(process.connections()),
                    'status': process.status()
                }
        except Exception as e:
            logger.error(f"Error getting process metrics: {e}")
            return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all system resource metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics(),
            'process': self.get_process_metrics()
        }
    
    def check_resource_alerts(self, metrics: Dict[str, Any]) -> list:
        """
        Check for resource usage alerts
        
        Returns list of alert messages if thresholds exceeded
        """
        alerts = []
        
        # CPU alert (>80%)
        cpu_percent = metrics.get('cpu', {}).get('cpu_percent', 0)
        if cpu_percent > 80:
            alerts.append({
                'severity': 'warning',
                'resource': 'cpu',
                'message': f'High CPU usage: {cpu_percent:.1f}%',
                'value': cpu_percent,
                'threshold': 80
            })
        
        # Memory alert (>85%)
        memory_percent = metrics.get('memory', {}).get('percent', 0)
        if memory_percent > 85:
            alerts.append({
                'severity': 'warning',
                'resource': 'memory',
                'message': f'High memory usage: {memory_percent:.1f}%',
                'value': memory_percent,
                'threshold': 85
            })
        
        # Disk alert (>90%)
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > 90:
            alerts.append({
                'severity': 'critical',
                'resource': 'disk',
                'message': f'High disk usage: {disk_percent:.1f}%',
                'value': disk_percent,
                'threshold': 90
            })
        
        return alerts
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        logger.info("Resource monitoring started")
        
        while not self.stop_event.is_set():
            try:
                # Collect metrics
                metrics = self.get_all_metrics()
                
                # Store in history
                self.history['timestamps'].append(metrics['timestamp'])
                self.history['cpu_percent'].append(metrics['cpu'].get('cpu_percent', 0))
                self.history['memory_percent'].append(metrics['memory'].get('percent', 0))
                self.history['disk_usage_percent'].append(metrics['disk'].get('percent', 0))
                self.history['network_bytes_sent'].append(metrics['network'].get('bytes_sent', 0))
                self.history['network_bytes_recv'].append(metrics['network'].get('bytes_recv', 0))
                
                # Trim history to max size
                for key in self.history:
                    if len(self.history[key]) > self.max_history_points:
                        self.history[key] = self.history[key][-self.max_history_points:]
                
                # Check for alerts
                alerts = self.check_resource_alerts(metrics)
                for alert in alerts:
                    logger.warning(f"Resource alert: {alert['message']}")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next interval
            self.stop_event.wait(self.interval)
        
        logger.info("Resource monitoring stopped")
    
    def start_monitoring(self):
        """Start background resource monitoring"""
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Background resource monitoring started")
    
    def stop_monitoring(self):
        """Stop background resource monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Background resource monitoring stopped")
    
    def get_history(self, hours: int = 1) -> Dict[str, list]:
        """
        Get historical metrics
        
        Args:
            hours: Number of hours of history to return (default: 1)
        
        Returns:
            Dictionary with historical data
        """
        if not self.history['timestamps']:
            return {}
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Find index of first timestamp after cutoff
        start_idx = 0
        for i, ts_str in enumerate(self.history['timestamps']):
            ts = datetime.fromisoformat(ts_str)
            if ts >= cutoff_time:
                start_idx = i
                break
        
        # Return sliced history
        return {
            key: values[start_idx:] 
            for key, values in self.history.items()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current resource usage"""
        metrics = self.get_all_metrics()
        
        return {
            'timestamp': metrics['timestamp'],
            'cpu_percent': metrics['cpu'].get('cpu_percent', 0),
            'memory_percent': metrics['memory'].get('percent', 0),
            'memory_available_mb': metrics['memory'].get('available_mb', 0),
            'disk_percent': metrics['disk'].get('percent', 0),
            'disk_free_gb': metrics['disk'].get('free_gb', 0),
            'process_memory_mb': metrics['process'].get('memory_mb', 0),
            'process_threads': metrics['process'].get('num_threads', 0),
            'alerts': self.check_resource_alerts(metrics)
        }


# Global resource monitor instance
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get or create global resource monitor instance"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor
