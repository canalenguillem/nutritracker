from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.enums import MealSource, MealStatus, MealType
from app.models.user import User
from app.services.meals import (
    EmptyMealError,
    MealChanges,
    MealNotFoundError,
    MealService,
    NewMeal,
    NewMealItem,
    local_log_date,
)
from fakes import FakeDailyLogRepository, FakeMealRepository

LUNCH_TIME = datetime(2026, 8, 18, 12, 30)


def build_user(timezone: str = "Europe/Madrid") -> User:
    return User(id=uuid4(), email="user@example.com", display_name="User", timezone=timezone)


def build_item(
    name: str = "Arroz",
    kcal: str = "130.00",
    protein: str = "2.70",
    fat: str = "0.30",
    carbohydrates: str = "28.00",
) -> NewMealItem:
    return NewMealItem(
        name=name,
        quantity=Decimal("100"),
        unit="g",
        kcal=Decimal(kcal),
        protein_g=Decimal(protein),
        fat_g=Decimal(fat),
        carbohydrates_g=Decimal(carbohydrates),
    )


@pytest.fixture
def service() -> MealService:
    daily_logs = FakeDailyLogRepository()
    return MealService(meals=FakeMealRepository(daily_logs=daily_logs), daily_logs=daily_logs)


async def test_create_meal_sums_the_item_totals(service: MealService) -> None:
    user = build_user()

    meal = await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.LUNCH,
            eaten_at=LUNCH_TIME,
            items=[build_item(), build_item(name="Pollo", kcal="165.00", protein="31.00")],
        ),
    )

    assert meal.total_kcal == Decimal("295.00")
    assert meal.protein_g == Decimal("33.70")
    assert meal.source is MealSource.MANUAL
    assert meal.status is MealStatus.CONFIRMED


async def test_create_meal_marks_typed_items_as_confirmed(service: MealService) -> None:
    meal = await service.create_meal(
        build_user(),
        NewMeal(meal_type=MealType.SNACK, eaten_at=LUNCH_TIME, items=[build_item()]),
    )

    assert all(item.user_confirmed for item in meal.items)


async def test_create_meal_rejects_a_meal_without_items(service: MealService) -> None:
    with pytest.raises(EmptyMealError):
        await service.create_meal(
            build_user(),
            NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[]),
        )


async def test_meals_of_the_same_day_share_a_daily_log(service: MealService) -> None:
    user = build_user()

    breakfast = await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.BREAKFAST,
            eaten_at=datetime(2026, 8, 18, 7, 15),
            items=[build_item()],
        ),
    )
    dinner = await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.DINNER,
            eaten_at=datetime(2026, 8, 18, 20, 45),
            items=[build_item()],
        ),
    )

    assert breakfast.daily_log_id == dinner.daily_log_id


async def test_a_meal_is_filed_under_the_local_day() -> None:
    # 23:30 UTC is already the next day in Madrid.
    assert local_log_date(datetime(2026, 8, 17, 23, 30), "Europe/Madrid") == date(2026, 8, 18)
    assert local_log_date(datetime(2026, 8, 17, 23, 30), "UTC") == date(2026, 8, 17)


async def test_an_unknown_timezone_falls_back_to_utc() -> None:
    assert local_log_date(datetime(2026, 8, 17, 23, 30), "Mars/Olympus") == date(2026, 8, 17)


async def test_an_offset_aware_time_is_stored_as_utc(service: MealService) -> None:
    meal = await service.create_meal(
        build_user(),
        NewMeal(
            meal_type=MealType.LUNCH,
            eaten_at=datetime(2026, 8, 18, 14, 30, tzinfo=UTC),
            items=[build_item()],
        ),
    )

    assert meal.eaten_at == datetime(2026, 8, 18, 14, 30)
    assert meal.eaten_at.tzinfo is None


async def test_listing_filters_by_local_day(service: MealService) -> None:
    user = build_user()
    await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.DINNER,
            eaten_at=datetime(2026, 8, 17, 20, 0),
            items=[build_item()],
        ),
    )
    await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.LUNCH,
            eaten_at=datetime(2026, 8, 18, 12, 0),
            items=[build_item()],
        ),
    )

    meals = await service.list_meals(user, date(2026, 8, 18))

    assert [meal.meal_type for meal in meals] == [MealType.LUNCH]


async def test_a_meal_belonging_to_another_user_is_not_found(service: MealService) -> None:
    owner = build_user()
    intruder = build_user()
    meal = await service.create_meal(
        owner,
        NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[build_item()]),
    )

    with pytest.raises(MealNotFoundError):
        await service.get_meal(intruder, meal.id)


async def test_updating_the_items_recomputes_the_totals(service: MealService) -> None:
    user = build_user()
    meal = await service.create_meal(
        user,
        NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[build_item()]),
    )

    updated = await service.update_meal(
        user, meal.id, MealChanges(items=[build_item(kcal="200.00")])
    )

    assert updated.total_kcal == Decimal("200.00")
    assert len(updated.items) == 1


async def test_updating_without_items_keeps_the_totals(service: MealService) -> None:
    user = build_user()
    meal = await service.create_meal(
        user,
        NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[build_item()]),
    )

    updated = await service.update_meal(user, meal.id, MealChanges(meal_type=MealType.DINNER))

    assert updated.meal_type is MealType.DINNER
    assert updated.total_kcal == Decimal("130.00")


async def test_moving_a_meal_to_another_day_moves_its_daily_log(service: MealService) -> None:
    user = build_user()
    meal = await service.create_meal(
        user,
        NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[build_item()]),
    )
    original_log_id = meal.daily_log_id

    updated = await service.update_meal(
        user, meal.id, MealChanges(eaten_at=datetime(2026, 8, 19, 12, 30))
    )

    assert updated.daily_log_id != original_log_id


async def test_clearing_the_notes_requires_an_explicit_change(service: MealService) -> None:
    user = build_user()
    meal = await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.LUNCH,
            eaten_at=LUNCH_TIME,
            items=[build_item()],
            notes="Con aceite de oliva",
        ),
    )

    untouched = await service.update_meal(user, meal.id, MealChanges(meal_type=MealType.DINNER))
    assert untouched.notes == "Con aceite de oliva"

    cleared = await service.update_meal(user, meal.id, MealChanges(notes=None, notes_provided=True))
    assert cleared.notes is None


async def test_deleting_a_meal_removes_it(service: MealService) -> None:
    user = build_user()
    meal = await service.create_meal(
        user,
        NewMeal(meal_type=MealType.LUNCH, eaten_at=LUNCH_TIME, items=[build_item()]),
    )

    await service.delete_meal(user, meal.id)

    with pytest.raises(MealNotFoundError):
        await service.get_meal(user, meal.id)


async def test_daily_totals_add_up_every_meal_of_the_day(service: MealService) -> None:
    user = build_user()
    await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.BREAKFAST,
            eaten_at=datetime(2026, 8, 18, 8, 0),
            items=[build_item()],
        ),
    )
    await service.create_meal(
        user,
        NewMeal(
            meal_type=MealType.LUNCH,
            eaten_at=datetime(2026, 8, 18, 14, 0),
            items=[build_item(kcal="165.00", protein="31.00")],
        ),
    )

    summary = await service.daily_totals(user, date(2026, 8, 18))

    assert summary.meal_count == 2
    assert summary.totals.kcal == Decimal("295.00")
    assert summary.totals.protein_g == Decimal("33.70")
