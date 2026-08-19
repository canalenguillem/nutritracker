from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.enums import UserStatus
from app.models.user import User
from app.repositories.auth_identities import SQLAlchemyAuthIdentityRepository
from app.repositories.daily_logs import SQLAlchemyDailyLogRepository
from app.repositories.exercises import SQLAlchemyExerciseRepository
from app.repositories.meals import SQLAlchemyMealRepository
from app.repositories.refresh_tokens import SQLAlchemyRefreshTokenRepository
from app.repositories.sleep import SQLAlchemySleepRepository
from app.repositories.user_profiles import SQLAlchemyUserProfileRepository
from app.repositories.users import SQLAlchemyUserRepository
from app.repositories.weights import SQLAlchemyWeightRepository
from app.security.tokens import TokenValidationError, decode_access_token
from app.services.auth import AuthService, RequestContext
from app.services.exercises import ExerciseService
from app.services.food_analysis import FoodAnalysisService
from app.services.food_estimate_cache import RedisFoodEstimateCache
from app.services.google_oauth import GoogleOAuthService
from app.services.meals import MealService
from app.services.met_cache import RedisMetCache
from app.services.met_lookup import OpenAIMetLookup
from app.services.oauth_state import RedisOAuthStateStore
from app.services.openai_food_analyzer import OpenAIFoodAnalyzer
from app.services.profiles import ProfileService
from app.services.sleep import SleepService
from app.services.users import UserNotFoundError, UserService
from app.services.weights import WeightService

bearer_scheme = HTTPBearer(auto_error=False)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


def get_app_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    return settings if isinstance(settings, Settings) else get_settings()


SettingsDependency = Annotated[Settings, Depends(get_app_settings)]


def get_user_service(session: SessionDependency) -> UserService:
    return UserService(SQLAlchemyUserRepository(session))


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(
    session: SessionDependency,
    users: UserServiceDependency,
    settings: SettingsDependency,
) -> AuthService:
    return AuthService(
        users=users,
        refresh_tokens=SQLAlchemyRefreshTokenRepository(session),
        identities=SQLAlchemyAuthIdentityRepository(session),
        settings=settings,
    )


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


def get_meal_service(session: SessionDependency) -> MealService:
    return MealService(
        meals=SQLAlchemyMealRepository(session),
        daily_logs=SQLAlchemyDailyLogRepository(session),
    )


MealServiceDependency = Annotated[MealService, Depends(get_meal_service)]


def get_exercise_service(
    request: Request, session: SessionDependency, settings: SettingsDependency
) -> ExerciseService:
    return ExerciseService(
        exercises=SQLAlchemyExerciseRepository(session),
        daily_logs=SQLAlchemyDailyLogRepository(session),
        profiles=SQLAlchemyUserProfileRepository(session),
        # Only consulted for an activity the published table does not cover.
        met_lookup=OpenAIMetLookup(settings) if settings.food_analysis_enabled else None,
        met_cache=RedisMetCache(request.app.state.redis_client),
    )


ExerciseServiceDependency = Annotated[ExerciseService, Depends(get_exercise_service)]


def get_sleep_service(session: SessionDependency) -> SleepService:
    return SleepService(SQLAlchemySleepRepository(session))


SleepServiceDependency = Annotated[SleepService, Depends(get_sleep_service)]


def get_profile_service(session: SessionDependency) -> ProfileService:
    return ProfileService(SQLAlchemyUserProfileRepository(session))


ProfileServiceDependency = Annotated[ProfileService, Depends(get_profile_service)]


def get_weight_service(session: SessionDependency) -> WeightService:
    return WeightService(
        weights=SQLAlchemyWeightRepository(session),
        profiles=SQLAlchemyUserProfileRepository(session),
    )


WeightServiceDependency = Annotated[WeightService, Depends(get_weight_service)]


def get_food_analysis_service(
    request: Request, settings: SettingsDependency
) -> FoodAnalysisService:
    cache = RedisFoodEstimateCache(
        request.app.state.redis_client,
        model=settings.openai_model,
        prompt_version=settings.openai_prompt_version,
    )
    analyzer = OpenAIFoodAnalyzer(settings) if settings.food_analysis_enabled else None
    return FoodAnalysisService(analyzer, cache)


FoodAnalysisServiceDependency = Annotated[FoodAnalysisService, Depends(get_food_analysis_service)]


def get_google_oauth_service(request: Request, settings: SettingsDependency) -> GoogleOAuthService:
    return GoogleOAuthService(settings, RedisOAuthStateStore(request.app.state.redis_client))


GoogleOAuthServiceDependency = Annotated[GoogleOAuthService, Depends(get_google_oauth_service)]


def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


RequestContextDependency = Annotated[RequestContext, Depends(get_request_context)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    users: UserServiceDependency,
    settings: SettingsDependency,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(credentials.credentials, settings)
        user = await users.get_by_id(user_id)
    except (TokenValidationError, UserNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    if user.status is not UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]
