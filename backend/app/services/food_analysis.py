import hashlib
import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol
from uuid import UUID

TWO_PLACES = Decimal("0.01")
WHITESPACE = re.compile(r"\s+")


class FoodAnalysisDisabledError(Exception):
    pass


class FoodAnalysisError(Exception):
    pass


class InvalidAnalysisResponseError(FoodAnalysisError):
    pass


@dataclass(frozen=True)
class MealPhoto:
    """A picture supporting the description, such as a nutrition label."""

    content: bytes
    media_type: str

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


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
    from_cache: bool = False


class FoodAnalyzer(Protocol):
    async def describe(
        self, description: str, language: str, photo: MealPhoto | None = None
    ) -> FoodEstimate: ...


class FoodEstimateCache(Protocol):
    async def get(self, user_id: UUID, description: str) -> FoodEstimate | None: ...

    async def set(self, user_id: UUID, description: str, estimate: FoodEstimate) -> None: ...


def normalize_description(description: str) -> str:
    """Fold the harmless differences between two ways of typing the same meal."""
    collapsed = WHITESPACE.sub(" ", description).strip().lower()
    return collapsed.strip(" .,;:!¡?¿")


def round_amount(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def total_energy(items: list[EstimatedItem]) -> Decimal:
    """Add the items up here rather than trusting the model's own arithmetic."""
    return round_amount(sum((item.kcal for item in items), Decimal("0")))


class FoodAnalysisService:
    def __init__(
        self, analyzer: FoodAnalyzer | None, cache: FoodEstimateCache | None = None
    ) -> None:
        self._analyzer = analyzer
        self._cache = cache

    @property
    def enabled(self) -> bool:
        return self._analyzer is not None

    async def describe(
        self,
        user_id: UUID,
        description: str,
        language: str = "es",
        photo: MealPhoto | None = None,
    ) -> FoodEstimate:
        cleaned = description.strip()
        if not cleaned and photo is None:
            raise InvalidAnalysisResponseError("There is nothing to work from.")

        # A picture changes the answer, so it has to change the key too.
        key = normalize_description(cleaned)
        if photo is not None:
            key = f"{key}#{photo.digest}"

        # A repeat of the same meal costs nothing and answers immediately.
        if self._cache is not None:
            remembered = await self._cache.get(user_id, key)
            if remembered is not None:
                return _with_totals(remembered, from_cache=True)

        if self._analyzer is None:
            raise FoodAnalysisDisabledError

        estimate = await self._analyzer.describe(cleaned, language, photo)
        if not estimate.items:
            raise InvalidAnalysisResponseError("The estimate contains no food.")

        fresh = _with_totals(estimate, from_cache=False)
        if self._cache is not None:
            await self._cache.set(user_id, key, fresh)

        return fresh


def _with_totals(estimate: FoodEstimate, from_cache: bool) -> FoodEstimate:
    return FoodEstimate(
        summary=estimate.summary,
        items=estimate.items,
        total_kcal=total_energy(estimate.items),
        questions=estimate.questions,
        confidence=estimate.confidence,
        warning=estimate.warning,
        from_cache=from_cache,
    )
