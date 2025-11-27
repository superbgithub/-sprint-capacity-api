"""
Main FastAPI application for Team Capacity Management API.
This is the entry point that configures and runs the server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sprints

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

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your API to be called from web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the sprint routes
app.include_router(sprints.router, prefix="/v1")


@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    """
    return {
        "message": "Team Capacity Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - useful for monitoring.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # Run the server on http://localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
