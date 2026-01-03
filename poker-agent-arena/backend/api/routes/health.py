"""Health check endpoints."""

from fastapi import APIRouter

from db.database import check_db_connection
from services.redis_service import check_redis_connection
from services.solana_service import check_solana_connection

router = APIRouter()


@router.get("/live")
async def liveness_check() -> dict:
    """
    Liveness probe for container orchestration.

    Returns 200 if the application is running.
    Used by Kubernetes/Docker to determine if container should be restarted.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check() -> dict:
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
async def health_check() -> dict:
    """
    Comprehensive health check.

    Returns detailed status of all services.
    """
    db_healthy = await check_db_connection()
    redis_healthy = await check_redis_connection()
    solana_healthy = await check_solana_connection()

    services = {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql",
        },
        "redis": {
            "status": "healthy" if redis_healthy else "unhealthy",
            "type": "redis",
        },
        "solana": {
            "status": "healthy" if solana_healthy else "unhealthy",
            "type": "rpc",
        },
    }

    healthy_count = sum(1 for s in services.values() if s["status"] == "healthy")
    total_count = len(services)

    return {
        "status": "healthy" if healthy_count == total_count else "degraded",
        "services": services,
        "summary": f"{healthy_count}/{total_count} services healthy",
    }
