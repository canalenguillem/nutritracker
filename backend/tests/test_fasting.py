from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.enums import MealType
from app.models.user import User
from app.services.meals import MealService, NewMeal, NewMealItem
from fakes import FakeDailyLogRepository, FakeMealRepository

NOW = datetime(2026, 8, 18, 20, 0)


def build_user(timezone: str = "Europe/Madrid") -> User:
    return User(id=uuid4(), email="user@example.com", display_name="User", timezone=timezone)


def an_item() -> NewMealItem:
    return NewMealItem(
        name="Algo",
        quantity=Decimal("100"),
        unit="g",
        kcal=Decimal("100"),
        protein_g=Decimal("5"),
        fat_g=Decimal("5"),
        carbohydrates_g=Decimal("10"),
    )


@pytest.fixture
def service() -> MealService:
    daily_logs = FakeDailyLogRepository()
    return MealService(meals=FakeMealRepository(daily_logs=daily_logs), daily_logs=daily_logs)


async def eat(service: MealService, user: User, at: datetime) -> None:
    await service.create_meal(
        user, NewMeal(meal_type=MealType.SNACK, eaten_at=at, items=[an_item()])
    )


async def test_the_gap_between_last_night_and_this_morning_is_the_fast(
    service: MealService,
) -> None:
    user = build_user()
    await eat(service, user, datetime(2026, 8, 17, 19, 30))
    await eat(service, user, datetime(2026, 8, 18, 11, 30))

    window = await service.fasting_window(user, date(2026, 8, 18), NOW)

    assert window.hours == Decimal("16.00")
    assert window.started_at == datetime(2026, 8, 17, 19, 30)
    assert window.ended_at == datetime(2026, 8, 18, 11, 30)
    assert window.ongoing is False


async def test_only_the_first_meal_of_the_day_closes_the_fast(service: MealService) -> None:
    user = build_user()
    await eat(service, user, datetime(2026, 8, 17, 21, 0))
    await eat(service, user, datetime(2026, 8, 18, 9, 0))
    await eat(service, user, datetime(2026, 8, 18, 14, 0))

    window = await service.fasting_window(user, date(2026, 8, 18), NOW)

    assert window.hours == Decimal("12.00")
    assert window.ended_at == datetime(2026, 8, 18, 9, 0)


async def test_a_fast_still_running_is_counted_up_to_now(service: MealService) -> None:
    user = build_user()
    await eat(service, user, datetime(2026, 8, 17, 21, 0))

    window = await service.fasting_window(user, date(2026, 8, 18), NOW)

    assert window.ongoing is True
    assert window.ended_at is None
    assert window.hours == Decimal("23.00")


async def test_a_past_day_stops_counting_at_its_own_midnight(service: MealService) -> None:
    user = build_user()
    await eat(service, user, datetime(2026, 8, 16, 20, 0))

    # Nothing was eaten on the 17th, and today is the 18th.
    window = await service.fasting_window(user, date(2026, 8, 17), NOW)

    assert window.ongoing is True
    assert window.hours is not None
    # Madrid closes the 17th at 22:00 UTC, not at whatever time it is now.
    assert window.hours == Decimal("26.00")


async def test_the_first_meal_ever_has_no_fast_before_it(service: MealService) -> None:
    user = build_user()
    await eat(service, user, datetime(2026, 8, 18, 9, 0))

    window = await service.fasting_window(user, date(2026, 8, 18), NOW)

    assert window.hours is None
    assert window.started_at is None


async def test_a_day_with_nothing_at_all_reports_nothing(service: MealService) -> None:
    window = await service.fasting_window(build_user(), date(2026, 8, 18), NOW)

    assert window.hours is None
    assert window.ongoing is False
