from datetime import date
from decimal import Decimal

from app.services.week_metrics import DayMetrics, build_week_metrics, monday_of

MONDAY = date(2026, 8, 17)
SUNDAY = date(2026, 8, 23)


def day(
    offset: int,
    *,
    food: str = "0",
    exercise: str = "0",
    balance: str | None = None,
    sleep: str | None = None,
    has_food: bool = False,
    has_exercise: bool = False,
) -> DayMetrics:
    return DayMetrics(
        day=date.fromordinal(MONDAY.toordinal() + offset),
        food_kcal=Decimal(food),
        exercise_kcal=Decimal(exercise),
        balance_kcal=None if balance is None else Decimal(balance),
        sleep_hours=None if sleep is None else Decimal(sleep),
        has_food=has_food,
        has_exercise=has_exercise,
    )


def test_monday_of_holds_a_monday_still() -> None:
    assert monday_of(MONDAY) == MONDAY


def test_monday_of_pulls_sunday_back_six_days() -> None:
    assert monday_of(SUNDAY) == MONDAY


def test_averages_run_over_the_days_that_carry_the_thing_averaged() -> None:
    days = [
        day(0, food="2000", has_food=True),
        day(1, food="2400", has_food=True),
        *[day(offset) for offset in range(2, 7)],
    ]

    metrics = build_week_metrics(MONDAY, days, today=date(2026, 8, 24))

    # Two days eaten, not seven: dividing by seven would report an intake of
    # 629 kcal a day for someone who ate over two thousand on both.
    assert metrics.days_with_food == 2
    assert metrics.average_food_kcal == Decimal("2200.00")
    assert metrics.total_food_kcal == Decimal("4400.00")


def test_a_week_still_running_is_not_complete() -> None:
    days = [day(offset) for offset in range(7)]

    metrics = build_week_metrics(MONDAY, days, today=SUNDAY)

    assert metrics.is_complete is False


def test_a_week_is_complete_only_once_its_last_day_has_passed() -> None:
    days = [day(offset) for offset in range(7)]

    assert build_week_metrics(MONDAY, days, today=date(2026, 8, 24)).is_complete is True


def test_the_balance_average_ignores_days_with_no_food_recorded() -> None:
    days = [
        day(0, food="2000", balance="-300", has_food=True),
        # Nothing eaten and nothing recorded: counting this as a 2600 deficit
        # would make an unrecorded day look like a starved one.
        day(1, balance="-2600"),
        *[day(offset) for offset in range(2, 7)],
    ]

    metrics = build_week_metrics(MONDAY, days, today=date(2026, 8, 24))

    assert metrics.average_balance_kcal == Decimal("-300.00")


def test_sleep_averages_only_the_nights_recorded() -> None:
    days = [
        day(0, sleep="7.5"),
        day(1, sleep="6.5"),
        *[day(offset) for offset in range(2, 7)],
    ]

    metrics = build_week_metrics(MONDAY, days, today=date(2026, 8, 24))

    assert metrics.days_with_sleep == 2
    assert metrics.average_sleep_hours == Decimal("7.00")
