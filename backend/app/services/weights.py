from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.models.user import User, UserProfile
from app.models.weight import WeightEntry
from app.repositories.user_profiles import UserProfileRepository
from app.repositories.weights import WeightRepository
from app.services.daily_logs import naive_utc
from app.services.weight_trend import WeightPoint, build_trend, trend_change

TWO_PLACES = Decimal("0.01")
CENTIMETRES_PER_METRE = Decimal("100")


class WeightEntryNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class NewWeightEntry:
    weight_kg: Decimal
    measured_at: datetime
    notes: str | None = None


@dataclass(frozen=True)
class WeightHistory:
    points: list[WeightPoint]
    latest_weight_kg: Decimal | None = None
    latest_trend_kg: Decimal | None = None
    change_7_days_kg: Decimal | None = None
    change_30_days_kg: Decimal | None = None
    target_weight_kg: Decimal | None = None
    body_mass_index: Decimal | None = None


def body_mass_index(weight_kg: Decimal | None, height_cm: Decimal | None) -> Decimal | None:
    """An estimate, and one that says nothing about body composition."""
    if weight_kg is None or height_cm is None or height_cm <= 0:
        return None

    height_m = height_cm / CENTIMETRES_PER_METRE
    return (weight_kg / (height_m * height_m)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class WeightService:
    def __init__(self, weights: WeightRepository, profiles: UserProfileRepository) -> None:
        self._weights = weights
        self._profiles = profiles

    async def record(self, user: User, data: NewWeightEntry) -> WeightEntry:
        entry = await self._weights.add(
            WeightEntry(
                user_id=user.id,
                weight_kg=data.weight_kg,
                measured_at=naive_utc(data.measured_at),
                notes=_clean_notes(data.notes),
            )
        )
        await self._sync_current_weight(user)
        return entry

    async def list_entries(self, user: User) -> list[WeightEntry]:
        return await self._weights.list_for_user(user.id)

    async def delete_entry(self, user: User, entry_id: UUID) -> None:
        entry = await self._weights.get_for_user(user.id, entry_id)
        if entry is None:
            raise WeightEntryNotFoundError(str(entry_id))

        await self._weights.remove(entry)
        await self._sync_current_weight(user)

    async def history(self, user: User) -> WeightHistory:
        entries = await self._weights.list_for_user(user.id)
        points = build_trend(entries, user.timezone)
        profile = await self._profiles.get_for_user(user.id)
        latest = points[-1] if points else None

        return WeightHistory(
            points=points,
            latest_weight_kg=latest.weight_kg if latest else None,
            latest_trend_kg=latest.trend_kg if latest else None,
            change_7_days_kg=trend_change(points, 7),
            change_30_days_kg=trend_change(points, 30),
            target_weight_kg=profile.target_weight_kg if profile else None,
            body_mass_index=body_mass_index(
                latest.trend_kg if latest else None,
                profile.height_cm if profile else None,
            ),
        )

    async def _sync_current_weight(self, user: User) -> None:
        """Keep the profile showing the latest reading, so estimates use it."""
        entries = await self._weights.list_for_user(user.id)
        latest = entries[-1].weight_kg if entries else None

        profile = await self._profiles.get_for_user(user.id)
        if profile is None:
            if latest is not None:
                await self._profiles.add(UserProfile(user_id=user.id, current_weight_kg=latest))
            return

        profile.current_weight_kg = latest


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    cleaned = notes.strip()
    return cleaned or None
