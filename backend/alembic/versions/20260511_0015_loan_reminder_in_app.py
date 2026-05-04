"""loan_reminder_logs in_app_sent_at for in-app due reminders

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "loan_reminder_logs",
        sa.Column("in_app_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("loan_reminder_logs", "in_app_sent_at")
