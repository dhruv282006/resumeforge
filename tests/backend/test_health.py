"""Tests for GET /api/v1/health endpoint.

All tests use ASGI transport — no live network connections are made.
Database and Redis checks are mocked to isolate the endpoint logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestHealthEndpointAllHealthy:
    """Health endpoint returns 'healthy' when all services respond."""

    @pytest.mark.asyncio
    async def test_returns_200(self, async_client: AsyncClient) -> None:
        """HTTP 200 is returned regardless of service health."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_healthy(self, async_client: AsyncClient) -> None:
        """Aggregate status is 'healthy' when all services are up."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_database_status_ok(self, async_client: AsyncClient) -> None:
        """Database service status is 'ok' when DB check succeeds."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert data["services"]["database"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_redis_status_ok(self, async_client: AsyncClient) -> None:
        """Redis service status is 'ok' when Redis check succeeds."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert data["services"]["redis"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_response_shape(self, async_client: AsyncClient) -> None:
        """Response contains all required top-level fields."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "services" in data

    @pytest.mark.asyncio
    async def test_service_latency_present(self, async_client: AsyncClient) -> None:
        """Each service entry includes a numeric latency_ms field."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        for service_data in data["services"].values():
            assert "latency_ms" in service_data
            assert isinstance(service_data["latency_ms"], float | int)

    @pytest.mark.asyncio
    async def test_version_matches_settings(self, async_client: AsyncClient, settings) -> None:
        """Version in response matches the application settings."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert data["version"] == settings.APP_VERSION

    @pytest.mark.asyncio
    async def test_environment_matches_settings(
        self, async_client: AsyncClient, settings
    ) -> None:
        """Environment in response matches the application settings."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert data["environment"] == settings.ENVIRONMENT


class TestHealthEndpointDatabaseDown:
    """Health endpoint reports 'degraded' when the database is unreachable."""

    @pytest.mark.asyncio
    async def test_returns_200_when_db_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Endpoint still returns HTTP 200 when DB is down."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_degraded_when_db_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Aggregate status is 'degraded' when DB is unreachable."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_database_status_error_when_db_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Database service status is 'error' when DB check returns False."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        data = response.json()
        assert data["services"]["database"]["status"] == "error"
        assert data["services"]["redis"]["status"] == "ok"


class TestHealthEndpointRedisDown:
    """Health endpoint reports 'degraded' when Redis is unreachable."""

    @pytest.mark.asyncio
    async def test_returns_200_when_redis_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Endpoint still returns HTTP 200 when Redis is down."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_degraded_when_redis_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Aggregate status is 'degraded' when Redis is unreachable."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_redis_status_error_when_redis_down(
        self, async_client_no_mocks: AsyncClient
    ) -> None:
        """Redis service status is 'error' when Redis check returns False."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            response = await async_client_no_mocks.get("/api/v1/health")
        data = response.json()
        assert data["services"]["redis"]["status"] == "error"
        assert data["services"]["database"]["status"] == "ok"
