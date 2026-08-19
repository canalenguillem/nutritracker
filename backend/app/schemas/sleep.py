from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import SleepQuality


class SleepCreateRequest(BaseModel):
    started_at: datetime
    ended_at: datetime
    quality: SleepQuality | None = None
    notes: str | None = Field(default=None, max_length=2000)


class SleepUpdateRequest(BaseModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None
    quality: SleepQuality | None = None
    notes: str | None = Field(default=None, max_length=2000)


class SleepEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    started_at: datetime
    ended_at: datetime
    quality: SleepQuality | None
    notes: str | None

    @field_serializer("started_at", "ended_at")
    def serialize_instant(self, moment: datetime) -> datetime:
        # Stored naive in UTC; say so, or the browser reads it as local time.
        return moment.replace(tzinfo=UTC)


class SleptNightResponse(SleepEntryResponse):
    hours: Decimal
