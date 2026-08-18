"""Create the exercise table.

Revision ID: 20260818_03
Revises: 20260818_02
Create Date: 2026-08-18 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260818_03"
down_revision: str | Sequence[str] | None = "20260818_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    exercise_intensity = sa.Enum(
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
        name="exercise_intensity",
        native_enum=False,
        create_constraint=True,
    )
    exercise_source = sa.Enum(
        "MANUAL",
        "DEVICE",
        "IMPORTED",
        name="exercise_source",
        native_enum=False,
        create_constraint=True,
    )

    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("daily_log_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_name", sa.String(length=120), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("intensity", exercise_intensity, nullable=False),
        sa.Column("estimated_calories", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("confirmed_calories", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("source", exercise_source, nullable=False),
        sa.Column("performed_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["daily_log_id"],
            ["daily_logs.id"],
            name=op.f("fk_exercises_daily_log_id_daily_logs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_exercises_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercises")),
    )
    op.create_index(op.f("ix_exercises_daily_log_id"), "exercises", ["daily_log_id"])
    op.create_index(op.f("ix_exercises_user_id"), "exercises", ["user_id"])
    op.create_index("ix_exercises_user_id_performed_at", "exercises", ["user_id", "performed_at"])


def downgrade() -> None:
    op.drop_index("ix_exercises_user_id_performed_at", table_name="exercises")
    op.drop_index(op.f("ix_exercises_user_id"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_daily_log_id"), table_name="exercises")
    op.drop_table("exercises")
