"""Create the sleep entries table.

Revision ID: 20260819_05
Revises: 20260818_04
Create Date: 2026-08-19 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260819_05"
down_revision: str | Sequence[str] | None = "20260818_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    sleep_quality = sa.Enum(
        "POOR",
        "FAIR",
        "GOOD",
        "VERY_GOOD",
        name="sleep_quality",
        native_enum=False,
        create_constraint=True,
    )

    op.create_table(
        "sleep_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=False),
        sa.Column("quality", sleep_quality, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_sleep_entries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sleep_entries")),
    )
    op.create_index(op.f("ix_sleep_entries_user_id"), "sleep_entries", ["user_id"])
    op.create_index("ix_sleep_entries_user_id_ended_at", "sleep_entries", ["user_id", "ended_at"])


def downgrade() -> None:
    op.drop_index("ix_sleep_entries_user_id_ended_at", table_name="sleep_entries")
    op.drop_index(op.f("ix_sleep_entries_user_id"), table_name="sleep_entries")
    op.drop_table("sleep_entries")
