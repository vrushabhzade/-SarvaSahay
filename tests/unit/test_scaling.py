"""
Unit Tests for Horizontal Scaling Capabilities
Tests stateless service design, load balancing, and auto-scaling
Requirements: 9.2, 9.3
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from shared.scaling.stateless import (
    StatelessService,
    SessionManager,
    RequestDeduplicator,
    get_session_manager
)
from shared.scaling.load_balancer import (
    LoadBalancerConfig,
    HealthCheckConfig,
    ServerInstance,
    LoadBalancingStrategy
)
from shared.scaling.autoscaler import (
    AutoScaler,
    ScalingPolicy,
    ScalingMetric,
    ScalingDirection,
    get_autoscaler
)


class TestStatelessService:
    """Test stateless service design"""
    
    def test_stateless_service_initialization(self):
        """Test stateless service initializes correctly"""
        class TestService(StatelessService):
            def process_request(self, request_data):
                return {"result": "success"}
        
        service = TestService("test_service")
        assert service.service_name == "test_service"
    
    def test_generate_request_id(self):
        """Test deterministic request ID generation"""
        class TestService(StatelessService):
            def process_request(self, request_data):
                return {}
        
        service = TestService("test")
        
        request1 = {"user_id": "123", "action": "test"}
        request2 = {"user_id": "123", "action": "test"}
        request3 = {"user_id": "456", "action": "test"}
        
        # Same request should generate same ID
        id1 = service.generate_request_id(request1)
        id2 = service.generate_request_id(request2)
        assert id1 == id2
        
        # Different request should generate different ID
        id3 = service.generate_request_id(request3)
        assert id1 != id3
    
    def test_is_idempotent_operation(self):
        """Test idempotent operation checking"""
        class TestService(StatelessService):
            def process_request(self, request_data):
                return {}
        
        service = TestService("test")
        
        assert service.is_idempotent_operation("GET")
        assert service.is_idempotent_operation("PUT")
        assert service.is_idempotent_operation("DELETE")
        assert not service.is_idempotent_operation("POST")


class TestSessionManager:
    """Test session management for stateless services"""
    
    def test_session_manager_initialization(self):
        """Test session manager initializes correctly"""
        manager = SessionManager()
        assert manager.local_cache is not None
    
    def test_create_session(self):
        """Test session creation"""
        manager = SessionManager()
        
        session_data = {"user_id": "123", "role": "user"}
        session_id = manager.create_session("123", session_data)
        
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_get_session(self):
        """Test session retrieval"""
        manager = SessionManager()
        
        session_data = {"user_id": "123", "role": "user"}
        session_id = manager.create_session("123", session_data)
        
        retrieved_data = manager.get_session(session_id)
        assert retrieved_data == session_data
    
    def test_update_session(self):
        """Test session update"""
        manager = SessionManager()
        
        session_data = {"user_id": "123", "role": "user"}
        session_id = manager.create_session("123", session_data)
        
        updated_data = {"user_id": "123", "role": "admin"}
        manager.update_session(session_id, updated_data)
        
        retrieved_data = manager.get_session(session_id)
        assert retrieved_data["role"] == "admin"
    
    def test_delete_session(self):
        """Test session deletion"""
        manager = SessionManager()
        
        session_data = {"user_id": "123", "role": "user"}
        session_id = manager.create_session("123", session_data)
        
        manager.delete_session(session_id)
        
        retrieved_data = manager.get_session(session_id)
        assert retrieved_data is None


class TestRequestDeduplicator:
    """Test request deduplication"""
    
    def test_request_deduplicator_initialization(self):
        """Test deduplicator initializes correctly"""
        dedup = RequestDeduplicator()
        assert dedup.processed_requests is not None
    
    def test_is_duplicate(self):
        """Test duplicate detection"""
        dedup = RequestDeduplicator()
        
        request_id = "test_request_123"
        
        # Should not be duplicate initially
        assert not dedup.is_duplicate(request_id)
        
        # Mark as processed
        dedup.mark_processed(request_id, {"result": "success"})
        
        # Should now be duplicate
        assert dedup.is_duplicate(request_id)
    
    def test_get_cached_result(self):
        """Test cached result retrieval"""
        dedup = RequestDeduplicator()
        
        request_id = "test_request_123"
        result = {"result": "success", "data": "test"}
        
        dedup.mark_processed(request_id, result)
        
        cached_result = dedup.get_cached_result(request_id)
        assert cached_result == result


class TestLoadBalancerConfig:
    """Test load balancer configuration"""
    
    def test_load_balancer_config_initialization(self):
        """Test load balancer config initializes correctly"""
        config = LoadBalancerConfig()
        assert config.strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert config.servers == []
    
    def test_add_server(self):
        """Test adding server to pool"""
        config = LoadBalancerConfig()
        
        config.add_server("localhost", 8000, weight=1)
        assert len(config.servers) == 1
        assert config.servers[0].host == "localhost"
        assert config.servers[0].port == 8000
    
    def test_remove_server(self):
        """Test removing server from pool"""
        config = LoadBalancerConfig()
        
        config.add_server("localhost", 8000)
        config.add_server("localhost", 8001)
        
        config.remove_server("localhost", 8000)
        assert len(config.servers) == 1
        assert config.servers[0].port == 8001
    
    def test_get_healthy_servers(self):
        """Test getting healthy servers"""
        config = LoadBalancerConfig()
        
        config.add_server("localhost", 8000)
        config.add_server("localhost", 8001)
        
        # Mark one server unhealthy
        config.mark_server_unhealthy("localhost", 8000)
        
        healthy_servers = config.get_healthy_servers()
        assert len(healthy_servers) == 1
        assert healthy_servers[0].port == 8001
    
    def test_health_check_config(self):
        """Test health check configuration"""
        health_check = HealthCheckConfig(
            enabled=True,
            endpoint="/health",
            interval_seconds=30,
            timeout_seconds=5
        )
        
        assert health_check.enabled
        assert health_check.endpoint == "/health"
        assert health_check.interval_seconds == 30
    
    def test_server_instance(self):
        """Test server instance configuration"""
        server = ServerInstance(
            host="localhost",
            port=8000,
            weight=2,
            max_connections=1000
        )
        
        assert server.get_url() == "http://localhost:8000"
        assert server.weight == 2
        assert server.is_healthy
    
    def test_nginx_config_generation(self):
        """Test Nginx configuration generation"""
        config = LoadBalancerConfig(
            strategy=LoadBalancingStrategy.ROUND_ROBIN
        )
        config.add_server("localhost", 8000)
        config.add_server("localhost", 8001)
        
        nginx_config = config.to_nginx_config()
        
        assert "upstream sarvasahay_backend" in nginx_config
        assert "localhost:8000" in nginx_config
        assert "localhost:8001" in nginx_config
    
    def test_haproxy_config_generation(self):
        """Test HAProxy configuration generation"""
        config = LoadBalancerConfig(
            strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        config.add_server("localhost", 8000)
        
        haproxy_config = config.to_haproxy_config()
        
        assert "backend sarvasahay_backend" in haproxy_config
        assert "balance leastconn" in haproxy_config
        assert "localhost:8000" in haproxy_config


class TestAutoScaler:
    """Test auto-scaling functionality"""
    
    def test_autoscaler_initialization(self):
        """Test auto-scaler initializes correctly"""
        scaler = AutoScaler()
        assert scaler.current_instances == 2
        assert scaler.policies == []
    
    def test_add_policy(self):
        """Test adding scaling policy"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0
        )
        
        scaler.add_policy(policy)
        assert len(scaler.policies) == 1
    
    def test_record_metric(self):
        """Test recording metrics"""
        scaler = AutoScaler()
        
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 50.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 60.0)
        
        assert len(scaler.metric_history[ScalingMetric.CPU_UTILIZATION.value]) == 2
    
    def test_get_metric_average(self):
        """Test metric average calculation"""
        scaler = AutoScaler()
        
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 50.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 60.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 70.0)
        
        avg = scaler.get_metric_average(ScalingMetric.CPU_UTILIZATION, periods=2)
        assert avg == 65.0  # (60 + 70) / 2
    
    def test_evaluate_policy_scale_up(self):
        """Test policy evaluation for scale up"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            min_instances=2,
            max_instances=10
        )
        
        scaler.add_policy(policy)
        
        # Record high CPU usage
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 75.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 80.0)
        
        direction = scaler.evaluate_policy(policy)
        assert direction == ScalingDirection.UP
    
    def test_evaluate_policy_scale_down(self):
        """Test policy evaluation for scale down"""
        scaler = AutoScaler()
        scaler.current_instances = 5  # Start with more instances
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            min_instances=2,
            max_instances=10
        )
        
        scaler.add_policy(policy)
        
        # Record low CPU usage
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 20.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 25.0)
        
        direction = scaler.evaluate_policy(policy)
        assert direction == ScalingDirection.DOWN
    
    def test_execute_scaling_up(self):
        """Test executing scale up"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            scale_up_increment=2
        )
        
        initial_instances = scaler.current_instances
        
        scaler.execute_scaling(ScalingDirection.UP, policy, 75.0)
        
        assert scaler.current_instances == initial_instances + 2
        assert len(scaler.scaling_history) == 1
    
    def test_execute_scaling_down(self):
        """Test executing scale down"""
        scaler = AutoScaler()
        scaler.current_instances = 5
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            scale_down_decrement=1
        )
        
        scaler.execute_scaling(ScalingDirection.DOWN, policy, 25.0)
        
        assert scaler.current_instances == 4
        assert len(scaler.scaling_history) == 1
    
    def test_min_max_instance_limits(self):
        """Test min/max instance limits are respected"""
        scaler = AutoScaler()
        scaler.current_instances = 2
        
        policy = ScalingPolicy(
            name="test",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            min_instances=2,
            max_instances=5,
            scale_down_decrement=1
        )
        
        # Try to scale down below minimum
        scaler.execute_scaling(ScalingDirection.DOWN, policy, 20.0)
        assert scaler.current_instances == 2  # Should stay at minimum
        
        # Scale up to maximum
        scaler.current_instances = 5
        scaler.execute_scaling(ScalingDirection.UP, policy, 80.0)
        assert scaler.current_instances == 5  # Should stay at maximum
    
    def test_cooldown_period(self):
        """Test cooldown period prevents rapid scaling"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            scale_up_cooldown_seconds=300
        )
        
        # Execute first scaling
        scaler.execute_scaling(ScalingDirection.UP, policy, 75.0)
        
        # Should be in cooldown
        assert scaler.is_in_cooldown(policy, ScalingDirection.UP)
    
    def test_get_scaling_recommendations(self):
        """Test getting scaling recommendations"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="cpu_scaling",
            metric=ScalingMetric.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0
        )
        
        scaler.add_policy(policy)
        
        # Record high CPU
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 75.0)
        scaler.record_metric(ScalingMetric.CPU_UTILIZATION, 80.0)
        
        recommendations = scaler.get_scaling_recommendations()
        
        assert 'current_instances' in recommendations
        assert 'recommendations' in recommendations
    
    def test_concurrent_users_scaling(self):
        """Test scaling based on concurrent users (Requirement 9.2: 1000+ users)"""
        scaler = AutoScaler()
        
        policy = ScalingPolicy(
            name="user_scaling",
            metric=ScalingMetric.CONCURRENT_USERS,
            scale_up_threshold=800.0,  # 80% of 1000 user requirement
            scale_down_threshold=200.0,
            min_instances=2,
            max_instances=10
        )
        
        scaler.add_policy(policy)
        
        # Simulate high user load
        scaler.record_metric(ScalingMetric.CONCURRENT_USERS, 850.0)
        scaler.record_metric(ScalingMetric.CONCURRENT_USERS, 900.0)
        
        direction = scaler.evaluate_policy(policy)
        assert direction == ScalingDirection.UP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
