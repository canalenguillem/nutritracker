from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import DailyLog, Meal


class MealRepository(Protocol):
    async def add(self, meal: Meal) -> Meal: ...

    async def get_for_user(self, user_id: UUID, meal_id: UUID) -> Meal | None: ...

    async def list_for_user(self, user_id: UUID, log_date: date | None = None) -> list[Meal]: ...

    async def remove(self, meal: Meal) -> None: ...

    async def flush(self) -> None: ...


class SQLAlchemyMealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, meal: Meal) -> Meal:
        self._session.add(meal)
        await self._session.flush()
        return meal

    async def get_for_user(self, user_id: UUID, meal_id: UUID) -> Meal | None:
        # Scoping by user in the query keeps another user's meal indistinguishable
        # from one that does not exist.
        statement = select(Meal).where(Meal.id == meal_id, Meal.user_id == user_id)
        meal: Meal | None = await self._session.scalar(statement)
        return meal

    async def list_for_user(self, user_id: UUID, log_date: date | None = None) -> list[Meal]:
        statement = select(Meal).where(Meal.user_id == user_id)
        if log_date is not None:
            statement = statement.join(Meal.daily_log).where(DailyLog.log_date == log_date)
        statement = statement.order_by(Meal.eaten_at.desc())
        result = await self._session.scalars(statement)
        return list(result)

    async def remove(self, meal: Meal) -> None:
        # Deleting through the session lets the ORM cascade reach the meal items.
        await self._session.delete(meal)

    async def flush(self) -> None:
        await self._session.flush()
