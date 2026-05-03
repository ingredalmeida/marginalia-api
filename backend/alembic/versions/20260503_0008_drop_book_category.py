"""remove book category column

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_books_category"), table_name="books")
    op.drop_column("books", "category")


def downgrade() -> None:
    op.add_column("books", sa.Column("category", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_books_category"), "books", ["category"], unique=False)
