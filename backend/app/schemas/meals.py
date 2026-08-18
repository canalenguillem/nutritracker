from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import MealSource, MealStatus, MealType

MAX_AMOUNT = Decimal("999999.99")

Amount = Field(ge=Decimal("0"), le=MAX_AMOUNT, decimal_places=2)


class MealItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    quantity: Decimal = Field(gt=Decimal("0"), le=MAX_AMOUNT, decimal_places=2)
    unit: str = Field(min_length=1, max_length=32)
    kcal: Decimal = Amount
    protein_g: Decimal = Amount
    fat_g: Decimal = Amount
    carbohydrates_g: Decimal = Amount


class MealCreateRequest(BaseModel):
    meal_type: MealType
    eaten_at: datetime
    items: list[MealItemRequest] = Field(min_length=1, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class MealUpdateRequest(BaseModel):
    meal_type: MealType | None = None
    eaten_at: datetime | None = None
    items: list[MealItemRequest] | None = Field(default=None, min_length=1, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class MealItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    quantity: Decimal
    unit: str
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    user_confirmed: bool


class MealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meal_type: MealType
    eaten_at: datetime
    source: MealSource
    status: MealStatus
    notes: str | None
    total_kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    items: list[MealItemResponse]

    @field_serializer("eaten_at")
    def serialize_eaten_at(self, eaten_at: datetime) -> datetime:
        # Stored naive in UTC; say so, or the browser reads it as local time.
        return eaten_at.replace(tzinfo=UTC)


class DailySummaryResponse(BaseModel):
    log_date: date
    meal_count: int
    total_kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    exercise_kcal: Decimal
    exercise_count: int
    # Food minus exercise. This is not a deficit: the baseline expenditure is
    # unknown until the profile records height, weight, age and activity.
    net_kcal: Decimal
