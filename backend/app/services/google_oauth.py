import logging

from authlib.integrations.httpx_client import AsyncOAuth2Client  # type: ignore[import-untyped]

from app.core.config import Settings
from app.services.auth import GoogleAccount
from app.services.oauth_state import OAuthStateStore

logger = logging.getLogger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPE = "openid email profile"


class GoogleOAuthDisabledError(Exception):
    pass


class InvalidOAuthStateError(Exception):
    pass


class GoogleOAuthError(Exception):
    pass


class GoogleOAuthService:
    def __init__(self, settings: Settings, state_store: OAuthStateStore) -> None:
        self._settings = settings
        self._state_store = state_store

    @property
    def enabled(self) -> bool:
        return self._settings.google_oauth_enabled

    async def create_authorization_url(self) -> str:
        self._ensure_enabled()
        state = await self._state_store.issue()
        async with self._create_client() as client:
            authorization_url, _ = client.create_authorization_url(
                GOOGLE_AUTHORIZE_URL,
                state=state,
                access_type="offline",
                prompt="select_account",
            )
        return str(authorization_url)

    async def exchange_code(self, code: str, state: str) -> GoogleAccount:
        self._ensure_enabled()
        if not await self._state_store.consume(state):
            raise InvalidOAuthStateError

        try:
            async with self._create_client() as client:
                await client.fetch_token(
                    GOOGLE_TOKEN_URL,
                    code=code,
                    grant_type="authorization_code",
                )
                response = await client.get(GOOGLE_USERINFO_URL)
                response.raise_for_status()
                profile = response.json()
        except Exception as error:
            logger.warning(
                "google_oauth_exchange_failed", extra={"error_type": type(error).__name__}
            )
            raise GoogleOAuthError from error

        email = profile.get("email")
        subject = profile.get("sub")
        if not email or not subject:
            raise GoogleOAuthError("Google did not return an email address")

        return GoogleAccount(
            provider_user_id=str(subject),
            email=str(email),
            display_name=str(profile.get("name") or email),
            avatar_url=profile.get("picture"),
            email_verified=bool(profile.get("email_verified")),
        )

    def _create_client(self) -> AsyncOAuth2Client:
        return AsyncOAuth2Client(
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret.get_secret_value(),
            redirect_uri=str(self._settings.google_redirect_uri),
            scope=GOOGLE_SCOPE,
            timeout=10.0,
        )

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise GoogleOAuthDisabledError
