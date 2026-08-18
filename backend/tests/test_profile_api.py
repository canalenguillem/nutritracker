from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from support import build_settings

from app.main import create_app
from app.models.base import Base


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


async def weigh(
    client: AsyncClient, headers: dict[str, str], weight: str, measured_at: str
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/weights",
        json={"weight_kg": weight, "measured_at": measured_at},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_the_profile_starts_empty_but_exists(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["height_cm"] is None
    assert body["activity_level"] == "moderate"
    assert body["primary_goal"] == "maintain_weight"


async def test_the_profile_keeps_what_it_is_given(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.patch(
        "/api/v1/profile",
        json={
            "height_cm": "178.00",
            "target_weight_kg": "75.00",
            "activity_level": "active",
            "primary_goal": "lose_weight",
            "biological_sex": "male",
            "birth_date": "1988-04-12",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["height_cm"] == "178.00"
    assert body["target_weight_kg"] == "75.00"
    assert body["activity_level"] == "active"
    assert body["birth_date"] == "1988-04-12"

    again = await client.get("/api/v1/profile", headers=headers)
    assert again.json()["height_cm"] == "178.00"


async def test_an_impossible_height_is_refused(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.patch("/api/v1/profile", json={"height_cm": "12.00"}, headers=headers)

    assert response.status_code == 422


async def test_the_profile_is_private(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    await client.patch("/api/v1/profile", json={"height_cm": "178.00"}, headers=owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.get("/api/v1/profile", headers=intruder_headers)

    assert response.json()["height_cm"] is None


async def test_a_weight_reading_updates_the_profile(client: AsyncClient) -> None:
    headers = await sign_up(client)

    await weigh(client, headers, "80.40", "2026-08-18T08:00:00")

    profile = await client.get("/api/v1/profile", headers=headers)
    assert profile.json()["current_weight_kg"] == "80.40"


async def test_the_history_carries_the_trend(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await weigh(client, headers, "80.00", "2026-08-17T08:00:00")
    await weigh(client, headers, "82.00", "2026-08-18T08:00:00")

    response = await client.get("/api/v1/weights/history", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["latest_weight_kg"] == "82.00"
    assert body["latest_trend_kg"] == "80.20"
    assert len(body["points"]) == 2


async def test_the_history_reports_the_body_mass_index(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await client.patch("/api/v1/profile", json={"height_cm": "178.00"}, headers=headers)
    await weigh(client, headers, "80.00", "2026-08-18T08:00:00")

    response = await client.get("/api/v1/weights/history", headers=headers)

    assert response.json()["body_mass_index"] == "25.25"


async def test_without_a_height_there_is_no_body_mass_index(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await weigh(client, headers, "80.00", "2026-08-18T08:00:00")

    assert (await client.get("/api/v1/weights/history", headers=headers)).json()[
        "body_mass_index"
    ] is None


async def test_a_reading_can_be_removed(client: AsyncClient) -> None:
    headers = await sign_up(client)
    entry = await weigh(client, headers, "80.00", "2026-08-18T08:00:00")

    response = await client.delete(f"/api/v1/weights/{entry['id']}", headers=headers)

    assert response.status_code == 204
    assert (await client.get("/api/v1/weights", headers=headers)).json() == []


async def test_another_account_cannot_remove_a_reading(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    entry = await weigh(client, owner_headers, "80.00", "2026-08-18T08:00:00")
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.delete(f"/api/v1/weights/{entry['id']}", headers=intruder_headers)

    assert response.status_code == 404
    assert len((await client.get("/api/v1/weights", headers=owner_headers)).json()) == 1


async def test_weights_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/weights/history")).status_code == 401
    assert (await client.get("/api/v1/profile")).status_code == 401


async def test_the_history_projects_the_target_date(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await client.patch("/api/v1/profile", json={"target_weight_kg": "78.00"}, headers=headers)

    # A month of steady loss, one reading a day.
    for day in range(30):
        weight = Decimal("82.00") - Decimal("0.05") * day
        await weigh(client, headers, f"{weight:.2f}", f"2026-07-{day + 1:02d}T08:00:00")

    response = await client.get("/api/v1/weights/history", headers=headers)

    assert response.status_code == 200, response.text
    projection = response.json()["projection"]
    assert projection["status"] == "reachable"
    assert projection["days_to_target"] > 0
    assert projection["reaches_target_on"] > "2026-07-30"
    assert Decimal(projection["kg_per_week"]) < Decimal("0")


async def test_a_target_in_the_wrong_direction_is_flagged(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await client.patch("/api/v1/profile", json={"target_weight_kg": "70.00"}, headers=headers)

    for day in range(30):
        weight = Decimal("82.00") + Decimal("0.05") * day
        await weigh(client, headers, f"{weight:.2f}", f"2026-07-{day + 1:02d}T08:00:00")

    projection = (await client.get("/api/v1/weights/history", headers=headers)).json()["projection"]

    assert projection["status"] == "wrong_way"
    assert projection["reaches_target_on"] is None


async def test_without_a_target_nothing_is_projected(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await weigh(client, headers, "80.00", "2026-08-18T08:00:00")

    projection = (await client.get("/api/v1/weights/history", headers=headers)).json()["projection"]

    assert projection["status"] == "not_enough_data"
    assert projection["reaches_target_on"] is None
