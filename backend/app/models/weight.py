from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WeightEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "weight_entries"
    __table_args__ = (Index("ix_weight_entries_user_id_measured_at", "user_id", "measured_at"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime())
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
