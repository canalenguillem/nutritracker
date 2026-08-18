from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MealSource, MealStatus, MealType


class DailyLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "daily_logs"
    __table_args__ = (Index("uq_daily_logs_user_id_log_date", "user_id", "log_date", unique=True),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date())
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    meals: Mapped[list["Meal"]] = relationship(
        back_populates="daily_log", cascade="all, delete-orphan"
    )


class Meal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_id_eaten_at", "user_id", "eaten_at"),)

    daily_log_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_logs.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_type: Mapped[MealType] = mapped_column(
        Enum(MealType, name="meal_type", native_enum=False, create_constraint=True)
    )
    eaten_at: Mapped[datetime] = mapped_column(DateTime())
    source: Mapped[MealSource] = mapped_column(
        Enum(MealSource, name="meal_source", native_enum=False, create_constraint=True)
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    total_kcal: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    carbohydrates_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    status: Mapped[MealStatus] = mapped_column(
        Enum(MealStatus, name="meal_status", native_enum=False, create_constraint=True)
    )

    daily_log: Mapped[DailyLog] = relationship(back_populates="meals")
    items: Mapped[list["MealItem"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="MealItem.created_at",
        lazy="selectin",
    )


class MealItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "meal_items"

    meal_id: Mapped[UUID] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    unit: Mapped[str] = mapped_column(String(32))
    kcal: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    carbohydrates_g: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    assumptions_json: Mapped[str | None] = mapped_column(Text(), nullable=True)
    user_confirmed: Mapped[bool] = mapped_column(default=False)

    meal: Mapped[Meal] = relationship(back_populates="items")
