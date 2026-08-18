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

SESSION = {
    "activity_name": "Brooklyn Fitboxing",
    "duration_minutes": 47,
    "intensity": "high",
    "performed_at": "2026-08-18T19:30:00",
    "notes": "Clase de los martes",
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


async def record(client: AsyncClient, headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/exercises", json={**SESSION, **overrides}, headers=headers
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_a_session_without_a_weight_is_not_estimated(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await record(client, headers)

    assert body["activity_name"] == "Brooklyn Fitboxing"
    assert body["estimated_calories"] is None
    assert body["counted_calories"] == "0.00"


async def test_giving_a_weight_produces_an_estimate(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await record(client, headers, weight_kg="80.00")

    assert body["estimated_calories"] == "714.40"
    assert body["counted_calories"] == "714.40"


async def test_the_weight_is_remembered_for_the_next_session(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await record(client, headers, weight_kg="80.00")

    body = await record(client, headers, performed_at="2026-08-19T19:30:00")

    assert body["estimated_calories"] == "714.40"


async def test_the_persons_own_number_wins(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await record(client, headers, weight_kg="80.00", confirmed_calories="520.00")

    assert body["estimated_calories"] == "714.40"
    assert body["confirmed_calories"] == "520.00"
    assert body["counted_calories"] == "520.00"


async def test_the_time_is_returned_as_utc(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await record(client, headers, performed_at="2026-08-18T21:30:00+02:00")

    assert body["performed_at"] == "2026-08-18T19:30:00Z"


async def test_changing_the_effort_recomputes_the_estimate(client: AsyncClient) -> None:
    headers = await sign_up(client)
    session = await record(client, headers, weight_kg="80.00")

    response = await client.patch(
        f"/api/v1/exercises/{session['id']}",
        json={"duration_minutes": 60, "intensity": "moderate"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["estimated_calories"] == "760.00"


async def test_a_session_can_be_deleted(client: AsyncClient) -> None:
    headers = await sign_up(client)
    session = await record(client, headers)

    assert (
        await client.delete(f"/api/v1/exercises/{session['id']}", headers=headers)
    ).status_code == 204
    assert (
        await client.get(f"/api/v1/exercises/{session['id']}", headers=headers)
    ).status_code == 404


async def test_sessions_are_listed_by_day(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await record(client, headers)
    await record(client, headers, performed_at="2026-08-19T19:30:00")

    response = await client.get("/api/v1/exercises", params={"date": "2026-08-19"}, headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_exercise_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/exercises")).status_code == 401


async def test_a_session_of_another_account_is_not_found(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    session = await record(client, owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.get(f"/api/v1/exercises/{session['id']}", headers=intruder_headers)

    assert response.status_code == 404


async def test_the_daily_summary_counts_the_exercise(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await client.post(
        "/api/v1/meals",
        json={
            "meal_type": "lunch",
            "eaten_at": "2026-08-18T13:00:00",
            "items": [
                {
                    "name": "Arroz",
                    "quantity": "150.00",
                    "unit": "g",
                    "kcal": "800.00",
                    "protein_g": "10.00",
                    "fat_g": "5.00",
                    "carbohydrates_g": "40.00",
                }
            ],
        },
        headers=headers,
    )
    await record(client, headers, weight_kg="80.00")

    response = await client.get(
        "/api/v1/meals/summary", params={"date": "2026-08-18"}, headers=headers
    )

    body = response.json()
    assert body["total_kcal"] == "800.00"
    assert body["exercise_kcal"] == "714.40"
    assert body["exercise_count"] == 1
    assert body["net_kcal"] == "85.60"
