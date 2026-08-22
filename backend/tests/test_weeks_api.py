from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from support import build_settings

from app.api.deps import SessionDependency, get_week_service
from app.main import create_app
from app.models.base import Base
from app.repositories.weekly_summaries import SQLAlchemyWeeklySummaryRepository
from app.services.week_metrics import WeekMetrics, monday_of
from app.services.week_review import WeekReview, WeekReviewError
from app.services.weeks import WeekService


@dataclass
class FakeWeekReviewer:
    review_text: WeekReview = field(
        default_factory=lambda: WeekReview(
            headline="Una semana tranquila.",
            observations=["Comiste cinco días de siete."],
            comparison=None,
            watch_out=None,
        )
    )
    fails: bool = False
    calls: list[tuple[WeekMetrics, WeekMetrics | None]] = field(default_factory=list)

    async def review(
        self, metrics: WeekMetrics, previous: WeekMetrics | None, language: str
    ) -> WeekReview:
        if self.fails:
            raise WeekReviewError("no")

        self.calls.append((metrics, previous))
        return self.review_text


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


def use_reviewer(application: FastAPI, reviewer: FakeWeekReviewer | None) -> None:
    """Swap in a reviewer that costs nothing, or none at all."""

    def dependency(session: SessionDependency) -> WeekService:
        return WeekService(SQLAlchemyWeeklySummaryRepository(session), reviewer)

    application.dependency_overrides[get_week_service] = dependency


async def sign_up(client: AsyncClient, email: str = "user@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Test User", "password": "secret-password"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def eat(client: AsyncClient, headers: dict[str, str], when: datetime, kcal: str) -> None:
    response = await client.post(
        "/api/v1/meals",
        json={
            "meal_type": "lunch",
            "eaten_at": when.isoformat(),
            "items": [
                {
                    "name": "Arroz",
                    "quantity": "1",
                    "unit": "plato",
                    "kcal": kcal,
                    "protein_g": "10",
                    "fat_g": "5",
                    "carbohydrates_g": "60",
                }
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def madrid_noon(day: date) -> datetime:
    # Noon UTC is inside the Madrid day whatever the offset, so the meal lands
    # on the day it is meant to.
    return datetime(day.year, day.month, day.day, 12, 0, tzinfo=UTC)


def this_monday() -> date:
    return monday_of(datetime.now(UTC).date())


async def test_the_week_runs_monday_to_sunday(client: AsyncClient) -> None:
    headers = await sign_up(client)

    response = await client.get("/api/v1/weeks", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["week_start"] == this_monday().isoformat()
    assert body["week_end"] == (this_monday() + timedelta(days=6)).isoformat()
    assert [day["log_date"] for day in body["days"]] == [
        (this_monday() + timedelta(days=offset)).isoformat() for offset in range(7)
    ]


async def test_any_day_asked_for_returns_the_week_holding_it(client: AsyncClient) -> None:
    headers = await sign_up(client)
    sunday = this_monday() - timedelta(days=1)

    response = await client.get(f"/api/v1/weeks?week={sunday.isoformat()}", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["week_start"] == (this_monday() - timedelta(days=7)).isoformat()


async def test_a_week_running_still_has_no_review_and_is_not_complete(
    client: AsyncClient,
) -> None:
    headers = await sign_up(client)

    body = (await client.get("/api/v1/weeks", headers=headers)).json()

    assert body["is_complete"] is False
    assert body["review"] is None
    assert body["has_previous_review"] is False


async def test_reviewing_a_running_week_leaves_it_open_to_be_reviewed_again(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_reviewer(application, FakeWeekReviewer())
    await eat(client, headers, madrid_noon(this_monday()), "700")

    first = await client.post("/api/v1/weeks/review", headers=headers)

    assert first.status_code == 201, first.text
    assert first.json()["review"]["is_final"] is False

    # The week is still running, so a second look is allowed to say something
    # different: what it describes has changed since.
    second = await client.post("/api/v1/weeks/review", headers=headers)
    assert second.status_code == 201, second.text


async def test_a_finished_week_keeps_the_summary_it_was_given(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_reviewer(application, FakeWeekReviewer())
    last_monday = this_monday() - timedelta(days=7)
    await eat(client, headers, madrid_noon(last_monday), "700")

    first = await client.post(
        f"/api/v1/weeks/review?week={last_monday.isoformat()}", headers=headers
    )
    assert first.status_code == 201, first.text
    assert first.json()["review"]["is_final"] is True

    again = await client.post(
        f"/api/v1/weeks/review?week={last_monday.isoformat()}", headers=headers
    )
    assert again.status_code == 409, again.text


async def test_a_week_with_nothing_recorded_has_nothing_to_look_back_at(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_reviewer(application, FakeWeekReviewer())

    response = await client.post("/api/v1/weeks/review", headers=headers)

    assert response.status_code == 422, response.text


async def test_without_a_reviewer_the_week_says_so_rather_than_offering_the_button(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    use_reviewer(application, None)
    await eat(client, headers, madrid_noon(this_monday()), "700")

    assert (await client.get("/api/v1/weeks", headers=headers)).json()["can_review"] is False
    assert (await client.post("/api/v1/weeks/review", headers=headers)).status_code == 503


async def test_a_failed_review_is_not_stored(client: AsyncClient, application: FastAPI) -> None:
    headers = await sign_up(client)
    use_reviewer(application, FakeWeekReviewer(fails=True))
    await eat(client, headers, madrid_noon(this_monday()), "700")

    assert (await client.post("/api/v1/weeks/review", headers=headers)).status_code == 502
    assert (await client.get("/api/v1/weeks", headers=headers)).json()["review"] is None


async def test_the_previous_week_is_compared_only_once_it_was_itself_written_up(
    client: AsyncClient, application: FastAPI
) -> None:
    headers = await sign_up(client)
    reviewer = FakeWeekReviewer()
    use_reviewer(application, reviewer)
    last_monday = this_monday() - timedelta(days=7)
    await eat(client, headers, madrid_noon(last_monday), "700")
    await eat(client, headers, madrid_noon(this_monday()), "700")

    # Last week has figures but no summary, so this week has nothing to be set
    # beside: the reviewer is handed no previous week at all.
    await client.post("/api/v1/weeks/review", headers=headers)
    assert reviewer.calls[-1][1] is None

    await client.post(f"/api/v1/weeks/review?week={last_monday.isoformat()}", headers=headers)
    await client.post("/api/v1/weeks/review", headers=headers)
    previous = reviewer.calls[-1][1]
    assert previous is not None
    assert previous.week_start == last_monday


async def test_a_week_reports_the_days_it_actually_holds(client: AsyncClient) -> None:
    headers = await sign_up(client)
    await eat(client, headers, madrid_noon(this_monday()), "700")
    await eat(client, headers, madrid_noon(this_monday() + timedelta(days=1)), "500")

    body = (await client.get("/api/v1/weeks", headers=headers)).json()

    assert body["days_with_food"] == 2
    assert body["total_food_kcal"] == "1200.00"
    assert body["average_food_kcal"] == "600.00"
