"""Create the weekly summaries table.

Revision ID: 20260822_06
Revises: 20260819_05
Create Date: 2026-08-22 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260822_06"
down_revision: str | Sequence[str] | None = "20260819_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("is_final", sa.Boolean(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("observations_json", sa.Text(), nullable=False),
        sa.Column("comparison", sa.Text(), nullable=True),
        sa.Column("watch_out", sa.Text(), nullable=True),
        sa.Column("days_with_food", sa.Integer(), nullable=False),
        sa.Column("days_with_exercise", sa.Integer(), nullable=False),
        sa.Column("days_with_sleep", sa.Integer(), nullable=False),
        sa.Column("total_food_kcal", sa.Numeric(precision=9, scale=2), nullable=False),
        sa.Column("average_food_kcal", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("total_exercise_kcal", sa.Numeric(precision=9, scale=2), nullable=False),
        sa.Column("average_sleep_hours", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("average_balance_kcal", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("weight_change_kg", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_weekly_summaries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weekly_summaries")),
    )
    op.create_index(op.f("ix_weekly_summaries_user_id"), "weekly_summaries", ["user_id"])
    op.create_index(
        "uq_weekly_summaries_user_id_week_start",
        "weekly_summaries",
        ["user_id", "week_start"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_weekly_summaries_user_id_week_start", table_name="weekly_summaries")
    op.drop_index(op.f("ix_weekly_summaries_user_id"), table_name="weekly_summaries")
    op.drop_table("weekly_summaries")
