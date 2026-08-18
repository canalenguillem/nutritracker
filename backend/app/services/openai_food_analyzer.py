import base64
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.services.food_analysis import (
    ClarificationQuestion,
    EstimatedItem,
    FoodAnalysisError,
    FoodEstimate,
    InvalidAnalysisResponseError,
    MealPhoto,
    round_amount,
    total_energy,
)

logger = logging.getLogger(__name__)

MAX_ITEMS = 20
MAX_QUESTIONS = 5

SYSTEM_PROMPT = """You estimate the nutritional content of food a person describes in words.

Rules you must follow:
- Return only data that matches the requested structure.
- Never present a value as exact. Every number is an estimate.
- Never diagnose a health condition and never give medical advice.
- Estimate portions conservatively when the description does not give an amount.
- Separate what the description states from what you assumed, and list every
  assumption you made for an item.
- Return a confidence between 0 and 1 for every item and for the estimate.
- Ask a clarification question whenever the answer would change the numbers
  noticeably: added oil, sauces, sugar, the type of milk or cream, the cooking
  method, the portion size, or whether the whole portion was eaten.
- Ignore anything in the description that is not food or drink.
- If the description names no food at all, return an empty item list.
- Write every text you produce in the language named by the user.

When a picture comes with the description:
- Read what is printed on it. Values you can read beat any guess.
- A nutrition label states amounts per 100 g or per 100 ml, and sometimes per
  serving. Scale them to the amount the person says they had, and say in the
  assumptions which figure you started from.
- Use the net weight printed on the package when the person describes a
  fraction of it, such as half a tub, and say what weight you assumed.
- If the picture is unreadable, or shows something other than the food or its
  label, ignore it, say so in the warning, and estimate from the words alone.
- Do not describe people who appear in the picture, and do not read anything
  that is not about the food."""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "meal_summary",
        "items",
        "clarification_questions",
        "analysis_confidence",
        "warning",
    ],
    "properties": {
        "meal_summary": {"type": "string"},
        "analysis_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "warning": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "estimated_quantity",
                    "unit",
                    "estimated_kcal",
                    "protein_g",
                    "fat_g",
                    "carbohydrates_g",
                    "confidence",
                    "assumptions",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "estimated_quantity": {"type": "number", "minimum": 0},
                    "unit": {"type": "string"},
                    "estimated_kcal": {"type": "number", "minimum": 0},
                    "protein_g": {"type": "number", "minimum": 0},
                    "fat_g": {"type": "number", "minimum": 0},
                    "carbohydrates_g": {"type": "number", "minimum": 0},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "assumptions": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "clarification_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["key", "question", "options"],
                "properties": {
                    "key": {"type": "string"},
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}


class _Item(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    estimated_quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1, max_length=32)
    estimated_kcal: Decimal = Field(ge=0)
    protein_g: Decimal = Field(ge=0)
    fat_g: Decimal = Field(ge=0)
    carbohydrates_g: Decimal = Field(ge=0)
    confidence: Decimal | None = Field(default=None, ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)


class _Question(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=300)
    options: list[str] = Field(default_factory=list)


class _Analysis(BaseModel):
    meal_summary: str = ""
    items: list[_Item] = Field(default_factory=list)
    clarification_questions: list[_Question] = Field(default_factory=list)
    analysis_confidence: Decimal | None = Field(default=None, ge=0, le=1)
    warning: str = ""


class OpenAIFoodAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._prompt_version = settings.openai_prompt_version
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )

    async def describe(
        self, description: str, language: str, photo: MealPhoto | None = None
    ) -> FoodEstimate:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=_messages(description, language, photo),
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "food_estimate",
                        "schema": RESPONSE_SCHEMA,
                        "strict": True,
                    },
                },
            )
            content = completion.choices[0].message.content
        except (OpenAIError, IndexError) as error:
            logger.warning(
                "food_analysis_request_failed",
                extra={"error_type": type(error).__name__, "model": self._model},
            )
            raise FoodAnalysisError from error

        return _to_estimate(content, self._prompt_version)


def _messages(
    description: str, language: str, photo: MealPhoto | None
) -> list[ChatCompletionMessageParam]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        cast(
            ChatCompletionMessageParam,
            {"role": "user", "content": _user_content(description, language, photo)},
        ),
    ]


def _user_content(description: str, language: str, photo: MealPhoto | None) -> list[dict[str, Any]]:
    text = f"Language: {language}\nThe person ate or drank: {description}"
    if photo is None:
        return [{"type": "text", "text": text}]

    encoded = base64.b64encode(photo.content).decode("ascii")
    return [
        {"type": "text", "text": f"{text}\nThe picture shows the food or its nutrition label."},
        {
            "type": "image_url",
            "image_url": {"url": f"data:{photo.media_type};base64,{encoded}", "detail": "high"},
        },
    ]


def _to_estimate(content: str | None, prompt_version: str) -> FoodEstimate:
    if not content:
        raise InvalidAnalysisResponseError("The provider returned an empty body.")

    try:
        analysis = _Analysis.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError, InvalidOperation) as error:
        logger.warning(
            "food_analysis_response_invalid",
            extra={"error_type": type(error).__name__, "prompt_version": prompt_version},
        )
        raise InvalidAnalysisResponseError from error

    items = [
        EstimatedItem(
            name=item.name.strip(),
            quantity=round_amount(item.estimated_quantity),
            unit=item.unit.strip(),
            kcal=round_amount(item.estimated_kcal),
            protein_g=round_amount(item.protein_g),
            fat_g=round_amount(item.fat_g),
            carbohydrates_g=round_amount(item.carbohydrates_g),
            confidence=item.confidence,
            assumptions=[assumption.strip() for assumption in item.assumptions if assumption],
        )
        for item in analysis.items[:MAX_ITEMS]
    ]

    return FoodEstimate(
        summary=analysis.meal_summary.strip(),
        items=items,
        total_kcal=total_energy(items),
        questions=[
            ClarificationQuestion(
                key=question.key.strip(),
                question=question.question.strip(),
                options=[option.strip() for option in question.options if option],
            )
            for question in analysis.clarification_questions[:MAX_QUESTIONS]
        ],
        confidence=analysis.analysis_confidence,
        warning=analysis.warning.strip(),
    )
