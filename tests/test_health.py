"""
Tests for health check endpoint with real DB/Redis pings.
"""

import os

os.environ.setdefault("FILTER_THIRD_PARTY_LIB", "false")
os.environ.setdefault("DD_TRACE_ENABLED", "false")
os.environ.setdefault("DD_PATCH_MODULES", "none")

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Tests for /health endpoint."""

    def test_health_returns_services_dict(self) -> None:
        """Health response should include redis and database keys."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "redis" in data["services"]
        assert "database" in data["services"]

    @patch("app.routers.health.redis_client")
    def test_health_degraded_when_redis_down(self, mock_redis: MagicMock) -> None:
        """Health should return degraded when Redis ping fails."""
        mock_redis_inner = MagicMock()
        mock_redis_inner.ping.side_effect = ConnectionError("Redis down")
        mock_redis._redis_client = mock_redis_inner

        response = client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["redis"] == "unavailable"

    @patch("app.routers.health.engine")
    def test_health_degraded_when_db_down(self, mock_engine: MagicMock) -> None:
        """Health should return degraded when DB connection fails."""
        mock_engine.connect.side_effect = Exception("DB down")

        response = client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] == "unavailable"
