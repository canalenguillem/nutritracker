from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weight import WeightEntry


class WeightRepository(Protocol):
    async def add(self, entry: WeightEntry) -> WeightEntry: ...

    async def get_for_user(self, user_id: UUID, entry_id: UUID) -> WeightEntry | None: ...

    async def list_for_user(self, user_id: UUID) -> list[WeightEntry]: ...

    async def remove(self, entry: WeightEntry) -> None: ...


class SQLAlchemyWeightRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: WeightEntry) -> WeightEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_for_user(self, user_id: UUID, entry_id: UUID) -> WeightEntry | None:
        statement = select(WeightEntry).where(
            WeightEntry.id == entry_id, WeightEntry.user_id == user_id
        )
        entry: WeightEntry | None = await self._session.scalar(statement)
        return entry

    async def list_for_user(self, user_id: UUID) -> list[WeightEntry]:
        statement = (
            select(WeightEntry)
            .where(WeightEntry.user_id == user_id)
            .order_by(WeightEntry.measured_at.asc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def remove(self, entry: WeightEntry) -> None:
        await self._session.delete(entry)
