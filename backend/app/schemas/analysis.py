from decimal import Decimal

from pydantic import BaseModel


class EstimatedItemResponse(BaseModel):
    name: str
    quantity: Decimal
    unit: str
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    confidence: Decimal | None
    assumptions: list[str]


class ClarificationQuestionResponse(BaseModel):
    key: str
    question: str
    options: list[str]


class FoodEstimateResponse(BaseModel):
    summary: str
    items: list[EstimatedItemResponse]
    total_kcal: Decimal
    questions: list[ClarificationQuestionResponse]
    confidence: Decimal | None
    warning: str
    from_cache: bool
