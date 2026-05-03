"""drop google_books_id from books

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_books_google_books_id"), table_name="books")
    op.drop_column("books", "google_books_id")


def downgrade() -> None:
    op.add_column("books", sa.Column("google_books_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_books_google_books_id"), "books", ["google_books_id"], unique=True)
