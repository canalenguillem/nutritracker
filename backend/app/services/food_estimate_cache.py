import hashlib
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.services.food_analysis import ClarificationQuestion, EstimatedItem, FoodEstimate

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "food:estimate:"
CACHE_TTL_SECONDS = 60 * 60 * 24 * 30


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _serialize(estimate: FoodEstimate) -> str:
    return json.dumps(
        {
            "summary": estimate.summary,
            "total_kcal": str(estimate.total_kcal),
            "confidence": None if estimate.confidence is None else str(estimate.confidence),
            "warning": estimate.warning,
            "items": [
                {
                    "name": item.name,
                    "quantity": str(item.quantity),
                    "unit": item.unit,
                    "kcal": str(item.kcal),
                    "protein_g": str(item.protein_g),
                    "fat_g": str(item.fat_g),
                    "carbohydrates_g": str(item.carbohydrates_g),
                    "confidence": None if item.confidence is None else str(item.confidence),
                    "assumptions": item.assumptions,
                }
                for item in estimate.items
            ],
            "questions": [
                {"key": question.key, "question": question.question, "options": question.options}
                for question in estimate.questions
            ],
        },
        ensure_ascii=False,
    )


def _deserialize(payload: str) -> FoodEstimate:
    data = json.loads(payload)
    return FoodEstimate(
        summary=str(data["summary"]),
        total_kcal=_decimal(data["total_kcal"]),
        confidence=_optional_decimal(data.get("confidence")),
        warning=str(data.get("warning", "")),
        items=[
            EstimatedItem(
                name=str(item["name"]),
                quantity=_decimal(item["quantity"]),
                unit=str(item["unit"]),
                kcal=_decimal(item["kcal"]),
                protein_g=_decimal(item["protein_g"]),
                fat_g=_decimal(item["fat_g"]),
                carbohydrates_g=_decimal(item["carbohydrates_g"]),
                confidence=_optional_decimal(item.get("confidence")),
                assumptions=[str(assumption) for assumption in item.get("assumptions", [])],
            )
            for item in data["items"]
        ],
        questions=[
            ClarificationQuestion(
                key=str(question["key"]),
                question=str(question["question"]),
                options=[str(option) for option in question.get("options", [])],
            )
            for question in data.get("questions", [])
        ],
    )


class RedisFoodEstimateCache:
    """Remembers an estimate per account, so a repeated meal costs nothing.

    Keys carry the model and prompt version, so changing either one retires
    the estimates produced by the previous pair instead of serving them on.
    """

    def __init__(
        self,
        client: Redis,
        model: str,
        prompt_version: str,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ) -> None:
        self._client = client
        self._model = model
        self._prompt_version = prompt_version
        self._ttl_seconds = ttl_seconds

    def _key(self, user_id: UUID, description: str) -> str:
        digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
        return f"{CACHE_KEY_PREFIX}{self._prompt_version}:{self._model}:{user_id}:{digest}"

    async def get(self, user_id: UUID, description: str) -> FoodEstimate | None:
        try:
            payload = await self._client.get(self._key(user_id, description))
        except RedisError as error:
            # A cache that is down must not stop a person recording a meal.
            logger.warning(
                "food_estimate_cache_unavailable", extra={"error_type": type(error).__name__}
            )
            return None

        if payload is None:
            return None

        try:
            return _deserialize(payload)
        except (json.JSONDecodeError, KeyError, InvalidOperation, TypeError, ValueError) as error:
            logger.warning(
                "food_estimate_cache_unreadable", extra={"error_type": type(error).__name__}
            )
            return None

    async def set(self, user_id: UUID, description: str, estimate: FoodEstimate) -> None:
        try:
            await self._client.set(
                self._key(user_id, description), _serialize(estimate), ex=self._ttl_seconds
            )
        except RedisError as error:
            logger.warning(
                "food_estimate_cache_write_failed", extra={"error_type": type(error).__name__}
            )
