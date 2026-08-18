from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from support import build_settings

from app.api.v1.auth import REFRESH_COOKIE_NAME
from app.main import create_app
from app.models.base import Base

REGISTRATION = {
    "email": "user@example.com",
    "display_name": "Test User",
    "password": "secret-password",
}


@pytest.fixture
async def application() -> AsyncIterator[FastAPI]:
    settings = build_settings()
    application = create_app(settings)
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


async def register(client: AsyncClient) -> dict[str, object]:
    response = await client.post("/api/v1/auth/register", json=REGISTRATION)
    assert response.status_code == 201, response.text
    return response.json()


async def test_register_is_refused_while_new_accounts_are_closed() -> None:
    settings = build_settings(registration_open=False)
    application = create_app(settings)
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    application.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/auth/register", json=REGISTRATION)

    await engine.dispose()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_register_returns_a_session_and_sets_the_refresh_cookie(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/v1/auth/register", json=REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["role"] == "user"
    assert "password" not in response.text

    cookie = response.cookies[REFRESH_COOKIE_NAME]
    assert cookie
    assert cookie != body["access_token"]
    set_cookie_header = response.headers["set-cookie"]
    assert "HttpOnly" in set_cookie_header
    assert "Path=/api/v1/auth" in set_cookie_header


async def test_register_rejects_a_duplicate_email(client: AsyncClient) -> None:
    await register(client)

    response = await client.post("/api/v1/auth/register", json=REGISTRATION)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_register_rejects_a_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={**REGISTRATION, "password": "short"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_login_rejects_a_wrong_password(client: AsyncClient) -> None:
    await register(client)

    response = await client.post(
        "/api/v1/auth/login", json={"email": REGISTRATION["email"], "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_login_returns_a_working_access_token(client: AsyncClient) -> None:
    await register(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )

    assert response.status_code == 200
    access_token = response.json()["access_token"]
    profile = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "user@example.com"


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-token"}],
)
async def test_me_requires_a_valid_bearer_token(
    client: AsyncClient, headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_refresh_rotates_the_cookie_and_rejects_the_replayed_one(
    client: AsyncClient,
) -> None:
    await register(client)
    first_cookie = client.cookies[REFRESH_COOKIE_NAME]

    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert client.cookies[REFRESH_COOKIE_NAME] != first_cookie

    rotated_cookie = client.cookies[REFRESH_COOKIE_NAME]
    client.cookies.clear()
    client.cookies.set(REFRESH_COOKIE_NAME, first_cookie, path="/api/v1/auth")
    replay = await client.post("/api/v1/auth/refresh")

    assert replay.status_code == 401

    # Replaying a used token drops every session, including the rotated one.
    client.cookies.clear()
    client.cookies.set(REFRESH_COOKIE_NAME, rotated_cookie, path="/api/v1/auth")
    after_reuse = await client.post("/api/v1/auth/refresh")

    assert after_reuse.status_code == 401


async def test_refresh_without_a_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


async def test_logout_invalidates_the_refresh_cookie(client: AsyncClient) -> None:
    await register(client)

    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert not client.cookies.get(REFRESH_COOKIE_NAME)

    refresh = await client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401


async def test_google_login_reports_that_it_is_not_configured(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/google/login")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
