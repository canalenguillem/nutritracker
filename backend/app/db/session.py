from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    database_url = URL.create(
        drivername="mysql+asyncmy",
        username=settings.mariadb_user,
        password=settings.mariadb_password.get_secret_value(),
        host=settings.mariadb_host,
        port=settings.mariadb_port,
        database=settings.mariadb_database,
    )
    return create_async_engine(database_url, pool_pre_ping=True)
