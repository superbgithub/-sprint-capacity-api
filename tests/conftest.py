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
    
    Important: We recreate the database engine for each test module to ensure
    it uses the correct event loop context for TestClient.
    """
    # Import database module to access engine
    from app.config import database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    # Dispose of the existing engine that was created at import time
    import asyncio
    try:
        asyncio.run(database.engine.dispose())
    except RuntimeError:
        # Already in event loop context, that's fine
        pass
    
    # Create a new engine in the current event loop context
    new_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=False,
        pool_recycle=3600,
    )
    
    # Replace the global engine with our new one
    database.engine = new_engine
    database.AsyncSessionLocal = async_sessionmaker(
        new_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Now create the test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up: dispose of the engine after tests
    try:
        asyncio.run(new_engine.dispose())
    except RuntimeError:
        pass
