"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import os
from fastapi.testclient import TestClient


# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"


# Set environment variable for tests BEFORE any imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Now import the app after setting the DATABASE_URL
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """
    Create a test client for API testing.
    Note: Database schema should be initialized BEFORE running pytest
    using scripts/init_test_db.py in CI/CD or locally.
    """
    with TestClient(app) as test_client:
        yield test_client
