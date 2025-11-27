"""
Main FastAPI application for Team Capacity Management API.
This is the entry point that configures and runs the server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sprints, calendar
from app.observability import (
    setup_logging,
    init_metrics_metadata,
    ObservabilityMiddleware,
    PerformanceMonitorMiddleware
)
from app.observability.health import router as health_router
from app.events import get_kafka_producer
from app.config.database import init_db, close_db
# Import models so they're registered with SQLAlchemy Base before init_db()
from app.models import db_models  # noqa: F401

# Setup structured logging
setup_logging(log_level="INFO")

# Create FastAPI application instance
app = FastAPI(
    title="Team Capacity Management API",
    description="API for managing team capacity planning across sprints",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com"
    }
)

# Initialize metrics metadata
init_metrics_metadata(
    app_name="team-capacity-api",
    version="1.0.0",
    environment="production"
)

# Add observability middleware (order matters - add these first)
app.add_middleware(PerformanceMonitorMiddleware, slow_request_threshold=1.0)
app.add_middleware(ObservabilityMiddleware)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your API to be called from web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sprints.router, prefix="/v1")
app.include_router(calendar.router)  # Feature-flagged calendar routes
app.include_router(health_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize database tables
    await init_db()
    
    # Initialize Kafka producer
    kafka_producer = get_kafka_producer()
    await kafka_producer.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    # Close Kafka producer
    kafka_producer = get_kafka_producer()
    await kafka_producer.stop()
    
    # Close database connections
    await close_db()


@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    """
    return {
        "message": "Team Capacity Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import uvicorn
    # Run the server on http://localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
