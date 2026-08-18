from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import ExerciseIntensity, ExerciseSource

MAX_CALORIES = Decimal("99999.99")
MAX_DURATION_MINUTES = 24 * 60


class ExerciseCreateRequest(BaseModel):
    activity_name: str = Field(min_length=1, max_length=120)
    duration_minutes: int = Field(gt=0, le=MAX_DURATION_MINUTES)
    intensity: ExerciseIntensity
    performed_at: datetime
    confirmed_calories: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=MAX_CALORIES, decimal_places=2
    )
    notes: str | None = Field(default=None, max_length=2000)
    weight_kg: Decimal | None = Field(
        default=None, gt=Decimal("0"), le=Decimal("500"), decimal_places=2
    )


class ExerciseUpdateRequest(BaseModel):
    activity_name: str | None = Field(default=None, min_length=1, max_length=120)
    duration_minutes: int | None = Field(default=None, gt=0, le=MAX_DURATION_MINUTES)
    intensity: ExerciseIntensity | None = None
    performed_at: datetime | None = None
    confirmed_calories: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=MAX_CALORIES, decimal_places=2
    )
    notes: str | None = Field(default=None, max_length=2000)


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_name: str
    duration_minutes: int
    intensity: ExerciseIntensity
    source: ExerciseSource
    performed_at: datetime
    estimated_calories: Decimal | None
    confirmed_calories: Decimal | None
    counted_calories: Decimal
    notes: str | None

    @field_serializer("performed_at")
    def serialize_performed_at(self, performed_at: datetime) -> datetime:
        # Stored naive in UTC; say so, or the browser reads it as local time.
        return performed_at.replace(tzinfo=UTC)
