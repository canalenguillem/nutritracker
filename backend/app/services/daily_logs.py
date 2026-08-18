from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.meal import DailyLog
from app.models.user import User
from app.repositories.daily_logs import DailyLogRepository

UTC_ZONE = ZoneInfo("UTC")


def local_log_date(moment: datetime, timezone_name: str) -> date:
    """Return the calendar day an entry belongs to for the person reading it.

    Timestamps are stored as naive UTC, so a meal eaten just after midnight in
    Madrid must not be filed under the previous day.
    """
    try:
        timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        timezone = UTC_ZONE

    aware = moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC_ZONE)
    return aware.astimezone(timezone).date()


def naive_utc(moment: datetime) -> datetime:
    """Store every timestamp as naive UTC, whatever offset the client sent."""
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(UTC_ZONE).replace(tzinfo=None)


async def resolve_daily_log(
    daily_logs: DailyLogRepository, user: User, moment: datetime
) -> DailyLog:
    """The day an entry belongs to, created the first time something lands on it."""
    log_date = local_log_date(moment, user.timezone)
    existing = await daily_logs.get_by_date(user.id, log_date)
    if existing is not None:
        return existing

    return await daily_logs.add(DailyLog(user_id=user.id, log_date=log_date))
