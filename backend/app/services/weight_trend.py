from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.models.weight import WeightEntry
from app.services.daily_logs import local_log_date

TWO_PLACES = Decimal("0.01")

# The Hacker's Diet smoothing: each day the trend closes a tenth of the gap to
# the reading. Day to day a scale reports water and food as much as fat, and
# this is what separates the signal from that noise.
SMOOTHING = Decimal("0.1")

# After a long silence the trend should reach the new reading rather than crawl,
# but carrying forward for years would waste time to no effect.
MAX_CARRIED_DAYS = 60


@dataclass(frozen=True)
class WeightPoint:
    measured_on: date
    weight_kg: Decimal
    trend_kg: Decimal


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def daily_readings(entries: list[WeightEntry], timezone_name: str) -> list[tuple[date, Decimal]]:
    """One reading per day, keeping the last one recorded for that day."""
    by_day: dict[date, tuple[WeightEntry, Decimal]] = {}
    for entry in entries:
        day = local_log_date(entry.measured_at, timezone_name)
        current = by_day.get(day)
        if current is None or entry.measured_at >= current[0].measured_at:
            by_day[day] = (entry, entry.weight_kg)

    return [(day, weight) for day, (_, weight) in sorted(by_day.items())]


def build_trend(entries: list[WeightEntry], timezone_name: str) -> list[WeightPoint]:
    readings = daily_readings(entries, timezone_name)
    if not readings:
        return []

    points: list[WeightPoint] = []
    trend = readings[0][1]
    previous_day = readings[0][0]

    for index, (day, weight) in enumerate(readings):
        if index == 0:
            trend = weight
        else:
            # Step once per day gone by, so a gap does not leave the trend behind.
            elapsed = min((day - previous_day).days, MAX_CARRIED_DAYS)
            for _ in range(max(elapsed, 1)):
                trend = trend + (weight - trend) * SMOOTHING

        previous_day = day
        points.append(
            WeightPoint(measured_on=day, weight_kg=_round(weight), trend_kg=_round(trend))
        )

    return points


def trend_change(points: list[WeightPoint], over_days: int) -> Decimal | None:
    """How much the trend moved across the last window, or nothing if too short."""
    if len(points) < 2:
        return None

    latest = points[-1]
    cutoff = latest.measured_on.toordinal() - over_days
    earlier = [point for point in points if point.measured_on.toordinal() <= cutoff]
    reference = earlier[-1] if earlier else points[0]

    if reference.measured_on == latest.measured_on:
        return None

    return _round(latest.trend_kg - reference.trend_kg)
