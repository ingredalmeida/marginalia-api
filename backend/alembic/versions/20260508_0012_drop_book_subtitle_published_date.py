"""drop book subtitle and published_date

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("books", "published_date")
    op.drop_column("books", "subtitle")


def downgrade() -> None:
    op.add_column("books", sa.Column("subtitle", sa.String(length=500), nullable=True))
    op.add_column("books", sa.Column("published_date", sa.String(length=64), nullable=True))
