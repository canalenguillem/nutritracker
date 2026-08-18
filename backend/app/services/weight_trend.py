from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

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

# The window the rate of change is read over. Shorter than this and a single
# wobble sets the direction; longer and a recent change of habit is invisible.
RATE_WINDOW_DAYS = 28
MIN_RATE_SPAN_DAYS = 7

DAYS_PER_WEEK = Decimal("7")
# Past this the arithmetic still works but the answer would be a fiction.
MAX_PROJECTED_DAYS = 5 * 365
# Within this much of the target, calling it reached is more useful than a date.
TARGET_TOLERANCE_KG = Decimal("0.10")

ProjectionStatus = Literal[
    "reachable",
    "already_there",
    "wrong_way",
    "too_flat",
    "not_enough_data",
    "too_far",
]


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


@dataclass(frozen=True)
class TrendProjection:
    status: ProjectionStatus
    kg_per_week: Decimal | None = None
    reaches_target_on: date | None = None
    days_to_target: int | None = None


def weekly_rate(points: list[WeightPoint]) -> Decimal | None:
    """How fast the trend is moving, in kilos a week.

    Read from the trend rather than the readings, so a heavy dinner the night
    before does not become a rate of change.
    """
    if len(points) < 2:
        return None

    latest = points[-1]
    window_start = latest.measured_on - timedelta(days=RATE_WINDOW_DAYS)
    within = [point for point in points if point.measured_on >= window_start]
    reference = within[0] if len(within) >= 2 else points[0]

    span_days = (latest.measured_on - reference.measured_on).days
    if span_days < MIN_RATE_SPAN_DAYS:
        return None

    per_day = (latest.trend_kg - reference.trend_kg) / Decimal(span_days)
    return _round(per_day * DAYS_PER_WEEK)


def project_target(points: list[WeightPoint], target_kg: Decimal | None) -> TrendProjection:
    """When the trend would meet the target if today's pace held.

    It is an extrapolation of a habit, not a promise: the pace changes, and the
    interface has to say so.
    """
    if target_kg is None or not points:
        return TrendProjection(status="not_enough_data")

    latest = points[-1]
    remaining = target_kg - latest.trend_kg

    if abs(remaining) <= TARGET_TOLERANCE_KG:
        return TrendProjection(status="already_there", kg_per_week=weekly_rate(points))

    rate = weekly_rate(points)
    if rate is None:
        return TrendProjection(status="not_enough_data")

    if rate == 0:
        return TrendProjection(status="too_flat", kg_per_week=rate)

    # Both must point the same way: losing towards a lower target, or gaining
    # towards a higher one.
    if (remaining > 0) != (rate > 0):
        return TrendProjection(status="wrong_way", kg_per_week=rate)

    days = int((remaining / (rate / DAYS_PER_WEEK)).to_integral_value(rounding=ROUND_HALF_UP))
    if days > MAX_PROJECTED_DAYS:
        return TrendProjection(status="too_far", kg_per_week=rate)

    return TrendProjection(
        status="reachable",
        kg_per_week=rate,
        days_to_target=days,
        reaches_target_on=latest.measured_on + timedelta(days=days),
    )
