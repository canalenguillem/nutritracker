from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
PrimaryGoal = Literal["lose_weight", "maintain_weight", "gain_muscle"]
BiologicalSex = Literal["female", "male", "unspecified"]


class ProfileUpdateRequest(BaseModel):
    height_cm: Decimal | None = Field(
        default=None, gt=Decimal("50"), le=Decimal("260"), decimal_places=2
    )
    target_weight_kg: Decimal | None = Field(
        default=None, gt=Decimal("20"), le=Decimal("500"), decimal_places=2
    )
    birth_date: date | None = None
    biological_sex: BiologicalSex | None = None
    activity_level: ActivityLevel | None = None
    primary_goal: PrimaryGoal | None = None
    daily_calorie_target: Decimal | None = Field(
        default=None, gt=Decimal("500"), le=Decimal("10000"), decimal_places=2
    )


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    height_cm: Decimal | None
    current_weight_kg: Decimal | None
    target_weight_kg: Decimal | None
    birth_date: date | None
    biological_sex: str | None
    activity_level: str
    primary_goal: str
    daily_calorie_target: Decimal | None
