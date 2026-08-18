import secrets
from typing import Protocol

from redis.asyncio import Redis

STATE_KEY_PREFIX = "oauth:state:"
STATE_TTL_SECONDS = 600


class OAuthStateStore(Protocol):
    async def issue(self) -> str: ...

    async def consume(self, state: str) -> bool: ...


class RedisOAuthStateStore:
    def __init__(self, client: Redis, ttl_seconds: int = STATE_TTL_SECONDS) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    async def issue(self) -> str:
        state = secrets.token_urlsafe(32)
        await self._client.set(f"{STATE_KEY_PREFIX}{state}", "1", ex=self._ttl_seconds)
        return state

    async def consume(self, state: str) -> bool:
        if not state:
            return False
        deleted = await self._client.delete(f"{STATE_KEY_PREFIX}{state}")
        return bool(deleted)
