from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SleepQuality


class SleepEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A night's sleep, filed under the day it ended.

    A night starting on Tuesday and ending on Wednesday is Wednesday's, which is
    the day it affects and the day someone looks at it.
    """

    __tablename__ = "sleep_entries"
    __table_args__ = (Index("ix_sleep_entries_user_id_ended_at", "user_id", "ended_at"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime())
    ended_at: Mapped[datetime] = mapped_column(DateTime())
    quality: Mapped[SleepQuality | None] = mapped_column(
        Enum(SleepQuality, name="sleep_quality", native_enum=False, create_constraint=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
