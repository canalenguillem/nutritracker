import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol
from uuid import UUID

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Nothing a person does sits outside this range: sleeping is about 0.9, and the
# hardest efforts a human sustains reach the low twenties. A value beyond it is
# a mistake, not an activity.
MIN_MET = Decimal("0.9")
MAX_MET = Decimal("25")

SYSTEM_PROMPT = """You report the metabolic equivalent of task (MET) for a physical activity.

Rules you must follow:
- Give the average MET for the activity at a normal effort, as the Compendium of
  Physical Activities would list it. Intensity is applied elsewhere; do not
  adjust for it.
- The value must lie between 0.9 and 25.
- If the text names no physical activity at all, or you do not know the activity,
  say so instead of guessing.
- Name the activity you understood, in the language the person used."""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["recognised", "activity", "met"],
    "properties": {
        "recognised": {"type": "boolean"},
        "activity": {"type": "string"},
        "met": {"type": ["number", "null"]},
    },
}


class _MetAnswer(BaseModel):
    recognised: bool
    activity: str = ""
    met: Decimal | None = Field(default=None)


class MetLookup(Protocol):
    """Finds the metabolic equivalent for an activity the table does not know."""

    async def met_for(self, user_id: UUID, activity_name: str) -> Decimal | None: ...


class MetCache(Protocol):
    async def get(self, user_id: UUID, activity_name: str) -> Decimal | None: ...

    async def set(self, user_id: UUID, activity_name: str, met: Decimal) -> None: ...


class OpenAIMetLookup:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )

    async def met_for(self, user_id: UUID, activity_name: str) -> Decimal | None:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Activity: {activity_name}"},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "met_value",
                        "schema": RESPONSE_SCHEMA,
                        "strict": True,
                    },
                },
            )
            content = completion.choices[0].message.content
        except (OpenAIError, IndexError) as error:
            logger.warning(
                "met_lookup_failed",
                extra={"error_type": type(error).__name__, "model": self._model},
            )
            return None

        return _to_met(content)


def _to_met(content: str | None) -> Decimal | None:
    if not content:
        return None

    try:
        answer = _MetAnswer.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError, InvalidOperation) as error:
        logger.warning("met_lookup_response_invalid", extra={"error_type": type(error).__name__})
        return None

    if not answer.recognised or answer.met is None:
        return None

    # Trust the range, not the model: a MET of 400 would triple every estimate.
    if not MIN_MET <= answer.met <= MAX_MET:
        logger.warning("met_lookup_out_of_range", extra={"met": str(answer.met)})
        return None

    return answer.met
