from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUserDependency,
    ExerciseServiceDependency,
    MealServiceDependency,
    ProfileServiceDependency,
    SleepServiceDependency,
    WeekServiceDependency,
    WeightServiceDependency,
)
from app.core.errors import ApiError
from app.models.base import utc_now
from app.models.user import User
from app.models.week import WeeklySummary
from app.schemas.weeks import WeekDayResponse, WeekResponse, WeekReviewResponse
from app.services.daily_logs import local_log_date
from app.services.energy import energy_balance
from app.services.exercises import ExerciseService
from app.services.meals import MealService
from app.services.profiles import ProfileService
from app.services.sleep import SleepService
from app.services.week_metrics import (
    DAYS_IN_WEEK,
    DayMetrics,
    WeekMetrics,
    build_week_metrics,
    monday_of,
)
from app.services.week_review import WeekReviewDisabledError, WeekReviewError
from app.services.weeks import (
    NothingToReviewError,
    WeekAlreadyClosedError,
    observations_of,
    previous_week_of,
)
from app.services.weights import WeightService

router = APIRouter(prefix="/weeks", tags=["weeks"])

WeekQuery = Annotated[date | None, Query(description="Any day of the week to read.")]


@router.get("", response_model=WeekResponse)
async def read_week(
    user: CurrentUserDependency,
    weeks: WeekServiceDependency,
    meals: MealServiceDependency,
    exercises: ExerciseServiceDependency,
    sleep: SleepServiceDependency,
    weights: WeightServiceDependency,
    profiles: ProfileServiceDependency,
    week: WeekQuery = None,
) -> WeekResponse:
    """The week's own figures, plus the review of it if one was written."""
    monday = _monday(week, user)
    metrics = await _metrics(user, monday, meals, exercises, sleep, weights, profiles)
    stored = await weeks.stored(user, monday)
    previous_stored = await weeks.stored(user, previous_week_of(monday))

    return _week_response(
        metrics,
        can_review=weeks.can_review,
        has_previous_review=previous_stored is not None,
        review=stored,
    )


@router.post("/review", response_model=WeekResponse, status_code=status.HTTP_201_CREATED)
async def review_week(
    user: CurrentUserDependency,
    weeks: WeekServiceDependency,
    meals: MealServiceDependency,
    exercises: ExerciseServiceDependency,
    sleep: SleepServiceDependency,
    weights: WeightServiceDependency,
    profiles: ProfileServiceDependency,
    week: WeekQuery = None,
) -> WeekResponse:
    """Write the week up. Once the week is over its review is kept as it stands."""
    monday = _monday(week, user)
    metrics = await _metrics(user, monday, meals, exercises, sleep, weights, profiles)

    previous_monday = previous_week_of(monday)
    previous_stored = await weeks.stored(user, previous_monday)
    previous = (
        await _metrics(user, previous_monday, meals, exercises, sleep, weights, profiles)
        if previous_stored is not None
        else None
    )

    try:
        summary = await weeks.review_week(user, metrics, previous, previous_stored)
    except WeekAlreadyClosedError as error:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            detail="That week is closed and keeps the summary it was given.",
        ) from error
    except NothingToReviewError as error:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            detail="There is nothing recorded that week to look back at.",
        ) from error
    except WeekReviewDisabledError as error:
        raise ApiError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SERVICE_UNAVAILABLE",
            detail="Weekly summaries are not configured on this server.",
        ) from error
    except WeekReviewError as error:
        raise ApiError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_ANALYSIS_FAILED",
            detail="The week could not be summarised. Try again.",
        ) from error

    return _week_response(
        metrics,
        can_review=True,
        has_previous_review=previous_stored is not None,
        review=summary,
    )


def _monday(week: date | None, user: User) -> date:
    return monday_of(week if week is not None else local_log_date(utc_now(), user.timezone))


def _week_response(
    metrics: WeekMetrics,
    *,
    can_review: bool,
    has_previous_review: bool,
    review: WeeklySummary | None,
) -> WeekResponse:
    return WeekResponse(
        week_start=metrics.week_start,
        week_end=metrics.week_end,
        is_complete=metrics.is_complete,
        days=[
            WeekDayResponse(
                log_date=day.day,
                food_kcal=day.food_kcal,
                exercise_kcal=day.exercise_kcal,
                balance_kcal=day.balance_kcal,
                sleep_hours=day.sleep_hours,
                has_food=day.has_food,
                has_exercise=day.has_exercise,
            )
            for day in metrics.days
        ],
        days_with_food=metrics.days_with_food,
        days_with_exercise=metrics.days_with_exercise,
        days_with_sleep=metrics.days_with_sleep,
        total_food_kcal=metrics.total_food_kcal,
        average_food_kcal=metrics.average_food_kcal,
        total_exercise_kcal=metrics.total_exercise_kcal,
        average_sleep_hours=metrics.average_sleep_hours,
        average_balance_kcal=metrics.average_balance_kcal,
        weight_change_kg=metrics.weight_change_kg,
        can_review=can_review,
        has_previous_review=has_previous_review,
        review=_review_response(review),
    )


def _review_response(summary: WeeklySummary | None) -> WeekReviewResponse | None:
    if summary is None:
        return None

    return WeekReviewResponse(
        week_start=summary.week_start,
        generated_at=summary.generated_at,
        is_final=summary.is_final,
        headline=summary.headline,
        observations=observations_of(summary),
        comparison=summary.comparison,
        watch_out=summary.watch_out,
    )


async def _metrics(
    user: User,
    monday: date,
    meals: MealService,
    exercises: ExerciseService,
    sleep: SleepService,
    weights: WeightService,
    profiles: ProfileService,
) -> WeekMetrics:
    today = local_log_date(utc_now(), user.timezone)
    profile = await profiles.get_profile(user)

    days: list[DayMetrics] = []
    for offset in range(DAYS_IN_WEEK):
        day = monday + timedelta(days=offset)
        totals = await meals.daily_totals(user, day)
        performed = await exercises.list_exercises(user, day)
        burned = sum((item.counted_calories for item in performed), Decimal("0"))

        night = await sleep.night_of(user, day)
        balance = energy_balance(
            consumed_kcal=totals.totals.kcal,
            exercise_kcal=burned,
            exercise_minutes=sum(item.duration_minutes for item in performed),
            daily_target_kcal=profile.daily_calorie_target,
            weight_kg=profile.current_weight_kg,
            height_cm=profile.height_cm,
            birth_date=profile.birth_date,
            biological_sex=profile.biological_sex,
            activity_level=profile.activity_level,
            today=day,
        )

        days.append(
            DayMetrics(
                day=day,
                food_kcal=totals.totals.kcal,
                exercise_kcal=burned,
                balance_kcal=balance.balance_kcal,
                sleep_hours=night.hours if night is not None else None,
                has_food=totals.meal_count > 0,
                has_exercise=bool(performed),
                is_future=day > today,
            )
        )

    change = await _weight_change(user, monday, weights)
    return build_week_metrics(monday, days, today, weight_change_kg=change)


async def _weight_change(user: User, monday: date, weights: WeightService) -> Decimal | None:
    """How the smoothed trend moved across the week, or nothing without both ends.

    Two readings in the same week is the least that can show a direction; one is
    a single measurement, and a measurement is not a change.
    """
    history = await weights.history(user)
    sunday = monday + timedelta(days=DAYS_IN_WEEK - 1)
    within = [point for point in history.points if monday <= point.measured_on <= sunday]
    if len(within) < 2:
        return None

    return within[-1].trend_kg - within[0].trend_kg
