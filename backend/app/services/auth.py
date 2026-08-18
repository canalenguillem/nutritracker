import logging
from dataclasses import dataclass
from datetime import datetime

from app.core.config import Settings
from app.models.base import utc_now
from app.models.enums import AuthProvider, UserStatus
from app.models.user import AuthIdentity, RefreshToken, User
from app.repositories.auth_identities import AuthIdentityRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    create_access_token,
    create_refresh_token,
    hash_ip_address,
    hash_refresh_token,
)
from app.services.users import NewUser, UserService

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class RegistrationClosedError(Exception):
    pass


@dataclass(frozen=True)
class RequestContext:
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass(frozen=True)
class GoogleAccount:
    provider_user_id: str
    email: str
    display_name: str
    avatar_url: str | None = None
    email_verified: bool = False


@dataclass(frozen=True)
class IssuedSession:
    user: User
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_at: datetime


class AuthService:
    def __init__(
        self,
        users: UserService,
        refresh_tokens: RefreshTokenRepository,
        identities: AuthIdentityRepository,
        settings: Settings,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._identities = identities
        self._settings = settings

    async def register(
        self, email: str, display_name: str, password: str, context: RequestContext
    ) -> IssuedSession:
        user = await self._users.create_user(
            NewUser(
                email=email,
                display_name=display_name,
                password_hash=hash_password(password),
            )
        )
        await self._identities.add(
            AuthIdentity(
                user_id=user.id,
                provider=AuthProvider.LOCAL,
                provider_user_id=str(user.id),
                provider_email=user.email,
            )
        )
        await self._users.record_login(user)
        return await self._issue_session(user, context)

    async def login(self, email: str, password: str, context: RequestContext) -> IssuedSession:
        user = await self._users.get_by_email(email)
        if user is None or user.password_hash is None:
            raise InvalidCredentialsError(email)
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError(email)

        self._ensure_active(user)
        await self._users.record_login(user)
        return await self._issue_session(user, context)

    async def login_with_google(
        self, account: GoogleAccount, context: RequestContext
    ) -> IssuedSession:
        identity = await self._identities.get_by_provider_user_id(
            AuthProvider.GOOGLE, account.provider_user_id
        )
        user = (
            await self._users.get_by_id(identity.user_id)
            if identity is not None
            else await self._link_or_create_google_user(account)
        )

        self._ensure_active(user)
        await self._users.record_login(user)
        return await self._issue_session(user, context)

    async def refresh(self, raw_token: str, context: RequestContext) -> IssuedSession:
        stored_token = await self._refresh_tokens.get_by_hash(hash_refresh_token(raw_token))
        if stored_token is None:
            raise InvalidRefreshTokenError

        if stored_token.revoked_at is not None:
            # A revoked token being replayed means the secret leaked: drop every session.
            logger.warning(
                "refresh_token_reuse_detected", extra={"user_id": str(stored_token.user_id)}
            )
            await self._refresh_tokens.revoke_all_for_user(stored_token.user_id)
            raise InvalidRefreshTokenError

        if stored_token.expires_at <= utc_now():
            raise InvalidRefreshTokenError

        stored_token.revoked_at = utc_now()
        user = await self._users.get_by_id(stored_token.user_id)
        self._ensure_active(user)
        return await self._issue_session(user, context)

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        stored_token = await self._refresh_tokens.get_by_hash(hash_refresh_token(raw_token))
        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = utc_now()

    async def _link_or_create_google_user(self, account: GoogleAccount) -> User:
        user = await self._users.get_by_email(account.email)
        if user is not None and not account.email_verified:
            # Linking by an unverified address would let anyone claim an existing account.
            raise InvalidCredentialsError(account.email)

        if user is None:
            # Signing in with Google creates an account, so it obeys the same gate.
            if not self._settings.registration_open:
                raise RegistrationClosedError(account.email)
            user = await self._users.create_user(
                NewUser(
                    email=account.email,
                    display_name=account.display_name,
                    avatar_url=account.avatar_url,
                    email_verified=account.email_verified,
                )
            )

        await self._identities.add(
            AuthIdentity(
                user_id=user.id,
                provider=AuthProvider.GOOGLE,
                provider_user_id=account.provider_user_id,
                provider_email=account.email,
            )
        )
        return user

    async def _issue_session(self, user: User, context: RequestContext) -> IssuedSession:
        access_token, expires_in = create_access_token(user.id, self._settings)
        raw_refresh_token, token_hash, expires_at = create_refresh_token(self._settings)
        await self._refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                user_agent=context.user_agent[:512] if context.user_agent else None,
                ip_hash=hash_ip_address(context.ip_address),
            )
        )
        return IssuedSession(
            user=user,
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=raw_refresh_token,
            refresh_expires_at=expires_at,
        )

    @staticmethod
    def _ensure_active(user: User) -> None:
        if user.status is not UserStatus.ACTIVE:
            raise InactiveUserError(str(user.id))
