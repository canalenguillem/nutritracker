import json
from dataclasses import dataclass
from datetime import date, timedelta

from app.models.base import utc_now
from app.models.user import User
from app.models.week import WeeklySummary
from app.repositories.weekly_summaries import WeeklySummaryRepository
from app.services.week_metrics import DAYS_IN_WEEK, WeekMetrics, monday_of
from app.services.week_review import (
    WeekReview,
    WeekReviewDisabledError,
    WeekReviewer,
)


class NothingToReviewError(Exception):
    pass


class WeekAlreadyClosedError(Exception):
    """A finished week was reviewed once and keeps that review."""


@dataclass(frozen=True)
class StoredReview:
    week_start: date
    generated_at: date
    is_final: bool
    review: WeekReview
    metrics: WeekMetrics


class WeekService:
    def __init__(
        self,
        summaries: WeeklySummaryRepository,
        reviewer: WeekReviewer | None,
    ) -> None:
        self._summaries = summaries
        self._reviewer = reviewer

    @property
    def can_review(self) -> bool:
        return self._reviewer is not None

    async def stored(self, user: User, week_start: date) -> WeeklySummary | None:
        return await self._summaries.get_for_week(user.id, monday_of(week_start))

    async def review_week(
        self,
        user: User,
        metrics: WeekMetrics,
        previous: WeekMetrics | None,
        previous_stored: WeeklySummary | None,
    ) -> WeeklySummary:
        """Write the week up, or hand back the one already written and closed."""
        existing = await self._summaries.get_for_week(user.id, metrics.week_start)
        if existing is not None and existing.is_final:
            raise WeekAlreadyClosedError(metrics.week_start.isoformat())

        if metrics.days_with_food == 0 and metrics.days_with_exercise == 0:
            raise NothingToReviewError(metrics.week_start.isoformat())

        if self._reviewer is None:
            raise WeekReviewDisabledError

        # Only a week that was itself written up is worth comparing against: an
        # unreviewed one has no words to set beside these.
        comparable = previous if previous_stored is not None else None
        review = await self._reviewer.review(metrics, comparable, user.locale)

        is_new = existing is None
        if existing is None:
            existing = WeeklySummary(user_id=user.id, week_start=metrics.week_start)

        # Filled before it reaches the session: the row has no nullable columns
        # to be written into afterwards.
        _apply(existing, review, metrics)
        if is_new:
            await self._summaries.add(existing)

        return existing

    async def delete(self, user: User, week_start: date) -> None:
        existing = await self._summaries.get_for_week(user.id, monday_of(week_start))
        if existing is not None:
            await self._summaries.remove(existing)


def _apply(summary: WeeklySummary, review: WeekReview, metrics: WeekMetrics) -> None:
    summary.generated_at = utc_now()
    summary.is_final = metrics.is_complete
    summary.headline = review.headline
    summary.observations_json = json.dumps(review.observations, ensure_ascii=False)
    summary.comparison = review.comparison
    summary.watch_out = review.watch_out
    summary.days_with_food = metrics.days_with_food
    summary.days_with_exercise = metrics.days_with_exercise
    summary.days_with_sleep = metrics.days_with_sleep
    summary.total_food_kcal = metrics.total_food_kcal
    summary.average_food_kcal = metrics.average_food_kcal
    summary.total_exercise_kcal = metrics.total_exercise_kcal
    summary.average_sleep_hours = metrics.average_sleep_hours
    summary.average_balance_kcal = metrics.average_balance_kcal
    summary.weight_change_kg = metrics.weight_change_kg


def observations_of(summary: WeeklySummary) -> list[str]:
    try:
        stored = json.loads(summary.observations_json)
    except json.JSONDecodeError:
        return []

    return [str(line) for line in stored] if isinstance(stored, list) else []


def previous_week_of(week_start: date) -> date:
    return week_start - timedelta(days=DAYS_IN_WEEK)
