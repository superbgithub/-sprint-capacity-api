"""
Pytest fixtures and configuration for acceptance tests.
"""
import pytest
import os
from fastapi.testclient import TestClient

# Use test database from environment or default
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
)

# Set environment variable for tests BEFORE any imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Now import the app after setting the DATABASE_URL
from app.main import app  # noqa: E402


@pytest.fixture(scope="function")
def test_db():
    """
    Database fixture - assumes schema is already initialized.
    In CI/CD, scripts/init_test_db.py runs before tests.
    Locally, run: python scripts/init_test_db.py
    
    Note: Database cleanup is handled by individual tests or test client teardown
    to ensure proper isolation between acceptance test scenarios.
    """
    # Schema is pre-initialized, no need to create/drop here
    yield


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create test client for acceptance tests."""
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(scope="function")
def context():
    """Shared context dictionary for storing test data between BDD steps."""
    return {}
