from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_food_analysis_service
from app.core.config import Settings
from app.main import create_app
from app.models.base import Base
from app.services.food_analysis import (
    EstimatedItem,
    FoodAnalysisError,
    FoodAnalysisService,
    FoodEstimate,
)
from fakes import FakeFoodAnalyzer

MEAL = {
    "meal_type": "lunch",
    "eaten_at": "2026-08-18T12:30:00",
    "notes": "Con aceite de oliva",
    "items": [
        {
            "name": "Arroz",
            "quantity": "150.00",
            "unit": "g",
            "kcal": "195.00",
            "protein_g": "4.05",
            "fat_g": "0.45",
            "carbohydrates_g": "42.00",
        },
        {
            "name": "Pollo a la plancha",
            "quantity": "120.00",
            "unit": "g",
            "kcal": "198.00",
            "protein_g": "37.20",
            "fat_g": "4.30",
            "carbohydrates_g": "0.00",
        },
    ],
}


@pytest.fixture
async def application() -> AsyncIterator[FastAPI]:
    settings = Settings(app_env="test", jwt_secret_key="api-test-secret-key-value-32-chars")
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


async def sign_up(client: AsyncClient, email: str = "user@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Test User", "password": "secret-password"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def create_meal(
    client: AsyncClient, headers: dict[str, str], **overrides: Any
) -> dict[str, Any]:
    response = await client.post("/api/v1/meals", json={**MEAL, **overrides}, headers=headers)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_creating_a_meal_returns_the_computed_totals(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await create_meal(client, headers)

    assert body["total_kcal"] == "393.00"
    assert body["protein_g"] == "41.25"
    assert body["carbohydrates_g"] == "42.00"
    assert body["source"] == "manual"
    assert body["status"] == "confirmed"
    assert len(body["items"]) == 2


async def test_the_eaten_time_is_returned_as_utc(client: AsyncClient) -> None:
    headers = await sign_up(client)

    body = await create_meal(client, headers, eaten_at="2026-08-18T22:30:00+02:00")

    assert body["eaten_at"] == "2026-08-18T20:30:00Z"


async def test_a_meal_needs_at_least_one_item(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.post("/api/v1/meals", json={**MEAL, "items": []}, headers=headers)

    assert response.status_code == 422


async def test_a_meal_rejects_negative_energy(client: AsyncClient) -> None:
    headers = await sign_up(client)
    items = [{**MEAL["items"][0], "kcal": "-10.00"}]  # type: ignore[index]

    response = await client.post("/api/v1/meals", json={**MEAL, "items": items}, headers=headers)

    assert response.status_code == 422


async def test_meals_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/meals")

    assert response.status_code == 401


async def test_listing_can_be_filtered_by_day(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await create_meal(client, headers)
    await create_meal(client, headers, eaten_at="2026-08-19T12:30:00")

    response = await client.get("/api/v1/meals", params={"date": "2026-08-19"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["eaten_at"].startswith("2026-08-19")


async def test_the_daily_summary_adds_up_the_meals_of_the_day(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await create_meal(client, headers)
    await create_meal(client, headers, meal_type="dinner", eaten_at="2026-08-18T21:00:00")

    response = await client.get(
        "/api/v1/meals/summary", params={"date": "2026-08-18"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meal_count"] == 2
    assert body["total_kcal"] == "786.00"


async def test_a_meal_can_be_edited(client: AsyncClient) -> None:
    headers = await sign_up(client)
    meal = await create_meal(client, headers)

    response = await client.patch(
        f"/api/v1/meals/{meal['id']}",
        json={"meal_type": "dinner", "notes": None},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meal_type"] == "dinner"
    assert body["notes"] is None
    assert body["total_kcal"] == "393.00"


async def test_replacing_the_items_returns_the_stored_items(client: AsyncClient) -> None:
    headers = await sign_up(client)
    meal = await create_meal(client, headers)

    response = await client.patch(
        f"/api/v1/meals/{meal['id']}",
        json={
            "items": [
                {
                    "name": "Manzana",
                    "quantity": "180.00",
                    "unit": "g",
                    "kcal": "94.00",
                    "protein_g": "0.50",
                    "fat_g": "0.30",
                    "carbohydrates_g": "25.00",
                }
            ]
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_kcal"] == "94.00"
    assert [item["name"] for item in body["items"]] == ["Manzana"]
    assert all(item["id"] for item in body["items"])

    stored = await client.get(f"/api/v1/meals/{meal['id']}", headers=headers)
    assert [item["name"] for item in stored.json()["items"]] == ["Manzana"]


async def test_a_meal_can_be_deleted(client: AsyncClient) -> None:
    headers = await sign_up(client)
    meal = await create_meal(client, headers)

    response = await client.delete(f"/api/v1/meals/{meal['id']}", headers=headers)
    assert response.status_code == 204

    missing = await client.get(f"/api/v1/meals/{meal['id']}", headers=headers)
    assert missing.status_code == 404


async def test_a_user_cannot_read_another_users_meal(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    meal = await create_meal(client, owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.get(f"/api/v1/meals/{meal['id']}", headers=intruder_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


async def test_a_user_cannot_delete_another_users_meal(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    meal = await create_meal(client, owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.delete(f"/api/v1/meals/{meal['id']}", headers=intruder_headers)
    assert response.status_code == 404

    still_there = await client.get(f"/api/v1/meals/{meal['id']}", headers=owner_headers)
    assert still_there.status_code == 200


async def test_a_user_only_lists_their_own_meals(client: AsyncClient) -> None:
    owner_headers = await sign_up(client, "owner@example.com")
    await create_meal(client, owner_headers)
    intruder_headers = await sign_up(client, "intruder@example.com")

    response = await client.get("/api/v1/meals", headers=intruder_headers)

    assert response.status_code == 200
    assert response.json() == []


COFFEE_ESTIMATE = FoodEstimate(
    summary="Café con nata",
    items=[
        EstimatedItem(
            name="Café solo",
            quantity=Decimal("60"),
            unit="ml",
            kcal=Decimal("2.00"),
            protein_g=Decimal("0.20"),
            fat_g=Decimal("0.00"),
            carbohydrates_g=Decimal("0.00"),
            confidence=Decimal("0.9"),
        ),
        EstimatedItem(
            name="Nata para café",
            quantity=Decimal("20"),
            unit="ml",
            kcal=Decimal("58.00"),
            protein_g=Decimal("0.40"),
            fat_g=Decimal("6.00"),
            carbohydrates_g=Decimal("0.60"),
            confidence=Decimal("0.5"),
            assumptions=["Se asume nata líquida para café"],
        ),
    ],
    total_kcal=Decimal("60.00"),
)


def use_analyzer(application: FastAPI, analyzer: FakeFoodAnalyzer) -> None:
    application.dependency_overrides[get_food_analysis_service] = lambda: FoodAnalysisService(
        analyzer
    )


async def test_describing_a_meal_returns_an_estimate(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_analyzer(application, FakeFoodAnalyzer(estimate=COFFEE_ESTIMATE))

    response = await client.post(
        "/api/v1/meals/describe", json={"description": "café con nata"}, headers=headers
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_kcal"] == "60.00"
    assert [item["name"] for item in body["items"]] == ["Café solo", "Nata para café"]
    assert body["items"][1]["assumptions"] == ["Se asume nata líquida para café"]


async def test_describing_a_meal_stores_nothing(client: AsyncClient, application: FastAPI) -> None:
    headers = await sign_up(client)
    use_analyzer(application, FakeFoodAnalyzer(estimate=COFFEE_ESTIMATE))

    await client.post(
        "/api/v1/meals/describe", json={"description": "café con nata"}, headers=headers
    )
    meals = await client.get("/api/v1/meals", headers=headers)

    assert meals.json() == []


async def test_describing_a_meal_needs_a_configured_provider(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.post(
        "/api/v1/meals/describe", json={"description": "café con nata"}, headers=headers
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


async def test_a_failing_provider_is_reported_as_an_analysis_error(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_analyzer(application, FakeFoodAnalyzer(error=FoodAnalysisError()))

    response = await client.post(
        "/api/v1/meals/describe", json={"description": "café con nata"}, headers=headers
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "AI_ANALYSIS_FAILED"


async def test_describing_a_meal_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/meals/describe", json={"description": "café con nata"})

    assert response.status_code == 401
