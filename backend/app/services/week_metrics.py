from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

DAYS_IN_WEEK = 7
TWO_PLACES = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _mean(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return _round(sum(values, Decimal("0")) / Decimal(len(values)))


@dataclass(frozen=True)
class DayMetrics:
    day: date
    food_kcal: Decimal
    exercise_kcal: Decimal
    balance_kcal: Decimal | None
    sleep_hours: Decimal | None
    has_food: bool
    has_exercise: bool
    #: True for a day of this week that has not arrived yet.
    is_future: bool = False


@dataclass(frozen=True)
class WeekMetrics:
    week_start: date
    week_end: date
    #: False while any day of it is still to come.
    is_complete: bool
    days: list[DayMetrics] = field(default_factory=list)
    days_with_food: int = 0
    days_with_exercise: int = 0
    days_with_sleep: int = 0
    total_food_kcal: Decimal = Decimal("0.00")
    average_food_kcal: Decimal | None = None
    total_exercise_kcal: Decimal = Decimal("0.00")
    average_sleep_hours: Decimal | None = None
    average_balance_kcal: Decimal | None = None
    weight_change_kg: Decimal | None = None


def monday_of(day: date) -> date:
    """The Monday opening the week a day belongs to."""
    return day - timedelta(days=day.weekday())


def build_week_metrics(
    week_start: date,
    days: list[DayMetrics],
    today: date,
    weight_change_kg: Decimal | None = None,
) -> WeekMetrics:
    """Gather a week into the few figures worth talking about.

    Averages run over the days that carry the thing being averaged, not over
    seven: three days eaten and four unrecorded is not an average of a low
    intake, it is three days of data.
    """
    week_end = week_start + timedelta(days=DAYS_IN_WEEK - 1)

    with_food = [day for day in days if day.has_food]
    with_exercise = [day for day in days if day.has_exercise]
    with_sleep = [day for day in days if day.sleep_hours is not None]
    with_balance = [day for day in days if day.balance_kcal is not None and day.has_food]

    return WeekMetrics(
        week_start=week_start,
        week_end=week_end,
        is_complete=week_end < today,
        days=days,
        days_with_food=len(with_food),
        days_with_exercise=len(with_exercise),
        days_with_sleep=len(with_sleep),
        total_food_kcal=_round(sum((day.food_kcal for day in days), Decimal("0"))),
        average_food_kcal=_mean([day.food_kcal for day in with_food]),
        total_exercise_kcal=_round(sum((day.exercise_kcal for day in days), Decimal("0"))),
        average_sleep_hours=_mean(
            [day.sleep_hours for day in with_sleep if day.sleep_hours is not None]
        ),
        average_balance_kcal=_mean(
            [day.balance_kcal for day in with_balance if day.balance_kcal is not None]
        ),
        weight_change_kg=weight_change_kg,
    )
