from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

MIN_WEIGHT = Decimal("20")
MAX_WEIGHT = Decimal("500")


class WeightCreateRequest(BaseModel):
    weight_kg: Decimal = Field(gt=MIN_WEIGHT, le=MAX_WEIGHT, decimal_places=2)
    measured_at: datetime
    notes: str | None = Field(default=None, max_length=2000)


class WeightEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    weight_kg: Decimal
    measured_at: datetime
    notes: str | None

    @field_serializer("measured_at")
    def serialize_measured_at(self, measured_at: datetime) -> datetime:
        # Stored naive in UTC; say so, or the browser reads it as local time.
        return measured_at.replace(tzinfo=UTC)


class WeightPointResponse(BaseModel):
    measured_on: date
    weight_kg: Decimal
    trend_kg: Decimal


class WeightHistoryResponse(BaseModel):
    points: list[WeightPointResponse]
    latest_weight_kg: Decimal | None
    latest_trend_kg: Decimal | None
    change_7_days_kg: Decimal | None
    change_30_days_kg: Decimal | None
    target_weight_kg: Decimal | None
    body_mass_index: Decimal | None
