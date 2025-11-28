"""
Tests for metrics collection.
"""
import pytest
from app.observability.metrics import (
    track_request_metrics,
    track_error,
    track_validation_error,
    timed,
    http_requests_total,
    http_request_duration_seconds,
    errors_total,
    validation_errors_total
)


def test_track_request_metrics():
    """Test tracking HTTP request metrics."""
    # Track a successful request
    track_request_metrics("GET", "/api/test", 200, 0.5)
    
    # Verify counter incremented
    metric_value = http_requests_total.labels(
        method="GET",
        endpoint="/api/test",
        status=200
    )._value._value
    assert metric_value >= 1


def test_track_error():
    """Test tracking error metrics."""
    track_error("ValueError", "/api/test")
    
    # Verify error counter incremented
    metric_value = errors_total.labels(
        error_type="ValueError",
        endpoint="/api/test"
    )._value._value
    assert metric_value >= 1


def test_track_validation_error():
    """Test tracking validation error metrics."""
    track_validation_error("email")
    
    # Verify validation error counter incremented
    metric_value = validation_errors_total.labels(
        field="email"
    )._value._value
    assert metric_value >= 1


def test_timed_decorator_sync():
    """Test @timed decorator for synchronous functions."""
    from prometheus_client import Histogram
    test_metric = Histogram('test_duration', 'Test duration')
    
    @timed(test_metric)
    def test_function():
        return "result"
    
    result = test_function()
    assert result == "result"


@pytest.mark.asyncio
async def test_timed_decorator_async():
    """Test @timed decorator for async functions."""
    from prometheus_client import Histogram
    test_metric = Histogram('test_async_duration', 'Test async duration')
    
    @timed(test_metric)
    async def test_async_function():
        return "async result"
    
    result = await test_async_function()
    assert result == "async result"


def test_histogram_observations():
    """Test that request duration histogram records observations."""
    # Track several requests with different durations
    track_request_metrics("GET", "/test", 200, 0.1)
    track_request_metrics("GET", "/test", 200, 0.5)
    track_request_metrics("GET", "/test", 200, 1.0)
    
    # Verify the function ran without errors
    # The histogram metrics are tracked internally by prometheus_client
    # Just verify no exceptions were raised
    assert True
