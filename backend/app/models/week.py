from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WeeklySummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A written look back at one week, kept so it can be compared with the next.

    The figures are stored alongside the words: a summary that recalculated
    itself later would stop matching what it says.
    """

    __tablename__ = "weekly_summaries"
    __table_args__ = (
        Index("uq_weekly_summaries_user_id_week_start", "user_id", "week_start", unique=True),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[date] = mapped_column(Date())
    generated_at: Mapped[datetime] = mapped_column(DateTime())
    #: True once the week was over when this was written, so it will not change.
    is_final: Mapped[bool] = mapped_column(Boolean(), default=False)

    headline: Mapped[str] = mapped_column(Text())
    observations_json: Mapped[str] = mapped_column(Text())
    comparison: Mapped[str | None] = mapped_column(Text(), nullable=True)
    watch_out: Mapped[str | None] = mapped_column(Text(), nullable=True)

    days_with_food: Mapped[int] = mapped_column()
    days_with_exercise: Mapped[int] = mapped_column()
    days_with_sleep: Mapped[int] = mapped_column()
    total_food_kcal: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    average_food_kcal: Mapped[Decimal | None] = mapped_column(Numeric(9, 2), nullable=True)
    total_exercise_kcal: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    average_sleep_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    average_balance_kcal: Mapped[Decimal | None] = mapped_column(Numeric(9, 2), nullable=True)
    weight_change_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
