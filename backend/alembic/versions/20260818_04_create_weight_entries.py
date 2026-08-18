"""Create the weight entries table.

Revision ID: 20260818_04
Revises: 20260818_03
Create Date: 2026-08-18 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260818_04"
down_revision: str | Sequence[str] | None = "20260818_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weight_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_weight_entries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weight_entries")),
    )
    op.create_index(op.f("ix_weight_entries_user_id"), "weight_entries", ["user_id"])
    op.create_index(
        "ix_weight_entries_user_id_measured_at", "weight_entries", ["user_id", "measured_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_weight_entries_user_id_measured_at", table_name="weight_entries")
    op.drop_index(op.f("ix_weight_entries_user_id"), table_name="weight_entries")
    op.drop_table("weight_entries")
