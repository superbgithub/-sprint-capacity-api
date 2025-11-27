"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import os
from fastapi.testclient import TestClient
from app.main import app


# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
SYNC_TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sprint_capacity_test"


# Set environment variable for tests
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def setup_test_database():
    """
    Initialize test database schema before database-dependent tests.
    Use this fixture explicitly in tests that need database access.
    """
    from sqlalchemy import create_engine
    from app.config.database import Base
    
    # Import all models to ensure they're registered with Base.metadata
    import app.models.db_models  # noqa: F401
    
    # Use synchronous engine for schema creation
    engine = create_engine(SYNC_TEST_DATABASE_URL, echo=True)
    
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# Shared test client - reuse to prevent event loop issues
@pytest.fixture(scope="module")
def client(setup_test_database):
    """
    Create a test client that's shared across tests in a module.
    Depends on setup_test_database to ensure schema is ready.
    """
    with TestClient(app) as test_client:
        yield test_client
