from datetime import date, datetime, timedelta
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
    aware = moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC_ZONE)
    return aware.astimezone(_zone(timezone_name)).date()


def _zone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return UTC_ZONE


def end_of_day(log_date: date, timezone_name: str) -> datetime:
    """The midnight closing that day, as the naive UTC everything is stored in."""
    local_midnight = datetime.combine(
        log_date + timedelta(days=1), datetime.min.time(), tzinfo=_zone(timezone_name)
    )
    return local_midnight.astimezone(UTC_ZONE).replace(tzinfo=None)


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
