from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.user import RefreshToken


class RefreshTokenRepository(Protocol):
    async def add(self, refresh_token: RefreshToken) -> RefreshToken: ...

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every active session and commit, even if the request then fails."""
        ...


class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        self._session.add(refresh_token)
        await self._session.flush()
        return refresh_token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        refresh_token: RefreshToken | None = await self._session.scalar(statement)
        return refresh_token

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        statement = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
        await self._session.execute(statement)
        # This runs while answering a request that ends in an error, so it has to
        # commit on its own: the caller's transaction is about to be rolled back.
        await self._session.commit()
