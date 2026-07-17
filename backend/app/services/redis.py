from typing import cast

from redis.asyncio import Redis

from app.core.config import Settings


def create_redis_client(settings: Settings) -> Redis:
    return cast(
        Redis,
        Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=settings.healthcheck_timeout_seconds,
            socket_timeout=settings.healthcheck_timeout_seconds,
        ),
    )
