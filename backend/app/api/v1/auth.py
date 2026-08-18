from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import (
    AuthServiceDependency,
    CurrentUserDependency,
    GoogleOAuthServiceDependency,
    RequestContextDependency,
    SettingsDependency,
)
from app.core.config import Settings
from app.schemas.auth import LoginRequest, RegisterRequest, SessionResponse, UserResponse
from app.services.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    IssuedSession,
    RegistrationClosedError,
)
from app.services.google_oauth import (
    GoogleOAuthDisabledError,
    GoogleOAuthError,
    InvalidOAuthStateError,
)
from app.services.users import UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "nutritrack_refresh_token"

RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)]


def _refresh_cookie_path(settings: Settings) -> str:
    return f"{settings.api_v1_prefix}/auth"


def _set_refresh_cookie(response: Response, session: IssuedSession, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=session.refresh_token,
        max_age=settings.jwt_refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path=_refresh_cookie_path(settings),
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path=_refresh_cookie_path(settings),
    )


def _session_response(session: IssuedSession) -> SessionResponse:
    return SessionResponse(
        access_token=session.access_token,
        expires_in=session.expires_in,
        user=UserResponse.model_validate(session.user),
    )


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthServiceDependency,
    context: RequestContextDependency,
    settings: SettingsDependency,
) -> SessionResponse:
    if not settings.registration_open:
        raise _registration_closed()

    try:
        session = await service.register(
            email=payload.email,
            display_name=payload.display_name,
            password=payload.password,
            context=context,
        )
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address.",
        ) from error

    _set_refresh_cookie(response, session, settings)
    return _session_response(session)


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthServiceDependency,
    context: RequestContextDependency,
    settings: SettingsDependency,
) -> SessionResponse:
    try:
        session = await service.login(
            email=payload.email, password=payload.password, context=context
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email address or password is incorrect.",
        ) from error
    except InactiveUserError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account is not active."
        ) from error

    _set_refresh_cookie(response, session, settings)
    return _session_response(session)


@router.post("/refresh", response_model=SessionResponse)
async def refresh(
    response: Response,
    service: AuthServiceDependency,
    context: RequestContextDependency,
    settings: SettingsDependency,
    refresh_token: RefreshCookie = None,
) -> SessionResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The refresh token is missing."
        )

    try:
        session = await service.refresh(refresh_token, context)
    except (InvalidRefreshTokenError, InactiveUserError) as error:
        _clear_refresh_cookie(response, settings)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The refresh token is invalid or has expired.",
        ) from error

    _set_refresh_cookie(response, session, settings)
    return _session_response(session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: AuthServiceDependency,
    settings: SettingsDependency,
    refresh_token: RefreshCookie = None,
) -> None:
    await service.logout(refresh_token)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserResponse)
async def read_current_user(user: CurrentUserDependency) -> UserResponse:
    return UserResponse.model_validate(user)


@router.get("/google/login")
async def google_login(service: GoogleOAuthServiceDependency) -> RedirectResponse:
    try:
        authorization_url = await service.create_authorization_url()
    except GoogleOAuthDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        ) from error
    return RedirectResponse(authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/google/callback")
async def google_callback(
    google: GoogleOAuthServiceDependency,
    service: AuthServiceDependency,
    context: RequestContextDependency,
    settings: SettingsDependency,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if error or not code or not state:
        return _frontend_redirect(settings, error or "missing_authorization_code")

    try:
        account = await google.exchange_code(code, state)
        session = await service.login_with_google(account, context)
    except InvalidOAuthStateError:
        return _frontend_redirect(settings, "invalid_state")
    except (GoogleOAuthDisabledError, GoogleOAuthError):
        return _frontend_redirect(settings, "google_exchange_failed")
    except InvalidCredentialsError:
        return _frontend_redirect(settings, "email_already_registered")
    except RegistrationClosedError:
        return _frontend_redirect(settings, "registration_closed")
    except InactiveUserError:
        return _frontend_redirect(settings, "account_inactive")

    response = _frontend_redirect(settings)
    _set_refresh_cookie(response, session, settings)
    return response


def _registration_closed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="New accounts are closed for now.",
    )


def _frontend_redirect(settings: Settings, error: str | None = None) -> RedirectResponse:
    target = f"{settings.frontend_url.rstrip('/')}/auth/callback"
    if error:
        target = f"{target}?error={error}"
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)
