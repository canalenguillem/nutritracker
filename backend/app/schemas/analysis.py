from decimal import Decimal

from pydantic import BaseModel, computed_field

from app.services.nutrition_check import kcal_from_macros, macros_disagree


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

    @computed_field
    def kcal_from_macros(self) -> Decimal:
        return kcal_from_macros(self.protein_g, self.fat_g, self.carbohydrates_g)

    @computed_field
    def macros_disagree(self) -> bool:
        return macros_disagree(self.kcal, self.protein_g, self.fat_g, self.carbohydrates_g)


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
