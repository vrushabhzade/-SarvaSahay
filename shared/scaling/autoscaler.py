"""
Auto-Scaling Module
Implements auto-scaling based on load metrics
Requirements: 9.2, 9.3
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ScalingDirection(Enum):
    """Scaling direction"""
    UP = "up"
    DOWN = "down"
    NONE = "none"


class ScalingMetric(Enum):
    """Metrics used for auto-scaling decisions"""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    CONCURRENT_USERS = "concurrent_users"
    ERROR_RATE = "error_rate"


class ScalingPolicy(BaseModel):
    """Auto-scaling policy configuration"""
    
    name: str = Field(..., description="Policy name")
    metric: ScalingMetric = Field(..., description="Metric to monitor")
    
    # Scale up thresholds
    scale_up_threshold: float = Field(..., description="Threshold to trigger scale up")
    scale_up_increment: int = Field(default=1, description="Number of instances to add")
    scale_up_cooldown_seconds: int = Field(default=300, description="Cooldown after scale up")
    
    # Scale down thresholds
    scale_down_threshold: float = Field(..., description="Threshold to trigger scale down")
    scale_down_decrement: int = Field(default=1, description="Number of instances to remove")
    scale_down_cooldown_seconds: int = Field(default=600, description="Cooldown after scale down")
    
    # Instance limits
    min_instances: int = Field(default=2, description="Minimum number of instances")
    max_instances: int = Field(default=10, description="Maximum number of instances")
    
    # Evaluation settings
    evaluation_periods: int = Field(default=2, description="Number of periods to evaluate")
    evaluation_period_seconds: int = Field(default=60, description="Length of evaluation period")
    
    enabled: bool = Field(default=True, description="Enable this policy")
    
    class Config:
        use_enum_values = True


class ScalingEvent(BaseModel):
    """Record of a scaling event"""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    direction: ScalingDirection
    policy_name: str
    metric_value: float
    threshold: float
    instances_before: int
    instances_after: int
    reason: str


class AutoScaler:
    """
    Auto-scaling manager for SarvaSahay Platform
    
    Monitors metrics and scales instances based on policies
    Requirements: 9.2 (horizontal scaling), 9.3 (scale to new regions)
    """
    
    def __init__(self):
        """Initialize auto-scaler"""
        self.policies: List[ScalingPolicy] = []
        self.current_instances = 2  # Start with 2 instances
        self.scaling_history: List[ScalingEvent] = []
        self.last_scale_time: Optional[datetime] = None
        self.metric_history: Dict[str, List[float]] = {}
        
        logger.info("AutoScaler initialized")
    
    def add_policy(self, policy: ScalingPolicy):
        """
        Add scaling policy
        
        Args:
            policy: Scaling policy configuration
        """
        self.policies.append(policy)
        logger.info(f"Added scaling policy: {policy.name}")
    
    def remove_policy(self, policy_name: str):
        """
        Remove scaling policy
        
        Args:
            policy_name: Name of policy to remove
        """
        self.policies = [p for p in self.policies if p.name != policy_name]
        logger.info(f"Removed scaling policy: {policy_name}")
    
    def record_metric(self, metric: ScalingMetric, value: float):
        """
        Record metric value for evaluation
        
        Args:
            metric: Metric type
            value: Metric value
        """
        metric_key = metric.value
        
        if metric_key not in self.metric_history:
            self.metric_history[metric_key] = []
        
        self.metric_history[metric_key].append(value)
        
        # Keep only recent history (last 100 data points)
        if len(self.metric_history[metric_key]) > 100:
            self.metric_history[metric_key] = self.metric_history[metric_key][-100:]
    
    def get_metric_average(self, metric: ScalingMetric, periods: int = 2) -> Optional[float]:
        """
        Get average metric value over recent periods
        
        Args:
            metric: Metric type
            periods: Number of periods to average
        
        Returns:
            Average value or None if insufficient data
        """
        # Handle both enum and string values
        metric_key = metric.value if isinstance(metric, ScalingMetric) else metric
        
        if metric_key not in self.metric_history:
            return None
        
        history = self.metric_history[metric_key]
        if len(history) < periods:
            return None
        
        recent_values = history[-periods:]
        return sum(recent_values) / len(recent_values)
    
    def is_in_cooldown(self, policy: ScalingPolicy, direction: ScalingDirection) -> bool:
        """
        Check if policy is in cooldown period
        
        Args:
            policy: Scaling policy
            direction: Scaling direction
        
        Returns:
            True if in cooldown
        """
        if not self.last_scale_time:
            return False
        
        cooldown_seconds = (
            policy.scale_up_cooldown_seconds if direction == ScalingDirection.UP
            else policy.scale_down_cooldown_seconds
        )
        
        time_since_last_scale = (datetime.utcnow() - self.last_scale_time).total_seconds()
        return time_since_last_scale < cooldown_seconds
    
    def evaluate_policy(self, policy: ScalingPolicy) -> ScalingDirection:
        """
        Evaluate scaling policy
        
        Args:
            policy: Scaling policy to evaluate
        
        Returns:
            Scaling direction (UP, DOWN, or NONE)
        """
        if not policy.enabled:
            return ScalingDirection.NONE
        
        # Get average metric value
        avg_value = self.get_metric_average(policy.metric, policy.evaluation_periods)
        
        if avg_value is None:
            logger.debug(f"Insufficient data for policy: {policy.name}")
            return ScalingDirection.NONE
        
        # Check scale up condition
        if avg_value >= policy.scale_up_threshold:
            if self.current_instances >= policy.max_instances:
                logger.info(f"At max instances ({policy.max_instances}), cannot scale up")
                return ScalingDirection.NONE
            
            if self.is_in_cooldown(policy, ScalingDirection.UP):
                logger.debug(f"Policy {policy.name} in scale-up cooldown")
                return ScalingDirection.NONE
            
            metric_name = policy.metric if isinstance(policy.metric, str) else policy.metric.value
            logger.info(
                f"Scale up triggered: {metric_name}={avg_value:.2f} "
                f">= {policy.scale_up_threshold}"
            )
            return ScalingDirection.UP
        
        # Check scale down condition
        if avg_value <= policy.scale_down_threshold:
            if self.current_instances <= policy.min_instances:
                logger.info(f"At min instances ({policy.min_instances}), cannot scale down")
                return ScalingDirection.NONE
            
            if self.is_in_cooldown(policy, ScalingDirection.DOWN):
                logger.debug(f"Policy {policy.name} in scale-down cooldown")
                return ScalingDirection.NONE
            
            metric_name = policy.metric if isinstance(policy.metric, str) else policy.metric.value
            logger.info(
                f"Scale down triggered: {metric_name}={avg_value:.2f} "
                f"<= {policy.scale_down_threshold}"
            )
            return ScalingDirection.DOWN
        
        return ScalingDirection.NONE
    
    def execute_scaling(
        self,
        direction: ScalingDirection,
        policy: ScalingPolicy,
        metric_value: float
    ) -> bool:
        """
        Execute scaling action
        
        Args:
            direction: Scaling direction
            policy: Policy that triggered scaling
            metric_value: Current metric value
        
        Returns:
            True if scaling was executed
        """
        if direction == ScalingDirection.NONE:
            return False
        
        instances_before = self.current_instances
        
        if direction == ScalingDirection.UP:
            self.current_instances += policy.scale_up_increment
            self.current_instances = min(self.current_instances, policy.max_instances)
            threshold = policy.scale_up_threshold
            metric_name = policy.metric if isinstance(policy.metric, str) else policy.metric.value
            reason = f"{metric_name} exceeded threshold"
        else:  # ScalingDirection.DOWN
            self.current_instances -= policy.scale_down_decrement
            self.current_instances = max(self.current_instances, policy.min_instances)
            threshold = policy.scale_down_threshold
            metric_name = policy.metric if isinstance(policy.metric, str) else policy.metric.value
            reason = f"{metric_name} below threshold"
        
        instances_after = self.current_instances
        
        # Record scaling event
        event = ScalingEvent(
            direction=direction,
            policy_name=policy.name,
            metric_value=metric_value,
            threshold=threshold,
            instances_before=instances_before,
            instances_after=instances_after,
            reason=reason
        )
        
        self.scaling_history.append(event)
        self.last_scale_time = datetime.utcnow()
        
        logger.info(
            f"Scaling executed: {direction.value} from {instances_before} to {instances_after} instances"
        )
        
        return True
    
    def evaluate_all_policies(self) -> List[ScalingEvent]:
        """
        Evaluate all policies and execute scaling if needed
        
        Returns:
            List of scaling events that occurred
        """
        events = []
        
        for policy in self.policies:
            direction = self.evaluate_policy(policy)
            
            if direction != ScalingDirection.NONE:
                metric_value = self.get_metric_average(policy.metric, policy.evaluation_periods)
                
                if self.execute_scaling(direction, policy, metric_value):
                    events.append(self.scaling_history[-1])
        
        return events
    
    def get_scaling_recommendations(self) -> Dict[str, Any]:
        """
        Get scaling recommendations based on current metrics
        
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'current_instances': self.current_instances,
            'recommendations': []
        }
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            avg_value = self.get_metric_average(policy.metric, policy.evaluation_periods)
            if avg_value is None:
                continue
            
            direction = self.evaluate_policy(policy)
            
            if direction != ScalingDirection.NONE:
                metric_name = policy.metric if isinstance(policy.metric, str) else policy.metric.value
                recommendations['recommendations'].append({
                    'policy': policy.name,
                    'metric': metric_name,
                    'current_value': avg_value,
                    'threshold': (
                        policy.scale_up_threshold if direction == ScalingDirection.UP
                        else policy.scale_down_threshold
                    ),
                    'action': direction.value,
                    'in_cooldown': self.is_in_cooldown(policy, direction)
                })
        
        return recommendations
    
    def get_scaling_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get scaling history
        
        Args:
            hours: Number of hours of history
        
        Returns:
            List of scaling events
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            {
                'timestamp': event.timestamp.isoformat(),
                'direction': event.direction.value,
                'policy': event.policy_name,
                'metric_value': event.metric_value,
                'threshold': event.threshold,
                'instances_before': event.instances_before,
                'instances_after': event.instances_after,
                'reason': event.reason
            }
            for event in self.scaling_history
            if event.timestamp >= cutoff_time
        ]


# Global auto-scaler instance
_autoscaler: Optional[AutoScaler] = None


def get_autoscaler() -> AutoScaler:
    """Get or create global auto-scaler instance"""
    global _autoscaler
    if _autoscaler is None:
        _autoscaler = AutoScaler()
        
        # Add default policies
        _autoscaler.add_policy(ScalingPolicy(
            name="cpu_based_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            min_instances=2,
            max_instances=10
        ))
        
        _autoscaler.add_policy(ScalingPolicy(
            name="concurrent_users_scaling",
            metric=ScalingMetric.CONCURRENT_USERS,
            scale_up_threshold=800.0,  # Scale up at 80% of 1000 user requirement
            scale_down_threshold=200.0,
            min_instances=2,
            max_instances=10
        ))
        
        logger.info("Default auto-scaling policies configured")
    
    return _autoscaler
