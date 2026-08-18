from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.weight import WeightEntry
from app.services.weight_trend import (
    build_trend,
    daily_readings,
    project_target,
    trend_change,
    weekly_rate,
)

USER_ID = uuid4()


def entry(day: int, weight: str, hour: int = 8) -> WeightEntry:
    return WeightEntry(
        id=uuid4(),
        user_id=USER_ID,
        measured_at=datetime(2026, 8, day, hour, 0),
        weight_kg=Decimal(weight),
    )


def test_without_readings_there_is_no_trend() -> None:
    assert build_trend([], "Europe/Madrid") == []


def test_the_first_reading_is_its_own_trend() -> None:
    points = build_trend([entry(1, "80.00")], "Europe/Madrid")

    assert points[0].weight_kg == Decimal("80.00")
    assert points[0].trend_kg == Decimal("80.00")


def test_the_trend_lags_behind_a_jump() -> None:
    points = build_trend([entry(1, "80.00"), entry(2, "82.00")], "Europe/Madrid")

    # A two kilo jump overnight is mostly water, so the trend barely moves.
    assert points[1].weight_kg == Decimal("82.00")
    assert points[1].trend_kg == Decimal("80.20")


def test_the_trend_ignores_a_single_bad_day() -> None:
    readings = [
        entry(1, "80.00"),
        entry(2, "80.10"),
        entry(3, "79.90"),
        entry(4, "83.00"),
        entry(5, "80.00"),
    ]

    points = build_trend(readings, "Europe/Madrid")

    # The scale swung three kilos; the trend stayed within a few hundred grams.
    assert points[-1].trend_kg < Decimal("80.40")
    assert points[-1].trend_kg > Decimal("79.90")


def test_a_steady_loss_is_followed() -> None:
    readings = [entry(day, str(Decimal("85") - Decimal("0.1") * day)) for day in range(1, 29)]

    points = build_trend(readings, "Europe/Madrid")

    assert points[-1].trend_kg < points[0].trend_kg
    change = trend_change(points, 7)
    assert change is not None
    assert change < Decimal("0")


def test_only_the_last_reading_of_a_day_counts() -> None:
    readings = daily_readings(
        [entry(1, "80.00", hour=7), entry(1, "81.00", hour=21)], "Europe/Madrid"
    )

    assert readings == [(readings[0][0], Decimal("81.00"))]


def test_a_gap_lets_the_trend_catch_up() -> None:
    close = build_trend([entry(1, "80.00"), entry(2, "84.00")], "Europe/Madrid")
    far = build_trend([entry(1, "80.00"), entry(28, "84.00")], "Europe/Madrid")

    # After a month the reading is believed much more than after one day.
    assert far[-1].trend_kg > close[-1].trend_kg


def test_a_single_reading_gives_no_change() -> None:
    assert trend_change(build_trend([entry(1, "80.00")], "Europe/Madrid"), 7) is None


def losing(days: int, start: str = "82.00", per_day: str = "0.05") -> list[WeightEntry]:
    """A steady loss, one reading a day, so the pace is unmistakable."""
    return [
        WeightEntry(
            id=uuid4(),
            user_id=USER_ID,
            measured_at=datetime(2026, 6, 1, 8, 0) + timedelta(days=day),
            weight_kg=Decimal(start) - Decimal(per_day) * day,
        )
        for day in range(days)
    ]


def test_the_weekly_rate_comes_from_the_trend() -> None:
    points = build_trend(losing(40), "Europe/Madrid")

    rate = weekly_rate(points)

    assert rate is not None
    # The readings fall 0.35 kg a week. The trend is still catching up at the
    # start of the window, so it reads slightly slower, and losing weight is
    # a negative rate.
    assert Decimal("-0.25") > rate > Decimal("-0.36")


def test_a_long_steady_history_reaches_the_real_pace() -> None:
    points = build_trend(losing(120), "Europe/Madrid")

    rate = weekly_rate(points)

    assert rate is not None
    # Once converged the trend runs parallel to the readings: 0.05 * 7.
    assert Decimal("-0.34") > rate > Decimal("-0.36")


def test_a_short_history_gives_no_rate() -> None:
    assert weekly_rate(build_trend(losing(3), "Europe/Madrid")) is None


def test_the_target_date_follows_the_pace() -> None:
    points = build_trend(losing(40), "Europe/Madrid")
    latest = points[-1]

    projection = project_target(points, latest.trend_kg - Decimal("2.00"))

    assert projection.status == "reachable"
    assert projection.days_to_target is not None
    assert projection.reaches_target_on is not None
    # Two kilos at about 0.35 a week is roughly a month and a half.
    assert 25 < projection.days_to_target < 60
    assert projection.reaches_target_on > latest.measured_on


def test_a_target_already_met_says_so() -> None:
    points = build_trend(losing(40), "Europe/Madrid")

    projection = project_target(points, points[-1].trend_kg)

    assert projection.status == "already_there"


def test_a_target_below_a_rising_trend_is_not_projected() -> None:
    rising = [
        WeightEntry(
            id=uuid4(),
            user_id=USER_ID,
            measured_at=datetime(2026, 6, 1, 8, 0) + timedelta(days=day),
            weight_kg=Decimal("80.00") + Decimal("0.05") * day,
        )
        for day in range(40)
    ]

    projection = project_target(build_trend(rising, "Europe/Madrid"), Decimal("75.00"))

    assert projection.status == "wrong_way"
    assert projection.reaches_target_on is None


def test_a_flat_trend_reaches_nothing() -> None:
    flat = [
        WeightEntry(
            id=uuid4(),
            user_id=USER_ID,
            measured_at=datetime(2026, 6, 1, 8, 0) + timedelta(days=day),
            weight_kg=Decimal("80.00"),
        )
        for day in range(40)
    ]

    projection = project_target(build_trend(flat, "Europe/Madrid"), Decimal("75.00"))

    assert projection.status == "too_flat"


def test_a_target_a_lifetime_away_is_refused() -> None:
    points = build_trend(losing(40, per_day="0.001"), "Europe/Madrid")

    projection = project_target(points, points[-1].trend_kg - Decimal("30.00"))

    assert projection.status == "too_far"
    assert projection.reaches_target_on is None


def test_without_a_target_there_is_nothing_to_project() -> None:
    assert project_target(build_trend(losing(40), "Europe/Madrid"), None).status == (
        "not_enough_data"
    )
