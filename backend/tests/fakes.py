from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.models.base import utc_now
from app.models.enums import AuthProvider, UserRole, UserStatus
from app.models.user import AuthIdentity, RefreshToken, User


@dataclass
class FakeUserRepository:
    users: list[User] = field(default_factory=list)

    async def add(self, user: User) -> User:
        # Mirrors the column defaults SQLAlchemy would apply on flush.
        user.id = user.id or uuid4()
        user.role = user.role or UserRole.USER
        user.status = user.status or UserStatus.ACTIVE
        self.users.append(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        return next((user for user in self.users if user.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((user for user in self.users if user.id == user_id), None)


@dataclass
class FakeRefreshTokenRepository:
    tokens: list[RefreshToken] = field(default_factory=list)

    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.id = refresh_token.id or uuid4()
        refresh_token.created_at = refresh_token.created_at or utc_now()
        self.tokens.append(refresh_token)
        return refresh_token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((token for token in self.tokens if token.token_hash == token_hash), None)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for token in self.tokens:
            if token.user_id == user_id and token.revoked_at is None:
                token.revoked_at = utc_now()


@dataclass
class FakeAuthIdentityRepository:
    identities: list[AuthIdentity] = field(default_factory=list)

    async def add(self, identity: AuthIdentity) -> AuthIdentity:
        identity.id = identity.id or uuid4()
        self.identities.append(identity)
        return identity

    async def get_by_provider_user_id(
        self, provider: AuthProvider, provider_user_id: str
    ) -> AuthIdentity | None:
        return next(
            (
                identity
                for identity in self.identities
                if identity.provider is provider and identity.provider_user_id == provider_user_id
            ),
            None,
        )
