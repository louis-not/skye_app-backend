import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "timestamp" in data["data"]
    assert "app_name" in data["data"]
    assert "version" in data["data"]


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint."""
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "components" in data["data"]
