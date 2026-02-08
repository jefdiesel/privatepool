"""Health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter

from config import get_settings
from db.database import check_db_connection, get_db_pool_status
from services.redis_service import check_redis_connection, get_redis_info
from services.solana_service import check_solana_connection, get_solana_slot

router = APIRouter()

# Track application start time for uptime calculation
_start_time = time.time()


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe for container orchestration.

    Returns 200 if the application is running.
    Used by Kubernetes/Docker to determine if container should be restarted.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness probe for traffic routing.

    Returns 200 if the application is ready to receive traffic.
    Checks that all required services are connected.
    """
    db_healthy = await check_db_connection()
    redis_healthy = await check_redis_connection()
    solana_healthy = await check_solana_connection()

    all_healthy = db_healthy and redis_healthy and solana_healthy

    return {
        "status": "ready" if all_healthy else "not_ready",
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "solana": "healthy" if solana_healthy else "unhealthy",
        },
    }


@router.get("")
async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check.

    Returns detailed status of all services including:
    - Database connectivity and pool status
    - Redis connectivity and memory usage
    - Solana RPC health and current slot
    - Application uptime
    """
    settings = get_settings()

    # Check all services
    db_healthy = await check_db_connection()
    redis_healthy = await check_redis_connection()
    solana_healthy = await check_solana_connection()

    # Get detailed status for each service
    db_pool = await get_db_pool_status()
    redis_info = await get_redis_info()
    solana_slot = await get_solana_slot()

    services: dict[str, dict[str, Any]] = {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql",
            "details": db_pool,
        },
        "redis": {
            "status": "healthy" if redis_healthy else "unhealthy",
            "type": "redis",
            "details": redis_info,
        },
        "solana": {
            "status": "healthy" if solana_healthy else "unhealthy",
            "type": "rpc",
            "details": {"current_slot": solana_slot} if solana_slot else None,
        },
    }

    healthy_count = sum(1 for s in services.values() if s["status"] == "healthy")
    total_count = len(services)

    # Calculate uptime
    uptime_seconds = int(time.time() - _start_time)
    uptime_days = uptime_seconds // 86400
    uptime_hours = (uptime_seconds % 86400) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    return {
        "status": "healthy" if healthy_count == total_count else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": f"{uptime_days}d {uptime_hours}h {uptime_minutes}m",
        },
        "services": services,
        "summary": f"{healthy_count}/{total_count} services healthy",
    }


@router.get("/metrics")
async def metrics() -> dict[str, Any]:
    """
    Prometheus-style metrics endpoint.

    Returns key metrics for monitoring dashboards.
    """
    db_pool = await get_db_pool_status()
    redis_info = await get_redis_info()

    uptime_seconds = int(time.time() - _start_time)

    return {
        "app_uptime_seconds": uptime_seconds,
        "db_pool_size": db_pool.get("pool_size", 0) if db_pool else 0,
        "db_pool_checked_in": db_pool.get("checked_in", 0) if db_pool else 0,
        "db_pool_checked_out": db_pool.get("checked_out", 0) if db_pool else 0,
        "redis_connected_clients": redis_info.get("connected_clients", 0) if redis_info else 0,
        "redis_used_memory_bytes": redis_info.get("used_memory", 0) if redis_info else 0,
    }
