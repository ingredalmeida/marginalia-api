"""add user hashed_password

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Bcrypt hash of "ChangeMe!123" — existing rows should reset password in real deploys
_PLACEHOLDER_HASH = "$2b$12$nKxE8BdMM0f8o7ErwzczyenheGBl.SB7egV.xLOqtwUpTlXeA9s8u"  # noqa: S105


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
    )
    bind = op.get_bind()
    bind.execute(
        text("UPDATE users SET hashed_password = :h WHERE hashed_password IS NULL"),
        {"h": _PLACEHOLDER_HASH},
    )
    op.alter_column("users", "hashed_password", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
