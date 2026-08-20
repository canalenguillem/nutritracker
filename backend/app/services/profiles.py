from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.user import User, UserProfile
from app.repositories.user_profiles import UserProfileRepository


@dataclass(frozen=True)
class ProfileChanges:
    height_cm: Decimal | None = None
    height_cm_provided: bool = False
    target_weight_kg: Decimal | None = None
    target_weight_kg_provided: bool = False
    birth_date: date | None = None
    birth_date_provided: bool = False
    biological_sex: str | None = None
    biological_sex_provided: bool = False
    activity_level: str | None = None
    primary_goal: str | None = None
    daily_calorie_target: Decimal | None = None
    daily_calorie_target_provided: bool = False


class ProfileService:
    def __init__(self, profiles: UserProfileRepository) -> None:
        self._profiles = profiles

    async def get_profile(self, user: User) -> UserProfile:
        """The profile, created empty the first time it is asked for."""
        profile = await self._profiles.get_for_user(user.id)
        if profile is not None:
            return profile

        return await self._profiles.add(UserProfile(user_id=user.id))

    async def update_profile(self, user: User, changes: ProfileChanges) -> UserProfile:
        profile = await self.get_profile(user)

        if changes.height_cm_provided:
            profile.height_cm = changes.height_cm
        if changes.target_weight_kg_provided:
            profile.target_weight_kg = changes.target_weight_kg
        if changes.birth_date_provided:
            profile.birth_date = changes.birth_date
        if changes.biological_sex_provided:
            profile.biological_sex = changes.biological_sex
        if changes.activity_level is not None:
            profile.activity_level = changes.activity_level
        if changes.primary_goal is not None:
            profile.primary_goal = changes.primary_goal
        if changes.daily_calorie_target_provided:
            profile.daily_calorie_target = changes.daily_calorie_target

        return profile
