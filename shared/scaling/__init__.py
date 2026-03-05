"""
Horizontal Scaling Module
Implements stateless service design and auto-scaling capabilities
"""

from .stateless import StatelessService, get_session_manager
from .load_balancer import LoadBalancerConfig, HealthCheckConfig
from .autoscaler import AutoScaler, ScalingPolicy, get_autoscaler

__all__ = [
    'StatelessService',
    'get_session_manager',
    'LoadBalancerConfig',
    'HealthCheckConfig',
    'AutoScaler',
    'ScalingPolicy',
    'get_autoscaler'
]
