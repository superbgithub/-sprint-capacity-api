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


# Set environment variable for tests BEFORE any imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Initialize test database schema before any tests run.
    This runs automatically for all test sessions.
    """
    from sqlalchemy import create_engine
    from app.config.database import Base
    
    # Import all models to ensure they're registered with Base.metadata
    import app.models.db_models  # noqa: F401
    
    print("\n" + "="*80)
    print("SETTING UP TEST DATABASE")
    print("="*80)
    
    # Use synchronous engine for schema creation
    engine = create_engine(SYNC_TEST_DATABASE_URL, echo=True)
    
    # Drop all tables first to ensure clean state
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("="*80)
    print("TEST DATABASE SETUP COMPLETE")
    print("="*80 + "\n")
    
    yield
    
    # Cleanup after all tests
    print("\nCleaning up test database...")
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# Shared test client - reuse to prevent event loop issues
@pytest.fixture(scope="module")
def client():
    """
    Create a test client that's shared across tests in a module.
    The database setup happens automatically via autouse fixture.
    """
    with TestClient(app) as test_client:
        yield test_client
