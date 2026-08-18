from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

TWO_PLACES = Decimal("0.01")


class FoodAnalysisDisabledError(Exception):
    pass


class FoodAnalysisError(Exception):
    pass


class InvalidAnalysisResponseError(FoodAnalysisError):
    pass


@dataclass(frozen=True)
class EstimatedItem:
    name: str
    quantity: Decimal
    unit: str
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    confidence: Decimal | None = None
    assumptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClarificationQuestion:
    key: str
    question: str
    options: list[str]


@dataclass(frozen=True)
class FoodEstimate:
    summary: str
    items: list[EstimatedItem]
    total_kcal: Decimal
    questions: list[ClarificationQuestion] = field(default_factory=list)
    confidence: Decimal | None = None
    warning: str = ""


class FoodAnalyzer(Protocol):
    async def describe(self, description: str, language: str) -> FoodEstimate: ...


def round_amount(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def total_energy(items: list[EstimatedItem]) -> Decimal:
    """Add the items up here rather than trusting the model's own arithmetic."""
    return round_amount(sum((item.kcal for item in items), Decimal("0")))


class FoodAnalysisService:
    def __init__(self, analyzer: FoodAnalyzer | None) -> None:
        self._analyzer = analyzer

    @property
    def enabled(self) -> bool:
        return self._analyzer is not None

    async def describe(self, description: str, language: str = "es") -> FoodEstimate:
        if self._analyzer is None:
            raise FoodAnalysisDisabledError

        cleaned = description.strip()
        if not cleaned:
            raise InvalidAnalysisResponseError("The description is empty.")

        estimate = await self._analyzer.describe(cleaned, language)
        if not estimate.items:
            raise InvalidAnalysisResponseError("The estimate contains no food.")

        return FoodEstimate(
            summary=estimate.summary,
            items=estimate.items,
            total_kcal=total_energy(estimate.items),
            questions=estimate.questions,
            confidence=estimate.confidence,
            warning=estimate.warning,
        )
