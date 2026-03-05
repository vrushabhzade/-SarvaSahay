"""
Load Balancer Configuration Module
Defines load balancing strategies and health check configurations
Requirements: 9.2, 9.3
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class HealthCheckConfig(BaseModel):
    """Health check configuration for load balancer"""
    
    enabled: bool = Field(default=True, description="Enable health checks")
    endpoint: str = Field(default="/api/v1/health", description="Health check endpoint")
    interval_seconds: int = Field(default=30, description="Health check interval")
    timeout_seconds: int = Field(default=5, description="Health check timeout")
    healthy_threshold: int = Field(default=2, description="Consecutive successes to mark healthy")
    unhealthy_threshold: int = Field(default=3, description="Consecutive failures to mark unhealthy")
    
    class Config:
        use_enum_values = True


class ServerInstance(BaseModel):
    """Server instance configuration"""
    
    host: str = Field(..., description="Server hostname or IP")
    port: int = Field(..., description="Server port")
    weight: int = Field(default=1, description="Weight for weighted load balancing")
    max_connections: int = Field(default=1000, description="Maximum concurrent connections")
    is_healthy: bool = Field(default=True, description="Current health status")
    current_connections: int = Field(default=0, description="Current active connections")
    
    def get_url(self) -> str:
        """Get full server URL"""
        return f"http://{self.host}:{self.port}"


class LoadBalancerConfig(BaseModel):
    """Load balancer configuration"""
    
    strategy: LoadBalancingStrategy = Field(
        default=LoadBalancingStrategy.ROUND_ROBIN,
        description="Load balancing strategy"
    )
    servers: List[ServerInstance] = Field(
        default_factory=list,
        description="Backend server instances"
    )
    health_check: HealthCheckConfig = Field(
        default_factory=HealthCheckConfig,
        description="Health check configuration"
    )
    sticky_sessions: bool = Field(
        default=False,
        description="Enable sticky sessions (session affinity)"
    )
    session_cookie_name: str = Field(
        default="SARVASAHAY_SESSION",
        description="Session cookie name for sticky sessions"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests"
    )
    retry_timeout_seconds: int = Field(
        default=30,
        description="Timeout for retry attempts"
    )
    
    class Config:
        use_enum_values = True
    
    def add_server(self, host: str, port: int, weight: int = 1):
        """Add server instance to pool"""
        server = ServerInstance(host=host, port=port, weight=weight)
        self.servers.append(server)
        logger.info(f"Added server to pool: {server.get_url()}")
    
    def remove_server(self, host: str, port: int):
        """Remove server instance from pool"""
        self.servers = [
            s for s in self.servers 
            if not (s.host == host and s.port == port)
        ]
        logger.info(f"Removed server from pool: http://{host}:{port}")
    
    def get_healthy_servers(self) -> List[ServerInstance]:
        """Get list of healthy servers"""
        return [s for s in self.servers if s.is_healthy]
    
    def mark_server_unhealthy(self, host: str, port: int):
        """Mark server as unhealthy"""
        for server in self.servers:
            if server.host == host and server.port == port:
                server.is_healthy = False
                logger.warning(f"Server marked unhealthy: {server.get_url()}")
                break
    
    def mark_server_healthy(self, host: str, port: int):
        """Mark server as healthy"""
        for server in self.servers:
            if server.host == host and server.port == port:
                server.is_healthy = True
                logger.info(f"Server marked healthy: {server.get_url()}")
                break
    
    def to_nginx_config(self) -> str:
        """
        Generate Nginx load balancer configuration
        
        Returns:
            Nginx configuration string
        """
        strategy_map = {
            LoadBalancingStrategy.ROUND_ROBIN: "",
            LoadBalancingStrategy.LEAST_CONNECTIONS: "least_conn;",
            LoadBalancingStrategy.IP_HASH: "ip_hash;",
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: ""
        }
        
        config = f"""
# SarvaSahay Platform Load Balancer Configuration
# Generated automatically - do not edit manually

upstream sarvasahay_backend {{
    {strategy_map.get(self.strategy, "")}
    
    # Backend servers
"""
        
        for server in self.servers:
            weight_str = f"weight={server.weight}" if server.weight > 1 else ""
            max_fails = self.health_check.unhealthy_threshold
            fail_timeout = f"{self.health_check.interval_seconds}s"
            
            config += f"    server {server.host}:{server.port} {weight_str} max_fails={max_fails} fail_timeout={fail_timeout};\n"
        
        config += "}\n\n"
        
        config += """
server {
    listen 80;
    server_name sarvasahay.gov.in;
    
    # Request timeout
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    
    # Buffer settings
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    
    # Headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
"""
        
        if self.sticky_sessions:
            config += f"    # Sticky sessions\n"
            config += f"    ip_hash;\n\n"
        
        config += """    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://sarvasahay_backend;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://sarvasahay_backend;
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
    }
    
    # Metrics endpoint (restricted)
    location /api/v1/metrics {
        # Restrict to internal IPs only
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://sarvasahay_backend;
    }
}
"""
        
        return config
    
    def to_haproxy_config(self) -> str:
        """
        Generate HAProxy load balancer configuration
        
        Returns:
            HAProxy configuration string
        """
        config = """
# SarvaSahay Platform HAProxy Configuration
# Generated automatically - do not edit manually

global
    log /dev/log local0
    log /dev/log local1 notice
    maxconn 4096
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    retries 3

frontend sarvasahay_frontend
    bind *:80
    default_backend sarvasahay_backend
    
    # Request rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 100 }

backend sarvasahay_backend
"""
        
        strategy_map = {
            LoadBalancingStrategy.ROUND_ROBIN: "roundrobin",
            LoadBalancingStrategy.LEAST_CONNECTIONS: "leastconn",
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: "roundrobin"
        }
        
        config += f"    balance {strategy_map.get(self.strategy, 'roundrobin')}\n"
        
        if self.health_check.enabled:
            config += f"    option httpchk GET {self.health_check.endpoint}\n"
            config += f"    http-check expect status 200\n"
        
        config += "\n"
        
        for i, server in enumerate(self.servers):
            check_str = f"check inter {self.health_check.interval_seconds}s" if self.health_check.enabled else ""
            weight_str = f"weight {server.weight}" if server.weight > 1 else ""
            
            config += f"    server server{i+1} {server.host}:{server.port} {weight_str} {check_str} maxconn {server.max_connections}\n"
        
        return config


def create_default_load_balancer_config() -> LoadBalancerConfig:
    """Create default load balancer configuration"""
    config = LoadBalancerConfig(
        strategy=LoadBalancingStrategy.ROUND_ROBIN,
        health_check=HealthCheckConfig(
            enabled=True,
            endpoint="/api/v1/health",
            interval_seconds=30,
            timeout_seconds=5
        )
    )
    
    # Add default servers (would be configured via environment)
    config.add_server("localhost", 8000, weight=1)
    
    return config
