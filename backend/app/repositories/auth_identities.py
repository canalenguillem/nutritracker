from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuthProvider
from app.models.user import AuthIdentity


class AuthIdentityRepository(Protocol):
    async def add(self, identity: AuthIdentity) -> AuthIdentity: ...

    async def get_by_provider_user_id(
        self, provider: AuthProvider, provider_user_id: str
    ) -> AuthIdentity | None: ...


class SQLAlchemyAuthIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, identity: AuthIdentity) -> AuthIdentity:
        self._session.add(identity)
        await self._session.flush()
        return identity

    async def get_by_provider_user_id(
        self, provider: AuthProvider, provider_user_id: str
    ) -> AuthIdentity | None:
        statement = select(AuthIdentity).where(
            AuthIdentity.provider == provider,
            AuthIdentity.provider_user_id == provider_user_id,
        )
        identity: AuthIdentity | None = await self._session.scalar(statement)
        return identity
