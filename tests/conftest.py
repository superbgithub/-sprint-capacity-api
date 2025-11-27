"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from app.main import app
from app.config.database import Base


# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
SYNC_TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sprint_capacity_test"


# Set environment variable for tests
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize test database schema before all tests."""
    # Use synchronous engine for schema creation
    engine = create_engine(SYNC_TEST_DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# Shared test client - reuse to prevent event loop issues
@pytest.fixture(scope="module")
def client():
    """Create a test client that's shared across tests in a module."""
    with TestClient(app) as test_client:
        yield test_client
