"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import os
from fastapi.testclient import TestClient


# Use a test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
SYNC_TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sprint_capacity_test"


# Set environment variable for tests BEFORE any imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Now import the app after setting the DATABASE_URL
from app.main import app  # noqa: E402


def pytest_configure(config):
    """
    This runs once when pytest starts, BEFORE any test collection.
    Only run database setup if we're testing modules that need it.
    """
    # Get the test paths being run
    test_paths = config.args if config.args else []
    
    # Check if we're running database-dependent tests
    needs_database = any(
        'contract' in str(path) or 
        'component' in str(path) or 
        'functional' in str(path) or 
        'resiliency' in str(path)
        for path in test_paths
    )
    
    # If no specific paths given, check if contract/component/functional/resiliency dirs exist
    if not test_paths or needs_database:
        # Import database utilities
        from sqlalchemy import create_engine
        from app.config.database import Base
        import app.models.db_models  # noqa: F401
        
        print("\n" + "="*80)
        print("INITIALIZING TEST DATABASE SCHEMA")
        print("="*80)
        
        try:
            # Use synchronous engine for schema creation
            engine = create_engine(SYNC_TEST_DATABASE_URL, echo=False)
            
            # Drop and recreate all tables
            print("Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
            
            print("Creating all tables from models...")
            Base.metadata.create_all(bind=engine)
            
            print("Tables created successfully")
            print("="*80 + "\n")
            
            engine.dispose()
        except Exception as e:
            print(f"Note: Could not initialize test database: {e}")
            print("This is expected if running only unit tests without database.\n")


# Shared test client - reuse to prevent event loop issues
@pytest.fixture(scope="module")
def client():
    """
    Create a test client that's shared across tests in a module.
    For database-dependent tests, the schema is created by pytest_configure.
    """
    with TestClient(app) as test_client:
        yield test_client
