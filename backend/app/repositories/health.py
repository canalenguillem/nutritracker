from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class HealthRepository(Protocol):
    @property
    def name(self) -> str: ...

    async def ping(self) -> None: ...


class MariaDBHealthRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @property
    def name(self) -> str:
        return "mariadb"

    async def ping(self) -> None:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


class RedisHealthRepository:
    def __init__(self, client: Redis) -> None:
        self._client = client

    @property
    def name(self) -> str:
        return "redis"

    async def ping(self) -> None:
        await self._client.ping()
