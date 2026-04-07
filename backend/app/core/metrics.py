"""
Prometheus metrics collection
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
from typing import Callable


# Define metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests',
    'Number of active requests'
)

AI_QUERY_COUNT = Counter(
    'ai_queries_total',
    'Total AI queries',
    ['query_type']
)

AI_QUERY_DURATION = Histogram(
    'ai_query_duration_seconds',
    'AI query duration in seconds',
    ['query_type']
)

K8S_ACTION_COUNT = Counter(
    'k8s_actions_total',
    'Total Kubernetes actions',
    ['action_type', 'status']
)

INCIDENT_COUNT = Gauge(
    'active_incidents',
    'Number of active incidents',
    ['severity']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()


def get_metrics():
    """Get Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions to track custom metrics
def track_ai_query(query_type: str, duration: float):
    """Track AI query metrics"""
    AI_QUERY_COUNT.labels(query_type=query_type).inc()
    AI_QUERY_DURATION.labels(query_type=query_type).observe(duration)


def track_k8s_action(action_type: str, success: bool):
    """Track Kubernetes action metrics"""
    status = "success" if success else "failure"
    K8S_ACTION_COUNT.labels(action_type=action_type, status=status).inc()


def update_incident_count(severity: str, count: int):
    """Update incident count gauge"""
    INCIDENT_COUNT.labels(severity=severity).set(count)


# Alias for backwards compatibility
metrics_middleware = PrometheusMiddleware
