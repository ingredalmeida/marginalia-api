"""loan_reminder_logs for due reminder idempotency

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loan_reminder_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("reminder_kind", sa.String(length=32), nullable=False),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("webhook_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["loan_id"], ["loans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "loan_id",
            "due_date",
            "reminder_kind",
            name="uq_loan_reminder_log_loan_due_kind",
        ),
    )
    op.create_index("ix_loan_reminder_logs_loan_id", "loan_reminder_logs", ["loan_id"])


def downgrade() -> None:
    op.drop_index("ix_loan_reminder_logs_loan_id", table_name="loan_reminder_logs")
    op.drop_table("loan_reminder_logs")
