"""
Middleware for logging, metrics, and tracing.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable

from app.observability.logging import (
    get_logger,
    set_request_id,
    clear_context,
    log_with_context
)
from app.observability.metrics import (
    track_request_metrics,
    track_error,
    http_requests_in_progress
)
from app.observability.alerts import get_alert_manager

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add observability features:
    - Request ID generation and propagation
    - Structured logging
    - Metrics collection
    - Request/response timing
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability features."""
        
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID')
        request_id = set_request_id(request_id)
        
        # Extract endpoint pattern
        endpoint = self._get_endpoint_pattern(request)
        method = request.method
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Log request start
        log_with_context(
            logger,
            'info',
            f'Request started: {method} {endpoint}',
            method=method,
            endpoint=endpoint,
            path=str(request.url.path),
            client_ip=request.client.host if request.client else 'unknown',
            user_agent=request.headers.get('user-agent', 'unknown')
        )
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Track metrics
            track_request_metrics(method, endpoint, response.status_code, duration)
            
            # Record for alerting (5xx = error)
            alert_manager = get_alert_manager()
            is_error = response.status_code >= 500
            alert_manager.record_request(is_error, duration * 1000)
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            
            # Log response
            log_with_context(
                logger,
                'info',
                f'Request completed: {method} {endpoint}',
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time
            
            # Track error
            error_type = type(exc).__name__
            track_error(error_type, endpoint)
            track_request_metrics(method, endpoint, 500, duration)
            
            # Record for alerting (exception = error)
            alert_manager = get_alert_manager()
            alert_manager.record_request(is_error=True, duration_ms=duration * 1000)
            
            # Log error
            log_with_context(
                logger,
                'error',
                f'Request failed: {method} {endpoint}',
                method=method,
                endpoint=endpoint,
                error_type=error_type,
                error_message=str(exc),
                duration_ms=round(duration * 1000, 2)
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            
            # Clear context for this request
            clear_context()
    
    def _get_endpoint_pattern(self, request: Request) -> str:
        """
        Extract the endpoint pattern from the request.
        Replaces path parameters with placeholders for better metrics grouping.
        
        Args:
            request: FastAPI request object
        
        Returns:
            Endpoint pattern (e.g., "/v1/sprints/{sprint_id}")
        """
        # Try to get the route pattern from FastAPI
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        
        # Fallback to the actual path
        path = request.url.path
        
        # Simple pattern matching for common paths
        parts = path.split('/')
        normalized_parts = []
        
        for i, part in enumerate(parts):
            # If part looks like an ID (UUID or number), replace with placeholder
            if i > 0 and part and (
                len(part) == 36 or  # UUID length
                part.startswith('sprint-') or  # Sprint ID
                part.isdigit()  # Numeric ID
            ):
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        
        return '/'.join(normalized_parts)


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor slow requests and log warnings.
    """
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        """
        Initialize performance monitor.
        
        Args:
            app: ASGI application
            slow_request_threshold: Threshold in seconds for slow request warning
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Log warning for slow requests
        if duration > self.slow_request_threshold:
            endpoint = self._get_endpoint_pattern(request)
            log_with_context(
                logger,
                'warning',
                f'Slow request detected: {request.method} {endpoint}',
                method=request.method,
                endpoint=endpoint,
                duration_ms=round(duration * 1000, 2),
                threshold_ms=self.slow_request_threshold * 1000
            )
        
        return response
    
    def _get_endpoint_pattern(self, request: Request) -> str:
        """Extract endpoint pattern (same as ObservabilityMiddleware)."""
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        return request.url.path
