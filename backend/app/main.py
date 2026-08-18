from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import create_database_engine, create_session_factory
from app.repositories.health import MariaDBHealthRepository, RedisHealthRepository
from app.services.health import HealthService
from app.services.redis import create_redis_client


def create_app(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()
    configure_logging(application_settings.log_level)

    database_engine = create_database_engine(application_settings)
    session_factory = create_session_factory(database_engine)
    redis_client = create_redis_client(application_settings)
    health_service = HealthService(
        repositories=(
            MariaDBHealthRepository(database_engine),
            RedisHealthRepository(redis_client),
        ),
        timeout_seconds=application_settings.healthcheck_timeout_seconds,
        app_name=application_settings.app_name,
        environment=application_settings.app_env,
        version=application_settings.app_version,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await redis_client.aclose()
        await database_engine.dispose()

    application = FastAPI(
        title=application_settings.app_name,
        version=application_settings.app_version,
        docs_url=f"{application_settings.api_v1_prefix}/docs",
        openapi_url=f"{application_settings.api_v1_prefix}/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.health_service = health_service
    application.state.redis_client = redis_client
    application.state.session_factory = session_factory
    application.state.settings = application_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    register_error_handlers(application)
    application.include_router(api_router, prefix=application_settings.api_v1_prefix)

    return application


app = create_app()
