"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"


# Shared test client - reuse to prevent event loop issues
@pytest.fixture(scope="module")
def client():
    """Create a test client that's shared across tests in a module."""
    with TestClient(app) as test_client:
        yield test_client
