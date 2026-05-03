"""reservations table and loan renewal_count

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservations_book_id", "reservations", ["book_id"])
    op.create_index("ix_reservations_user_id", "reservations", ["user_id"])
    op.add_column(
        "loans",
        sa.Column("renewal_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.alter_column("loans", "renewal_count", server_default=None)


def downgrade() -> None:
    op.drop_column("loans", "renewal_count")
    op.drop_index("ix_reservations_user_id", table_name="reservations")
    op.drop_index("ix_reservations_book_id", table_name="reservations")
    op.drop_table("reservations")
