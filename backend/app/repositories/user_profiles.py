from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserProfile


class UserProfileRepository(Protocol):
    async def get_for_user(self, user_id: UUID) -> UserProfile | None: ...

    async def add(self, profile: UserProfile) -> UserProfile: ...


class SQLAlchemyUserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_user(self, user_id: UUID) -> UserProfile | None:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        profile: UserProfile | None = await self._session.scalar(statement)
        return profile

    async def add(self, profile: UserProfile) -> UserProfile:
        self._session.add(profile)
        await self._session.flush()
        return profile
