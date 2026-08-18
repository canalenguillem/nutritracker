from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.models.meal import DailyLog


class ExerciseRepository(Protocol):
    async def add(self, exercise: Exercise) -> Exercise: ...

    async def get_for_user(self, user_id: UUID, exercise_id: UUID) -> Exercise | None: ...

    async def list_for_user(
        self, user_id: UUID, log_date: date | None = None
    ) -> list[Exercise]: ...

    async def remove(self, exercise: Exercise) -> None: ...


class SQLAlchemyExerciseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, exercise: Exercise) -> Exercise:
        self._session.add(exercise)
        await self._session.flush()
        return exercise

    async def get_for_user(self, user_id: UUID, exercise_id: UUID) -> Exercise | None:
        statement = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        exercise: Exercise | None = await self._session.scalar(statement)
        return exercise

    async def list_for_user(self, user_id: UUID, log_date: date | None = None) -> list[Exercise]:
        statement = select(Exercise).where(Exercise.user_id == user_id)
        if log_date is not None:
            statement = statement.join(Exercise.daily_log).where(DailyLog.log_date == log_date)
        statement = statement.order_by(Exercise.performed_at.desc())
        result = await self._session.scalars(statement)
        return list(result)

    async def remove(self, exercise: Exercise) -> None:
        await self._session.delete(exercise)
