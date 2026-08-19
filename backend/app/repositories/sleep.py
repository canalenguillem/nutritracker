from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sleep import SleepEntry


class SleepRepository(Protocol):
    async def add(self, entry: SleepEntry) -> SleepEntry: ...

    async def get_for_user(self, user_id: UUID, entry_id: UUID) -> SleepEntry | None: ...

    async def list_between(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> list[SleepEntry]: ...

    async def remove(self, entry: SleepEntry) -> None: ...


class SQLAlchemySleepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: SleepEntry) -> SleepEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_for_user(self, user_id: UUID, entry_id: UUID) -> SleepEntry | None:
        statement = select(SleepEntry).where(
            SleepEntry.id == entry_id, SleepEntry.user_id == user_id
        )
        entry: SleepEntry | None = await self._session.scalar(statement)
        return entry

    async def list_between(self, user_id: UUID, start: datetime, end: datetime) -> list[SleepEntry]:
        """Nights that ended within the window, since that is the day they belong to."""
        statement = (
            select(SleepEntry)
            .where(
                SleepEntry.user_id == user_id,
                SleepEntry.ended_at >= start,
                SleepEntry.ended_at < end,
            )
            .order_by(SleepEntry.ended_at.desc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def remove(self, entry: SleepEntry) -> None:
        await self._session.delete(entry)
