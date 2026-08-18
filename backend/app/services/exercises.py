from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.models.enums import ExerciseIntensity, ExerciseSource
from app.models.exercise import Exercise
from app.models.user import User, UserProfile
from app.repositories.daily_logs import DailyLogRepository
from app.repositories.exercises import ExerciseRepository
from app.repositories.user_profiles import UserProfileRepository
from app.services.daily_logs import naive_utc, resolve_daily_log
from app.services.exercise_calories import ActivityMet, estimate_calories, resolve_met
from app.services.met_cache import RedisMetCache
from app.services.met_lookup import MetLookup


class ExerciseNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class NewExercise:
    activity_name: str
    duration_minutes: int
    intensity: ExerciseIntensity
    performed_at: datetime
    confirmed_calories: Decimal | None = None
    notes: str | None = None
    weight_kg: Decimal | None = None


@dataclass(frozen=True)
class ExerciseChanges:
    activity_name: str | None = None
    duration_minutes: int | None = None
    intensity: ExerciseIntensity | None = None
    performed_at: datetime | None = None
    confirmed_calories: Decimal | None = None
    confirmed_calories_provided: bool = False
    notes: str | None = None
    notes_provided: bool = False


class ExerciseService:
    def __init__(
        self,
        exercises: ExerciseRepository,
        daily_logs: DailyLogRepository,
        profiles: UserProfileRepository,
        met_lookup: MetLookup | None = None,
        met_cache: RedisMetCache | None = None,
    ) -> None:
        self._exercises = exercises
        self._daily_logs = daily_logs
        self._profiles = profiles
        self._met_lookup = met_lookup
        self._met_cache = met_cache

    async def create_exercise(self, user: User, data: NewExercise) -> Exercise:
        performed_at = naive_utc(data.performed_at)
        weight_kg = await self._resolve_weight(user, data.weight_kg)
        daily_log = await resolve_daily_log(self._daily_logs, user, performed_at)

        exercise = Exercise(
            daily_log_id=daily_log.id,
            user_id=user.id,
            activity_name=data.activity_name.strip(),
            duration_minutes=data.duration_minutes,
            intensity=data.intensity,
            estimated_calories=estimate_calories(
                data.activity_name,
                data.intensity,
                data.duration_minutes,
                weight_kg,
                met=(await self._met_for(user, data.activity_name)).met,
            ),
            confirmed_calories=data.confirmed_calories,
            source=ExerciseSource.MANUAL,
            performed_at=performed_at,
            notes=_clean_notes(data.notes),
        )
        return await self._exercises.add(exercise)

    async def list_exercises(self, user: User, log_date: date | None = None) -> list[Exercise]:
        return await self._exercises.list_for_user(user.id, log_date)

    async def get_exercise(self, user: User, exercise_id: UUID) -> Exercise:
        exercise = await self._exercises.get_for_user(user.id, exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError(str(exercise_id))
        return exercise

    async def update_exercise(
        self, user: User, exercise_id: UUID, changes: ExerciseChanges
    ) -> Exercise:
        exercise = await self.get_exercise(user, exercise_id)

        if changes.activity_name is not None:
            exercise.activity_name = changes.activity_name.strip()
        if changes.duration_minutes is not None:
            exercise.duration_minutes = changes.duration_minutes
        if changes.intensity is not None:
            exercise.intensity = changes.intensity
        if changes.notes_provided:
            exercise.notes = _clean_notes(changes.notes)
        if changes.confirmed_calories_provided:
            exercise.confirmed_calories = changes.confirmed_calories

        if changes.performed_at is not None:
            performed_at = naive_utc(changes.performed_at)
            exercise.performed_at = performed_at
            daily_log = await resolve_daily_log(self._daily_logs, user, performed_at)
            exercise.daily_log_id = daily_log.id

        # Anything about the effort changes what the estimate should say.
        if (
            changes.activity_name is not None
            or changes.duration_minutes is not None
            or changes.intensity is not None
        ):
            weight_kg = await self._resolve_weight(user, None)
            exercise.estimated_calories = estimate_calories(
                exercise.activity_name,
                exercise.intensity,
                exercise.duration_minutes,
                weight_kg,
                met=(await self._met_for(user, exercise.activity_name)).met,
            )

        return exercise

    async def delete_exercise(self, user: User, exercise_id: UUID) -> None:
        exercise = await self.get_exercise(user, exercise_id)
        await self._exercises.remove(exercise)

    async def burned_calories(self, user: User, log_date: date) -> Decimal:
        exercises = await self._exercises.list_for_user(user.id, log_date)
        return sum((exercise.counted_calories for exercise in exercises), Decimal("0.00"))

    async def _met_for(self, user: User, activity_name: str) -> ActivityMet:
        return await resolve_met(
            user.id, activity_name, lookup=self._met_lookup, cache=self._met_cache
        )

    async def _resolve_weight(self, user: User, given: Decimal | None) -> Decimal | None:
        """Use the weight just given, remembering it, or the one already known."""
        profile = await self._profiles.get_for_user(user.id)

        if given is not None and given > 0:
            if profile is None:
                await self._profiles.add(UserProfile(user_id=user.id, current_weight_kg=given))
            else:
                profile.current_weight_kg = given
            return given

        return profile.current_weight_kg if profile is not None else None


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    cleaned = notes.strip()
    return cleaned or None
