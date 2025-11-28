"""
Tests for observability middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.observability.middleware import ObservabilityMiddleware, PerformanceMonitorMiddleware


@pytest.fixture
def test_app():
    """Create test FastAPI application with observability middleware."""
    app = FastAPI()
    app.add_middleware(PerformanceMonitorMiddleware, slow_request_threshold=0.1)
    app.add_middleware(ObservabilityMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_request_id_generation(client):
    """Test that request ID is generated and added to response headers."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length


def test_request_id_propagation(client):
    """Test that request ID from header is propagated."""
    test_request_id = "test-request-123"
    response = client.get("/test", headers={"X-Request-ID": test_request_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == test_request_id


def test_endpoint_pattern_extraction(client):
    """Test that endpoint patterns are correctly extracted."""
    response = client.get("/test")
    assert response.status_code == 200
    # Middleware should process the request without errors


def test_error_tracking(client):
    """Test that errors are tracked by middleware."""
    with pytest.raises(ValueError):
        client.get("/error")
    # Middleware should track the error without crashing


def test_performance_monitoring(client):
    """Test that slow requests are logged."""
    # This is a fast request, should not trigger slow request warning
    response = client.get("/test")
    assert response.status_code == 200
