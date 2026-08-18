import hashlib
import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "activity:met:"
# A metabolic equivalent is a stable fact, so it can be kept for a long time.
CACHE_TTL_SECONDS = 60 * 60 * 24 * 180


class RedisMetCache:
    """Remembers the metabolic equivalent found for an activity.

    Fitboxing every Tuesday should cost one lookup, not one a week.
    """

    def __init__(self, client: Redis, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    def _key(self, user_id: UUID, activity_name: str) -> str:
        digest = hashlib.sha256(activity_name.encode("utf-8")).hexdigest()
        return f"{CACHE_KEY_PREFIX}{user_id}:{digest}"

    async def get(self, user_id: UUID, activity_name: str) -> Decimal | None:
        try:
            stored = await self._client.get(self._key(user_id, activity_name))
        except RedisError as error:
            # A cache that is down must not stop a session being recorded.
            logger.warning("met_cache_unavailable", extra={"error_type": type(error).__name__})
            return None

        if stored is None:
            return None

        try:
            return Decimal(stored)
        except InvalidOperation:
            return None

    async def set(self, user_id: UUID, activity_name: str, met: Decimal) -> None:
        try:
            await self._client.set(
                self._key(user_id, activity_name), str(met), ex=self._ttl_seconds
            )
        except RedisError as error:
            logger.warning("met_cache_write_failed", extra={"error_type": type(error).__name__})
