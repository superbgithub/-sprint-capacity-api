"""
Prometheus metrics for monitoring application performance and business metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from typing import Callable
from functools import wraps

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Business metrics - Sprint operations
sprints_created_total = Counter(
    'sprints_created_total',
    'Total number of sprints created'
)

sprints_updated_total = Counter(
    'sprints_updated_total',
    'Total number of sprints updated'
)

sprints_deleted_total = Counter(
    'sprints_deleted_total',
    'Total number of sprints deleted'
)

sprint_capacity_calculations_total = Counter(
    'sprint_capacity_calculations_total',
    'Total number of sprint capacity calculations performed'
)

team_members_added_total = Counter(
    'team_members_added_total',
    'Total number of team members added across all sprints'
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

validation_errors_total = Counter(
    'validation_errors_total',
    'Total number of validation errors',
    ['field']
)

# System metrics
active_sprints = Gauge(
    'active_sprints',
    'Number of currently active sprints'
)

database_connections = Gauge(
    'database_connections',
    'Number of active database connections'
)

# Application info
app_info = Info(
    'sprint_capacity_api',
    'Sprint Capacity Management API information'
)

# Health check metrics
system_cpu_percent = Gauge(
    'system_cpu_percent',
    'Current CPU usage percentage'
)

system_memory_percent = Gauge(
    'system_memory_percent',
    'Current memory usage percentage'
)

system_memory_used_mb = Gauge(
    'system_memory_used_mb',
    'Current memory used in megabytes'
)

system_memory_available_mb = Gauge(
    'system_memory_available_mb',
    'Current memory available in megabytes'
)

system_disk_percent = Gauge(
    'system_disk_percent',
    'Current disk usage percentage'
)

system_uptime_seconds = Gauge(
    'system_uptime_seconds',
    'Application uptime in seconds'
)

health_check_status = Gauge(
    'health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    ['check_type']
)


def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """
    Track request metrics.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_error(error_type: str, endpoint: str) -> None:
    """
    Track error occurrence.
    
    Args:
        error_type: Type of error (e.g., 'ValidationError', 'DatabaseError')
        endpoint: API endpoint where error occurred
    """
    errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def track_validation_error(field: str) -> None:
    """
    Track validation error for a specific field.
    
    Args:
        field: Field name that failed validation
    """
    validation_errors_total.labels(field=field).inc()


def metrics_endpoint() -> Response:
    """
    Generate Prometheus metrics response.
    
    Returns:
        Response with Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def timed(metric: Histogram):
    """
    Decorator to time function execution and record in histogram.
    
    Args:
        metric: Histogram metric to record timing
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def init_metrics_metadata(app_name: str = "Sprint Capacity Management", 
                         version: str = "1.0.0",
                         environment: str = "production") -> None:
    """
    Initialize application metadata in metrics.
    
    Args:
        app_name: Application name
        version: Application version
        environment: Deployment environment
    """
    app_info.info({
        'version': version,
        'api': app_name,
        'environment': environment
    })
