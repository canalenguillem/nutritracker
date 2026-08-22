from datetime import date
from decimal import Decimal

import pytest

from app.services.week_metrics import DayMetrics, build_week_metrics
from app.services.week_review import WeekReviewError, describe_week, to_review

MONDAY = date(2026, 8, 17)


def week(*days: DayMetrics, today: date = date(2026, 8, 22)) -> object:
    filled = list(days) + [
        DayMetrics(
            day=date.fromordinal(MONDAY.toordinal() + offset),
            food_kcal=Decimal("0"),
            exercise_kcal=Decimal("0"),
            balance_kcal=None,
            sleep_hours=None,
            has_food=False,
            has_exercise=False,
            is_future=date.fromordinal(MONDAY.toordinal() + offset) > today,
        )
        for offset in range(len(days), 7)
    ]
    return build_week_metrics(MONDAY, filled, today=today)


def a_day(offset: int, **overrides: object) -> DayMetrics:
    values: dict[str, object] = {
        "day": date.fromordinal(MONDAY.toordinal() + offset),
        "food_kcal": Decimal("0"),
        "exercise_kcal": Decimal("0"),
        "balance_kcal": None,
        "sleep_hours": None,
        "has_food": False,
        "has_exercise": False,
        "is_future": False,
    }
    values.update(overrides)
    return DayMetrics(**values)  # type: ignore[arg-type]


def test_figures_reach_the_model_rounded_not_weighed() -> None:
    metrics = week(a_day(0, food_kcal=Decimal("620.00"), has_food=True))

    described = describe_week(metrics, "this week")  # type: ignore[arg-type]

    # 620.00 handed over comes back as "620.00 kilocalories", which reads as a
    # figure someone put on a scale.
    assert described["average_food_kcal_on_days_recorded"] == 620
    assert described["days"][0]["food_kcal"] == 620


def test_sleep_and_weight_keep_one_decimal() -> None:
    metrics = week(a_day(0, sleep_hours=Decimal("7.53")))

    described = describe_week(metrics, "this week")  # type: ignore[arg-type]

    assert described["average_sleep_hours"] == "7.5"


def test_days_still_to_come_are_marked_as_such() -> None:
    # Saturday, so Sunday has not happened: calling it an unrecorded day would
    # blame someone for a day they have not lived yet.
    metrics = week(a_day(0, food_kcal=Decimal("500"), has_food=True))

    described = describe_week(metrics, "this week")  # type: ignore[arg-type]

    assert described["days"][6]["still_to_come"] is True
    assert described["days"][0]["still_to_come"] is False
    assert described["days_still_to_come"] == 1


def test_a_review_that_says_nothing_is_refused() -> None:
    with pytest.raises(WeekReviewError):
        to_review('{"headline": "", "observations": [], "comparison": null, "watch_out": null}')


def test_a_review_keeps_at_most_five_observations() -> None:
    body = (
        '{"headline": "Una semana sostenida.", "observations": '
        '["a", "b", "c", "d", "e", "f"], "comparison": null, "watch_out": null}'
    )

    assert len(to_review(body).observations) == 5


def test_blank_observations_are_dropped() -> None:
    body = (
        '{"headline": "Bien.", "observations": ["a", "   ", "b"], '
        '"comparison": "  ", "watch_out": null}'
    )

    review = to_review(body)

    assert review.observations == ["a", "b"]
    assert review.comparison is None
