#!/usr/bin/env python3
"""
Initialize test database schema.
Run this before pytest to create all tables.
"""
import asyncio
import os
import sys


async def init_test_db():
    """Create database schema for testing."""
    # Add parent directory to path so we can import app modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.config.database import Base
    import app.models.db_models  # noqa: F401
    
    # Use test database URL
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sprint_capacity_test"
    )
    
    print("="*80)
    print("INITIALIZING TEST DATABASE SCHEMA")
    print(f"Database: {DATABASE_URL}")
    print("="*80)
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Drop existing tables
            print("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            print("Creating all tables from models...")
            await conn.run_sync(Base.metadata.create_all)
            
            print("✓ Tables created successfully")
            print("="*80)
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_test_db())
