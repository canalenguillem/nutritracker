"""Create meal tables.

Revision ID: 20260818_02
Revises: 20260717_01
Create Date: 2026-08-18 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260818_02"
down_revision: str | Sequence[str] | None = "20260717_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    meal_type = sa.Enum(
        "BREAKFAST",
        "LUNCH",
        "DINNER",
        "SNACK",
        name="meal_type",
        native_enum=False,
        create_constraint=True,
    )
    meal_source = sa.Enum(
        "PHOTO_AI",
        "MANUAL",
        "IMPORTED",
        name="meal_source",
        native_enum=False,
        create_constraint=True,
    )
    meal_status = sa.Enum(
        "PENDING",
        "PROCESSING",
        "NEEDS_REVIEW",
        "CONFIRMED",
        "FAILED",
        "CANCELLED",
        name="meal_status",
        native_enum=False,
        create_constraint=True,
    )

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_daily_logs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_logs")),
    )
    op.create_index(op.f("ix_daily_logs_user_id"), "daily_logs", ["user_id"])
    op.create_index(
        "uq_daily_logs_user_id_log_date", "daily_logs", ["user_id", "log_date"], unique=True
    )

    op.create_table(
        "meals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("daily_log_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("meal_type", meal_type, nullable=False),
        sa.Column("eaten_at", sa.DateTime(), nullable=False),
        sa.Column("source", meal_source, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("total_kcal", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("carbohydrates_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("status", meal_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["daily_log_id"],
            ["daily_logs.id"],
            name=op.f("fk_meals_daily_log_id_daily_logs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_meals_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meals")),
    )
    op.create_index(op.f("ix_meals_daily_log_id"), "meals", ["daily_log_id"])
    op.create_index(op.f("ix_meals_user_id"), "meals", ["user_id"])
    op.create_index("ix_meals_user_id_eaten_at", "meals", ["user_id", "eaten_at"])

    op.create_table(
        "meal_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meal_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("kcal", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("carbohydrates_g", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("assumptions_json", sa.Text(), nullable=True),
        sa.Column("user_confirmed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meal_id"],
            ["meals.id"],
            name=op.f("fk_meal_items_meal_id_meals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_items")),
    )
    op.create_index(op.f("ix_meal_items_meal_id"), "meal_items", ["meal_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_meal_items_meal_id"), table_name="meal_items")
    op.drop_table("meal_items")
    op.drop_index("ix_meals_user_id_eaten_at", table_name="meals")
    op.drop_index(op.f("ix_meals_user_id"), table_name="meals")
    op.drop_index(op.f("ix_meals_daily_log_id"), table_name="meals")
    op.drop_table("meals")
    op.drop_index("uq_daily_logs_user_id_log_date", table_name="daily_logs")
    op.drop_index(op.f("ix_daily_logs_user_id"), table_name="daily_logs")
    op.drop_table("daily_logs")
