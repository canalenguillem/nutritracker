from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.models.enums import MealSource, MealStatus, MealType
from app.models.meal import Meal, MealItem
from app.models.user import User
from app.repositories.daily_logs import DailyLogRepository
from app.repositories.meals import MealRepository
from app.services.daily_logs import naive_utc, resolve_daily_log

TWO_PLACES = Decimal("0.01")


class MealNotFoundError(Exception):
    pass


class EmptyMealError(Exception):
    pass


@dataclass(frozen=True)
class NewMealItem:
    name: str
    quantity: Decimal
    unit: str
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal


@dataclass(frozen=True)
class NewMeal:
    meal_type: MealType
    eaten_at: datetime
    items: list[NewMealItem]
    notes: str | None = None


@dataclass(frozen=True)
class MealChanges:
    meal_type: MealType | None = None
    eaten_at: datetime | None = None
    notes: str | None = None
    notes_provided: bool = False
    items: list[NewMealItem] | None = None


@dataclass(frozen=True)
class MealTotals:
    kcal: Decimal = Decimal("0")
    protein_g: Decimal = Decimal("0")
    fat_g: Decimal = Decimal("0")
    carbohydrates_g: Decimal = Decimal("0")


@dataclass(frozen=True)
class DailyTotals:
    log_date: date
    meal_count: int = 0
    totals: MealTotals = field(default_factory=MealTotals)


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _sum_items(items: list[MealItem]) -> MealTotals:
    return MealTotals(
        kcal=_round(sum((item.kcal for item in items), Decimal("0"))),
        protein_g=_round(sum((item.protein_g for item in items), Decimal("0"))),
        fat_g=_round(sum((item.fat_g for item in items), Decimal("0"))),
        carbohydrates_g=_round(sum((item.carbohydrates_g for item in items), Decimal("0"))),
    )


class MealService:
    def __init__(self, meals: MealRepository, daily_logs: DailyLogRepository) -> None:
        self._meals = meals
        self._daily_logs = daily_logs

    async def create_meal(self, user: User, data: NewMeal) -> Meal:
        if not data.items:
            raise EmptyMealError

        eaten_at = naive_utc(data.eaten_at)
        daily_log = await resolve_daily_log(self._daily_logs, user, eaten_at)
        meal = Meal(
            daily_log_id=daily_log.id,
            user_id=user.id,
            meal_type=data.meal_type,
            eaten_at=eaten_at,
            source=MealSource.MANUAL,
            # A meal the user typed needs no review; only AI estimates do.
            status=MealStatus.CONFIRMED,
            notes=_clean_notes(data.notes),
            items=[_to_item(item) for item in data.items],
        )
        _apply_totals(meal)
        return await self._meals.add(meal)

    async def list_meals(self, user: User, log_date: date | None = None) -> list[Meal]:
        return await self._meals.list_for_user(user.id, log_date)

    async def recent_meals(
        self, user: User, query: str | None = None, limit: int = 10
    ) -> list[Meal]:
        """The meals worth repeating, most recent first.

        The same dish eaten many times would otherwise fill the list, so only
        the latest of each combination of foods is kept.
        """
        candidates = await self._meals.list_recent_for_user(user.id, query, limit * 6)

        seen: set[tuple[str, ...]] = set()
        distinct: list[Meal] = []
        for meal in candidates:
            signature = tuple(sorted(item.name.strip().lower() for item in meal.items))
            if not signature or signature in seen:
                continue
            seen.add(signature)
            distinct.append(meal)
            if len(distinct) == limit:
                break

        return distinct

    async def get_meal(self, user: User, meal_id: UUID) -> Meal:
        meal = await self._meals.get_for_user(user.id, meal_id)
        if meal is None:
            raise MealNotFoundError(str(meal_id))
        return meal

    async def update_meal(self, user: User, meal_id: UUID, changes: MealChanges) -> Meal:
        meal = await self.get_meal(user, meal_id)

        if changes.items is not None:
            if not changes.items:
                raise EmptyMealError
            meal.items = [_to_item(item) for item in changes.items]
            _apply_totals(meal)

        if changes.meal_type is not None:
            meal.meal_type = changes.meal_type

        if changes.notes_provided:
            meal.notes = _clean_notes(changes.notes)

        if changes.eaten_at is not None:
            eaten_at = naive_utc(changes.eaten_at)
            meal.eaten_at = eaten_at
            daily_log = await resolve_daily_log(self._daily_logs, user, eaten_at)
            meal.daily_log_id = daily_log.id

        # Flush so replaced items carry their identifiers into the response.
        await self._meals.flush()
        return meal

    async def delete_meal(self, user: User, meal_id: UUID) -> None:
        meal = await self.get_meal(user, meal_id)
        await self._meals.remove(meal)

    async def daily_totals(self, user: User, log_date: date) -> DailyTotals:
        meals = await self._meals.list_for_user(user.id, log_date)
        return DailyTotals(
            log_date=log_date,
            meal_count=len(meals),
            totals=MealTotals(
                kcal=_round(sum((meal.total_kcal for meal in meals), Decimal("0"))),
                protein_g=_round(sum((meal.protein_g for meal in meals), Decimal("0"))),
                fat_g=_round(sum((meal.fat_g for meal in meals), Decimal("0"))),
                carbohydrates_g=_round(sum((meal.carbohydrates_g for meal in meals), Decimal("0"))),
            ),
        )


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    cleaned = notes.strip()
    return cleaned or None


def _to_item(data: NewMealItem) -> MealItem:
    return MealItem(
        name=data.name.strip(),
        quantity=_round(data.quantity),
        unit=data.unit.strip(),
        kcal=_round(data.kcal),
        protein_g=_round(data.protein_g),
        fat_g=_round(data.fat_g),
        carbohydrates_g=_round(data.carbohydrates_g),
        user_confirmed=True,
    )


def _apply_totals(meal: Meal) -> None:
    totals = _sum_items(meal.items)
    meal.total_kcal = totals.kcal
    meal.protein_g = totals.protein_g
    meal.fat_g = totals.fat_g
    meal.carbohydrates_g = totals.carbohydrates_g
