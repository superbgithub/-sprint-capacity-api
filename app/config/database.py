"""
Database configuration and connection management.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.observability.logging import get_logger
from app.utils.circuit_breaker import database_breaker, CircuitBreakerError, CircuitState
from app.utils.retry import retry_with_backoff

logger = get_logger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sprint_user:sprint_password@localhost:5432/sprint_capacity"
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for ORM models
Base = declarative_base()


async def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        CircuitBreakerError: If database circuit breaker is open
    """
    # Check circuit breaker before creating session
    if database_breaker.state == CircuitState.OPEN:
        logger.error("Database circuit breaker is OPEN - service unavailable")
        raise CircuitBreakerError("Database circuit breaker is OPEN")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
            # Mark success for circuit breaker
            database_breaker._on_success()
        except Exception as e:
            await session.rollback()
            # Mark failure for circuit breaker
            database_breaker._on_failure()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@retry_with_backoff(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0,
    operation_name="database_health_check"
)
async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        from sqlalchemy import text
        
        async def _check():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        
        await database_breaker.call_async(_check)
        return True
    except CircuitBreakerError:
        logger.warning("Database circuit breaker is OPEN")
        return False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def close_db():
    """
    Close database connections.
    Call this during application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")
