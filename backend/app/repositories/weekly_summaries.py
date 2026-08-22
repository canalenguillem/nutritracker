from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.week import WeeklySummary


class WeeklySummaryRepository(Protocol):
    async def add(self, summary: WeeklySummary) -> WeeklySummary: ...

    async def get_for_week(self, user_id: UUID, week_start: date) -> WeeklySummary | None: ...

    async def remove(self, summary: WeeklySummary) -> None: ...


class SQLAlchemyWeeklySummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, summary: WeeklySummary) -> WeeklySummary:
        self._session.add(summary)
        await self._session.flush()
        return summary

    async def get_for_week(self, user_id: UUID, week_start: date) -> WeeklySummary | None:
        statement = select(WeeklySummary).where(
            WeeklySummary.user_id == user_id, WeeklySummary.week_start == week_start
        )
        summary: WeeklySummary | None = await self._session.scalar(statement)
        return summary

    async def remove(self, summary: WeeklySummary) -> None:
        await self._session.delete(summary)
