"""
Health check endpoints and monitoring.
"""
import psutil
import time
from datetime import datetime
from fastapi import APIRouter, Response
from typing import Dict, Any

from app.observability.logging import get_logger
from app.observability.metrics import metrics_endpoint

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

# Track application start time
START_TIME = time.time()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with system metrics.
    
    Returns:
        Detailed health status including system resources
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate uptime
        uptime_seconds = round(time.time() - START_TIME, 2)
        uptime_hours = round(uptime_seconds / 3600, 2)
        
        # Determine overall health status
        status = "healthy"
        issues = []
        
        if cpu_percent > 80:
            status = "degraded"
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 80:
            status = "degraded"
            issues.append(f"High memory usage: {memory.percent}%")
        
        if disk.percent > 80:
            status = "degraded"
            issues.append(f"High disk usage: {disk.percent}%")
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": {
                "seconds": uptime_seconds,
                "hours": uptime_hours
            },
            "system": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": disk.percent
                }
            },
            "issues": issues
        }
    
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc)
        }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/load balancers.
    
    Returns:
        Readiness status
    """
    # Check if application is ready to accept traffic
    # This could include database connectivity, external service checks, etc.
    
    ready = True
    checks = {}
    
    # Example: Check if enough time has passed since startup
    uptime = time.time() - START_TIME
    if uptime < 2:  # Need at least 2 seconds to be ready
        ready = False
        checks["startup"] = {
            "status": "not_ready",
            "message": "Application still starting up"
        }
    else:
        checks["startup"] = {
            "status": "ready",
            "message": "Application ready"
        }
    
    # Example: Check system resources
    memory = psutil.virtual_memory()
    if memory.percent > 95:
        ready = False
        checks["resources"] = {
            "status": "not_ready",
            "message": f"Memory usage critical: {memory.percent}%"
        }
    else:
        checks["resources"] = {
            "status": "ready",
            "message": "Resources available"
        }
    
    return {
        "ready": ready,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes.
    
    Returns:
        Liveness status
    """
    # Simple check that application is alive
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def get_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus-formatted metrics
    """
    return metrics_endpoint()
