from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from support import build_settings

from app.main import create_app
from app.models.base import Base

# Madrid is two hours ahead in August, so a night from 23:30 to 07:00 local
# is stored as 21:30 to 05:00.
LAST_NIGHT = {
    "started_at": "2026-08-18T23:30:00+02:00",
    "ended_at": "2026-08-19T07:00:00+02:00",
}


@pytest.fixture
async def application() -> AsyncIterator[FastAPI]:
    application = create_app(build_settings())
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    application.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    yield application
    await engine.dispose()


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def sign_up(client: AsyncClient, email: str = "user@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Test User", "password": "secret-password"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def sleep(client: AsyncClient, headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    response = await client.post("/api/v1/sleep", json={**LAST_NIGHT, **overrides}, headers=headers)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_a_night_is_measured_from_its_two_ends(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await sleep(client, headers, quality="good")

    assert body["hours"] == "7.50"
    assert body["quality"] == "good"
    assert body["started_at"] == "2026-08-18T21:30:00Z"
    assert body["ended_at"] == "2026-08-19T05:00:00Z"


async def test_the_night_belongs_to_the_day_it_ended(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await sleep(client, headers)

    woke_on = await client.get("/api/v1/sleep", params={"date": "2026-08-19"}, headers=headers)
    went_to_bed_on = await client.get(
        "/api/v1/sleep", params={"date": "2026-08-18"}, headers=headers
    )

    assert woke_on.json() is not None
    assert woke_on.json()["hours"] == "7.50"
    # The night is not reported on the evening it started.
    assert went_to_bed_on.json() is None


async def test_a_day_without_sleep_recorded_says_nothing(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.get("/api/v1/sleep", params={"date": "2026-08-19"}, headers=headers)

    assert response.status_code == 200
    assert response.json() is None


async def test_a_night_that_ends_before_it_starts_is_refused(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.post(
        "/api/v1/sleep",
        json={"started_at": "2026-08-19T07:00:00Z", "ended_at": "2026-08-18T23:30:00Z"},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_night_longer_than_a_day_is_refused(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.post(
        "/api/v1/sleep",
        json={"started_at": "2026-08-17T23:00:00Z", "ended_at": "2026-08-19T07:00:00Z"},
        headers=headers,
    )

    assert response.status_code == 422


async def test_a_night_can_be_removed(client: AsyncClient) -> None:
    headers = await sign_up(client)
    night = await sleep(client, headers)

    assert (await client.delete(f"/api/v1/sleep/{night['id']}", headers=headers)).status_code == 204
    assert (
        await client.get("/api/v1/sleep", params={"date": "2026-08-19"}, headers=headers)
    ).json() is None


async def test_another_account_cannot_remove_a_night(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    night = await sleep(client, owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.delete(f"/api/v1/sleep/{night['id']}", headers=intruder_headers)

    assert response.status_code == 404
    assert (
        await client.get("/api/v1/sleep", params={"date": "2026-08-19"}, headers=owner_headers)
    ).json() is not None


async def test_sleep_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/sleep")).status_code == 401
