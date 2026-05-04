"""loan_reminder_logs.loan_due_at_utc_snapshot for overdue idempotency invalidation

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "loan_reminder_logs",
        sa.Column("loan_due_at_utc_snapshot", sa.Date(), nullable=True),
    )
    op.execute(
        """
        UPDATE loan_reminder_logs AS l
        SET loan_due_at_utc_snapshot = ((loans.due_at AT TIME ZONE 'UTC')::date)
        FROM loans
        WHERE l.loan_id = loans.id
          AND l.reminder_kind = 'overdue_fine_daily'
        """
    )


def downgrade() -> None:
    op.drop_column("loan_reminder_logs", "loan_due_at_utc_snapshot")
