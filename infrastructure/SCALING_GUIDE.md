# SarvaSahay Platform Scaling Guide

## Overview

This guide explains the performance monitoring and horizontal scaling capabilities implemented for the SarvaSahay Platform to meet requirements 9.1, 9.2, 9.3, and 9.5.

## Performance Monitoring (Requirement 9.1, 9.5)

### Metrics Collection

The platform uses Prometheus for metrics collection with the following key metrics:

- **Request Metrics**: Total requests, duration, concurrent requests
- **Eligibility Engine**: Evaluation time (<5 seconds requirement), schemes matched
- **Document Processing**: Processing time, OCR accuracy
- **Application Submission**: Submission time, success rate
- **Government API**: Request duration, success/failure rates
- **Cache Performance**: Hit/miss ratios
- **System Resources**: CPU, memory, disk usage

### API Endpoints

- `GET /api/v1/metrics` - Prometheus metrics endpoint
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/resources` - System resource metrics
- `GET /api/v1/alerts` - Active alerts
- `GET /api/v1/dashboard` - Comprehensive dashboard data

### Resource Monitoring

Automatic background monitoring tracks:
- CPU utilization (alert at >80%)
- Memory usage (alert at >85%)
- Disk space (alert at >90%)
- Network I/O
- Process-specific metrics

### Alerting

Configurable alerts for:
- Performance thresholds (5-second eligibility requirement)
- Resource usage limits
- Error rates
- Uptime requirements (99.5%)

## Horizontal Scaling (Requirement 9.2, 9.3)

### Stateless Service Design

All services are designed to be stateless:
- No local state storage
- Session management via Redis
- Idempotent operations
- Request deduplication

### Load Balancing

Multiple load balancing strategies supported:
- Round Robin (default)
- Least Connections
- Weighted Round Robin
- IP Hash (sticky sessions)

Configuration files provided for:
- Nginx Ingress (Kubernetes)
- HAProxy

### Auto-Scaling

Automatic scaling based on metrics:
- CPU utilization (scale up at 70%, down at 30%)
- Concurrent users (scale up at 800/1000 users)
- Memory usage
- Request count
- Response time

**Scaling Limits:**
- Minimum instances: 2 (high availability)
- Maximum instances: 10
- Cooldown periods prevent rapid scaling

### Kubernetes Deployment

Horizontal Pod Autoscaler (HPA) configuration:
- Scales based on CPU and memory
- Min replicas: 2
- Max replicas: 10
- Pod anti-affinity for distribution across nodes

## Usage

### Starting Monitoring

```python
from shared.monitoring import get_resource_monitor

monitor = get_resource_monitor()
monitor.start_monitoring()
```

### Tracking Performance

```python
from shared.monitoring import get_metrics_collector

collector = get_metrics_collector()

# Track eligibility evaluation
collector.track_eligibility_evaluation(
    duration=2.5,
    schemes_matched=15,
    status="success"
)
```

### Configuring Auto-Scaling

```python
from shared.scaling import get_autoscaler, ScalingPolicy, ScalingMetric

scaler = get_autoscaler()

# Add custom policy
policy = ScalingPolicy(
    name="custom_scaling",
    metric=ScalingMetric.CONCURRENT_USERS,
    scale_up_threshold=800.0,
    scale_down_threshold=200.0,
    min_instances=2,
    max_instances=10
)

scaler.add_policy(policy)
```

### Deploying to Kubernetes

```bash
# Apply deployment configuration
kubectl apply -f infrastructure/kubernetes/deployment.yaml

# Apply ingress configuration
kubectl apply -f infrastructure/kubernetes/nginx-ingress.yaml

# Check HPA status
kubectl get hpa sarvasahay-api-hpa

# View metrics
kubectl top pods
```

## Performance Requirements

The system is designed to meet these requirements:

- **Eligibility Evaluation**: <5 seconds for 30+ schemes (Requirement 9.1)
- **Concurrent Users**: Support 1000+ concurrent users (Requirement 9.2)
- **Uptime**: 99.5% during business hours (Requirement 9.5)
- **Scalability**: Horizontal scaling without downtime (Requirement 9.3)

## Monitoring Dashboard

Access the monitoring dashboard at:
- `/api/v1/dashboard` - JSON dashboard data
- `/api/v1/metrics` - Prometheus metrics (for Grafana)

## Troubleshooting

### High Response Times

1. Check `/api/v1/alerts` for performance alerts
2. Review `/api/v1/resources` for resource constraints
3. Check auto-scaler recommendations: `/api/v1/dashboard`

### Scaling Issues

1. Verify HPA status: `kubectl get hpa`
2. Check pod status: `kubectl get pods`
3. Review scaling history in dashboard

### Resource Alerts

1. Check active alerts: `GET /api/v1/alerts`
2. Review resource history: `GET /api/v1/resources/history?hours=24`
3. Adjust alert thresholds if needed

## Configuration

### Environment Variables

```bash
# Performance settings
MAX_CONCURRENT_USERS=1000
MAX_SIMULTANEOUS_EVALUATIONS=10000
UPTIME_REQUIREMENT=0.995

# Monitoring
PERF_RATE_LIMIT_PER_MINUTE=60
PERF_RATE_LIMIT_BURST=10
```

### Kubernetes Resources

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

## Best Practices

1. **Always use stateless services** - Store state in Redis/Database
2. **Enable health checks** - Configure liveness and readiness probes
3. **Monitor metrics** - Set up Prometheus and Grafana
4. **Configure alerts** - Set appropriate thresholds
5. **Test scaling** - Verify auto-scaling works under load
6. **Use pod anti-affinity** - Distribute pods across nodes
7. **Set resource limits** - Prevent resource exhaustion

## References

- Prometheus Documentation: https://prometheus.io/docs/
- Kubernetes HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- Nginx Ingress: https://kubernetes.github.io/ingress-nginx/
