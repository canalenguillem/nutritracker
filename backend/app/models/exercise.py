from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ExerciseIntensity, ExerciseSource
from app.models.meal import DailyLog


class Exercise(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "exercises"
    __table_args__ = (Index("ix_exercises_user_id_performed_at", "user_id", "performed_at"),)

    daily_log_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_logs.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    activity_name: Mapped[str] = mapped_column(String(120))
    duration_minutes: Mapped[int] = mapped_column()
    intensity: Mapped[ExerciseIntensity] = mapped_column(
        Enum(
            ExerciseIntensity, name="exercise_intensity", native_enum=False, create_constraint=True
        )
    )
    # Both are kept: a watch or a machine may disagree with the estimate, and
    # the person decides which number counts.
    estimated_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    confirmed_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    source: Mapped[ExerciseSource] = mapped_column(
        Enum(ExerciseSource, name="exercise_source", native_enum=False, create_constraint=True)
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime())
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    daily_log: Mapped[DailyLog] = relationship()

    @property
    def counted_calories(self) -> Decimal:
        """What the balance should use: the person's number wins."""
        if self.confirmed_calories is not None:
            return self.confirmed_calories
        # Two places throughout, so the API never mixes "0" with "0.00".
        return self.estimated_calories or Decimal("0.00")
