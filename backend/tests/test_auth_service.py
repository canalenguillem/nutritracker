from datetime import timedelta

import pytest

from app.core.config import Settings
from app.models.base import utc_now
from app.models.enums import AuthProvider, UserStatus
from app.security.tokens import decode_access_token, hash_refresh_token
from app.services.auth import (
    AuthService,
    GoogleAccount,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RequestContext,
)
from app.services.users import UserService
from fakes import FakeAuthIdentityRepository, FakeRefreshTokenRepository, FakeUserRepository

CONTEXT = RequestContext(user_agent="pytest", ip_address="10.0.0.1")


@pytest.fixture
def settings() -> Settings:
    return Settings(app_env="test", jwt_secret_key="unit-test-secret-key-value-32-chars")


@pytest.fixture
def users() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def refresh_tokens() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def identities() -> FakeAuthIdentityRepository:
    return FakeAuthIdentityRepository()


@pytest.fixture
def service(
    users: FakeUserRepository,
    refresh_tokens: FakeRefreshTokenRepository,
    identities: FakeAuthIdentityRepository,
    settings: Settings,
) -> AuthService:
    return AuthService(
        users=UserService(users),
        refresh_tokens=refresh_tokens,
        identities=identities,
        settings=settings,
    )


async def register_user(
    service: AuthService, email: str = "user@example.com", password: str = "secret-password"
) -> None:
    await service.register(
        email=email, display_name="Test User", password=password, context=CONTEXT
    )


async def test_register_stores_hashed_password_and_local_identity(
    service: AuthService,
    users: FakeUserRepository,
    identities: FakeAuthIdentityRepository,
    settings: Settings,
) -> None:
    session = await service.register(
        email="USER@Example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )

    stored_user = users.users[0]
    assert stored_user.email == "user@example.com"
    assert stored_user.password_hash is not None
    assert "secret-password" not in stored_user.password_hash
    assert stored_user.last_login_at is not None
    assert identities.identities[0].provider is AuthProvider.LOCAL
    assert decode_access_token(session.access_token, settings) == stored_user.id


async def test_register_never_stores_the_raw_refresh_token(
    service: AuthService, refresh_tokens: FakeRefreshTokenRepository
) -> None:
    session = await service.register(
        email="user@example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )

    stored_token = refresh_tokens.tokens[0]
    assert stored_token.token_hash != session.refresh_token
    assert stored_token.token_hash == hash_refresh_token(session.refresh_token)
    assert stored_token.user_agent == "pytest"
    assert stored_token.ip_hash is not None
    assert stored_token.ip_hash != "10.0.0.1"


async def test_login_accepts_valid_credentials_and_records_the_login(
    service: AuthService, users: FakeUserRepository
) -> None:
    await register_user(service)
    users.users[0].last_login_at = None

    session = await service.login("USER@example.com", "secret-password", CONTEXT)

    assert session.user.email == "user@example.com"
    assert users.users[0].last_login_at is not None


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("user@example.com", "wrong-password"),
        ("unknown@example.com", "secret-password"),
    ],
)
async def test_login_rejects_bad_credentials(
    service: AuthService, email: str, password: str
) -> None:
    await register_user(service)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email, password, CONTEXT)


async def test_login_rejects_accounts_without_a_password(
    service: AuthService, users: FakeUserRepository
) -> None:
    await register_user(service)
    users.users[0].password_hash = None

    with pytest.raises(InvalidCredentialsError):
        await service.login("user@example.com", "secret-password", CONTEXT)


async def test_login_rejects_inactive_accounts(
    service: AuthService, users: FakeUserRepository
) -> None:
    await register_user(service)
    users.users[0].status = UserStatus.INACTIVE

    with pytest.raises(InactiveUserError):
        await service.login("user@example.com", "secret-password", CONTEXT)


async def test_refresh_rotates_the_stored_token(
    service: AuthService, refresh_tokens: FakeRefreshTokenRepository
) -> None:
    first = await service.register(
        email="user@example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )

    second = await service.refresh(first.refresh_token, CONTEXT)

    assert second.refresh_token != first.refresh_token
    assert refresh_tokens.tokens[0].revoked_at is not None
    assert refresh_tokens.tokens[1].revoked_at is None


async def test_refresh_revokes_every_session_when_a_used_token_is_replayed(
    service: AuthService, refresh_tokens: FakeRefreshTokenRepository
) -> None:
    first = await service.register(
        email="user@example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )
    await service.refresh(first.refresh_token, CONTEXT)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(first.refresh_token, CONTEXT)

    assert all(token.revoked_at is not None for token in refresh_tokens.tokens)


async def test_refresh_rejects_expired_tokens(
    service: AuthService, refresh_tokens: FakeRefreshTokenRepository
) -> None:
    session = await service.register(
        email="user@example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )
    refresh_tokens.tokens[0].expires_at = utc_now() - timedelta(seconds=1)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(session.refresh_token, CONTEXT)


async def test_refresh_rejects_unknown_tokens(service: AuthService) -> None:
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh("not-a-real-token", CONTEXT)


async def test_logout_revokes_the_presented_token(
    service: AuthService, refresh_tokens: FakeRefreshTokenRepository
) -> None:
    session = await service.register(
        email="user@example.com",
        display_name="Test User",
        password="secret-password",
        context=CONTEXT,
    )

    await service.logout(session.refresh_token)

    assert refresh_tokens.tokens[0].revoked_at is not None
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(session.refresh_token, CONTEXT)


async def test_logout_without_a_token_is_a_no_op(service: AuthService) -> None:
    await service.logout(None)


async def test_google_login_creates_a_user_without_a_password(
    service: AuthService, users: FakeUserRepository, identities: FakeAuthIdentityRepository
) -> None:
    account = GoogleAccount(
        provider_user_id="google-123",
        email="new@example.com",
        display_name="New User",
        avatar_url="https://example.com/avatar.png",
        email_verified=True,
    )

    session = await service.login_with_google(account, CONTEXT)

    assert session.user.password_hash is None
    assert session.user.avatar_url == "https://example.com/avatar.png"
    assert session.user.email_verified_at is not None
    assert identities.identities[0].provider is AuthProvider.GOOGLE
    assert len(users.users) == 1


async def test_google_login_reuses_the_linked_identity(
    service: AuthService, users: FakeUserRepository, identities: FakeAuthIdentityRepository
) -> None:
    account = GoogleAccount(
        provider_user_id="google-123",
        email="new@example.com",
        display_name="New User",
        email_verified=True,
    )
    first = await service.login_with_google(account, CONTEXT)

    second = await service.login_with_google(account, CONTEXT)

    assert second.user.id == first.user.id
    assert len(users.users) == 1
    assert len(identities.identities) == 1


async def test_google_login_links_a_verified_address_to_an_existing_account(
    service: AuthService, users: FakeUserRepository, identities: FakeAuthIdentityRepository
) -> None:
    await register_user(service)
    account = GoogleAccount(
        provider_user_id="google-123",
        email="user@example.com",
        display_name="Test User",
        email_verified=True,
    )

    session = await service.login_with_google(account, CONTEXT)

    assert session.user.id == users.users[0].id
    assert len(users.users) == 1
    assert {identity.provider for identity in identities.identities} == {
        AuthProvider.LOCAL,
        AuthProvider.GOOGLE,
    }


async def test_google_login_refuses_to_link_an_unverified_address(service: AuthService) -> None:
    await register_user(service)
    account = GoogleAccount(
        provider_user_id="google-123",
        email="user@example.com",
        display_name="Test User",
        email_verified=False,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.login_with_google(account, CONTEXT)
