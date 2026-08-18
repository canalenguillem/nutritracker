from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.models.weight import WeightEntry
from app.services.weight_trend import build_trend, daily_readings, trend_change

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
