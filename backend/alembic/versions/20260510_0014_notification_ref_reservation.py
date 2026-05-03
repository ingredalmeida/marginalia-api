"""notification ref_reservation_id for actionable hold notices

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("ref_reservation_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_notifications_ref_reservation_id",
        "notifications",
        "reservations",
        ["ref_reservation_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_notifications_ref_reservation_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "ref_reservation_id")
