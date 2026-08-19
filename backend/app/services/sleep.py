from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.models.enums import SleepQuality
from app.models.sleep import SleepEntry
from app.models.user import User
from app.repositories.sleep import SleepRepository
from app.services.daily_logs import end_of_day, naive_utc

MINUTES_PER_HOUR = Decimal("60")
# Longer than this and the two ends almost certainly describe different nights.
MAX_NIGHT_HOURS = Decimal("24")


class SleepEntryNotFoundError(Exception):
    pass


class ImpossibleNightError(Exception):
    pass


@dataclass(frozen=True)
class NewSleepEntry:
    started_at: datetime
    ended_at: datetime
    quality: SleepQuality | None = None
    notes: str | None = None


@dataclass(frozen=True)
class SleptNight:
    entry: SleepEntry
    hours: Decimal


def hours_of(entry: SleepEntry) -> Decimal:
    minutes = Decimal((entry.ended_at - entry.started_at).total_seconds()) / Decimal("60")
    return (minutes / MINUTES_PER_HOUR).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SleepService:
    def __init__(self, sleep: SleepRepository) -> None:
        self._sleep = sleep

    async def record(self, user: User, data: NewSleepEntry) -> SleepEntry:
        started_at = naive_utc(data.started_at)
        ended_at = naive_utc(data.ended_at)

        if ended_at <= started_at:
            raise ImpossibleNightError("A night has to end after it started.")

        length = Decimal((ended_at - started_at).total_seconds()) / Decimal("3600")
        if length > MAX_NIGHT_HOURS:
            raise ImpossibleNightError("That is longer than a day.")

        return await self._sleep.add(
            SleepEntry(
                user_id=user.id,
                started_at=started_at,
                ended_at=ended_at,
                quality=data.quality,
                notes=_clean_notes(data.notes),
            )
        )

    async def night_of(self, user: User, log_date: date) -> SleptNight | None:
        """The sleep that ended on this day, which is the night before it."""
        end = end_of_day(log_date, user.timezone)
        entries = await self._sleep.list_between(user.id, end - timedelta(days=1), end)
        if not entries:
            return None

        # Newest first: the last stretch of sleep is the night people mean.
        entry = entries[0]
        return SleptNight(entry=entry, hours=hours_of(entry))

    async def delete_entry(self, user: User, entry_id: UUID) -> None:
        entry = await self._sleep.get_for_user(user.id, entry_id)
        if entry is None:
            raise SleepEntryNotFoundError(str(entry_id))

        await self._sleep.remove(entry)


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    cleaned = notes.strip()
    return cleaned or None
