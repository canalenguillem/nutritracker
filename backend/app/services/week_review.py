import json
import logging
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.services.week_metrics import WeekMetrics

logger = logging.getLogger(__name__)

MAX_OBSERVATIONS = 5

SYSTEM_PROMPT = """You look back at one week of a person's food, training and sleep.

You are given figures, already calculated. Do not recalculate them and do not
invent any that are not there.

Rules you must follow:
- Address the person directly, as "you", one person and not several. Never write
  about them in the third person.
- The headline says something about the week. "Weekly summary" and other titles
  of that kind are not headlines; write what the week was like.
- Point at what the figures actually show. If three days out of seven were
  recorded, say the week is thinly recorded rather than drawing conclusions from
  it as though it were complete.
- Every number you were given is an estimate. Round them as you speak, and never
  repeat a figure to the decimal as though the food had been weighed.
- A day marked as still to come has not happened yet. Never call it unrecorded
  and never count it against the person.
- Never diagnose, never prescribe a diet or a calorie figure, and never tell
  someone to eat more or less. Describe what happened, not what to do about it.
- If a previous week is given, say how this one differs. If none is given, leave
  the comparison empty rather than imagining one.
- Weight moves with water and food as much as with fat, so never read a single
  week's weight change as fat gained or lost.
- Keep each observation to one sentence. Between two and five of them.
- Write everything in the language named by the user."""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["headline", "observations", "comparison", "watch_out"],
    "properties": {
        "headline": {"type": "string"},
        "observations": {"type": "array", "items": {"type": "string"}},
        "comparison": {"type": ["string", "null"]},
        "watch_out": {"type": ["string", "null"]},
    },
}


class _Review(BaseModel):
    headline: str = Field(default="", max_length=300)
    observations: list[str] = Field(default_factory=list)
    comparison: str | None = None
    watch_out: str | None = None


@dataclass(frozen=True)
class WeekReview:
    headline: str
    observations: list[str] = field(default_factory=list)
    comparison: str | None = None
    watch_out: str | None = None


class WeekReviewer(Protocol):
    async def review(
        self, metrics: WeekMetrics, previous: WeekMetrics | None, language: str
    ) -> WeekReview: ...


class WeekReviewDisabledError(Exception):
    pass


class WeekReviewError(Exception):
    pass


def describe_week(metrics: WeekMetrics, label: str) -> dict[str, Any]:
    """The week as plain figures, which is all the model should work from."""
    return {
        "which": label,
        "from": metrics.week_start.isoformat(),
        "to": metrics.week_end.isoformat(),
        "week_finished": metrics.is_complete,
        "days_with_food_recorded": metrics.days_with_food,
        "days_with_training_recorded": metrics.days_with_exercise,
        "days_with_sleep_recorded": metrics.days_with_sleep,
        "days_still_to_come": sum(1 for day in metrics.days if day.is_future),
        "average_food_kcal_on_days_recorded": _whole(metrics.average_food_kcal),
        "total_training_kcal": _whole(metrics.total_exercise_kcal),
        "average_sleep_hours": _one_place(metrics.average_sleep_hours),
        "average_daily_balance_kcal": _whole(metrics.average_balance_kcal),
        "weight_trend_change_kg": _one_place(metrics.weight_change_kg),
        "days": [
            {
                "day": day.day.isoformat(),
                "still_to_come": day.is_future,
                "food_kcal": _whole(day.food_kcal) if day.has_food else None,
                "training_kcal": _whole(day.exercise_kcal) if day.has_exercise else None,
                "sleep_hours": _one_place(day.sleep_hours),
            }
            for day in metrics.days
        ],
    }


def _whole(value: Decimal | None) -> int | None:
    """Rounded to the kilocalorie before the model ever sees it.

    Handing over 620.00 invites the answer to repeat 620.00, and a figure
    carried to two decimal places reads as something that was weighed.
    """
    return None if value is None else int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _one_place(value: Decimal | None) -> str | None:
    return None if value is None else str(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


class OpenAIWeekReviewer:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )

    async def review(
        self, metrics: WeekMetrics, previous: WeekMetrics | None, language: str
    ) -> WeekReview:
        payload: dict[str, Any] = {"this_week": describe_week(metrics, "this week")}
        if previous is not None:
            payload["previous_week"] = describe_week(previous, "the week before")

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Language: {language}\n{json.dumps(payload, ensure_ascii=False)}"
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "week_review",
                        "schema": RESPONSE_SCHEMA,
                        "strict": True,
                    },
                },
            )
            content = completion.choices[0].message.content
        except (OpenAIError, IndexError) as error:
            logger.warning(
                "week_review_failed",
                extra={"error_type": type(error).__name__, "model": self._model},
            )
            raise WeekReviewError from error

        return to_review(content)


def to_review(content: str | None) -> WeekReview:
    if not content:
        raise WeekReviewError("The provider returned an empty body.")

    try:
        parsed = _Review.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as error:
        logger.warning("week_review_invalid", extra={"error_type": type(error).__name__})
        raise WeekReviewError from error

    observations = [line.strip() for line in parsed.observations if line.strip()]
    if not parsed.headline.strip() or not observations:
        raise WeekReviewError("The review says nothing.")

    return WeekReview(
        headline=parsed.headline.strip(),
        observations=observations[:MAX_OBSERVATIONS],
        comparison=(parsed.comparison or "").strip() or None,
        watch_out=(parsed.watch_out or "").strip() or None,
    )
