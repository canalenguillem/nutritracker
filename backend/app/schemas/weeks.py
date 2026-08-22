from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class WeekDayResponse(BaseModel):
    log_date: date
    food_kcal: Decimal
    exercise_kcal: Decimal
    balance_kcal: Decimal | None
    sleep_hours: Decimal | None
    has_food: bool
    has_exercise: bool


class WeekReviewResponse(BaseModel):
    week_start: date
    generated_at: datetime
    #: True once the week is over: a closed week keeps the review it was given.
    is_final: bool
    headline: str
    observations: list[str]
    comparison: str | None
    watch_out: str | None

    @field_serializer("generated_at")
    def serialize_instant(self, moment: datetime) -> datetime:
        return moment.replace(tzinfo=UTC)


class WeekResponse(BaseModel):
    week_start: date
    week_end: date
    is_complete: bool
    days: list[WeekDayResponse]
    days_with_food: int
    days_with_exercise: int
    days_with_sleep: int
    total_food_kcal: Decimal
    average_food_kcal: Decimal | None
    total_exercise_kcal: Decimal
    average_sleep_hours: Decimal | None
    average_balance_kcal: Decimal | None
    weight_change_kg: Decimal | None
    #: False when no reviewer is configured, so the button can say why.
    can_review: bool
    #: A week is only compared against one that was itself written up.
    has_previous_review: bool
    review: WeekReviewResponse | None
