"""
Security Tests Configuration
----------------------------
Fixtures and configuration for security tests.
"""
import pytest
import os


@pytest.fixture(scope="session")
def security_test_environment():
    """Set up security test environment"""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
    os.environ["ENVIRONMENT"] = "test"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def security_headers():
    """Expected security headers configuration"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
