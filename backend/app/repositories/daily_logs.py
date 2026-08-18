from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import DailyLog


class DailyLogRepository(Protocol):
    async def add(self, daily_log: DailyLog) -> DailyLog: ...

    async def get_by_date(self, user_id: UUID, log_date: date) -> DailyLog | None: ...


class SQLAlchemyDailyLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, daily_log: DailyLog) -> DailyLog:
        self._session.add(daily_log)
        await self._session.flush()
        return daily_log

    async def get_by_date(self, user_id: UUID, log_date: date) -> DailyLog | None:
        statement = select(DailyLog).where(
            DailyLog.user_id == user_id, DailyLog.log_date == log_date
        )
        daily_log: DailyLog | None = await self._session.scalar(statement)
        return daily_log
