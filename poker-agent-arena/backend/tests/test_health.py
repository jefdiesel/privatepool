"""Tests for health check endpoints."""

from unittest.mock import AsyncMock, patch


def test_liveness_endpoint(client):
    """Test that liveness endpoint returns alive status."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint_all_healthy(client):
    """Test readiness endpoint when all services are healthy."""
    with patch("api.routes.health.check_db_connection", new_callable=AsyncMock) as mock_db, \
         patch("api.routes.health.check_redis_connection", new_callable=AsyncMock) as mock_redis, \
         patch("api.routes.health.check_solana_connection", new_callable=AsyncMock) as mock_solana:

        mock_db.return_value = True
        mock_redis.return_value = True
        mock_solana.return_value = True

        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["services"]["database"] == "healthy"
        assert data["services"]["redis"] == "healthy"
        assert data["services"]["solana"] == "healthy"


def test_readiness_endpoint_db_unhealthy(client):
    """Test readiness endpoint when database is unhealthy."""
    with patch("api.routes.health.check_db_connection", new_callable=AsyncMock) as mock_db, \
         patch("api.routes.health.check_redis_connection", new_callable=AsyncMock) as mock_redis, \
         patch("api.routes.health.check_solana_connection", new_callable=AsyncMock) as mock_solana:

        mock_db.return_value = False
        mock_redis.return_value = True
        mock_solana.return_value = True

        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["services"]["database"] == "unhealthy"


def test_health_endpoint_comprehensive(client):
    """Test comprehensive health endpoint."""
    with patch("api.routes.health.check_db_connection", new_callable=AsyncMock) as mock_db, \
         patch("api.routes.health.check_redis_connection", new_callable=AsyncMock) as mock_redis, \
         patch("api.routes.health.check_solana_connection", new_callable=AsyncMock) as mock_solana:

        mock_db.return_value = True
        mock_redis.return_value = True
        mock_solana.return_value = True

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["summary"] == "3/3 services healthy"


def test_health_endpoint_degraded(client):
    """Test health endpoint when some services are down."""
    with patch("api.routes.health.check_db_connection", new_callable=AsyncMock) as mock_db, \
         patch("api.routes.health.check_redis_connection", new_callable=AsyncMock) as mock_redis, \
         patch("api.routes.health.check_solana_connection", new_callable=AsyncMock) as mock_solana:

        mock_db.return_value = True
        mock_redis.return_value = False
        mock_solana.return_value = True

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["summary"] == "2/3 services healthy"
