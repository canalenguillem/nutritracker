from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def application() -> FastAPI:
    return create_app(Settings(app_env="test"))


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=application)
    async with (
        application.router.lifespan_context(application),
        AsyncClient(transport=transport, base_url="http://testserver") as client,
    ):
        yield client


async def test_liveness_returns_utc_timestamp_and_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["timestamp"].endswith("Z")
    assert response.headers["X-Request-ID"]


async def test_unknown_route_uses_consistent_error_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Not Found",
            "details": None,
            "request_id": response.headers["X-Request-ID"],
        }
    }
