"""book metadata, category, google id, authors json

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("subtitle", sa.String(length=500), nullable=True))
    op.add_column("books", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("books", sa.Column("publisher", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("published_date", sa.String(length=64), nullable=True))
    op.add_column("books", sa.Column("category", sa.String(length=64), nullable=True))
    op.add_column("books", sa.Column("google_books_id", sa.String(length=64), nullable=True))
    op.add_column("books", sa.Column("authors_json", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_books_category"), "books", ["category"], unique=False)
    op.create_index(op.f("ix_books_google_books_id"), "books", ["google_books_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_books_google_books_id"), table_name="books")
    op.drop_index(op.f("ix_books_category"), table_name="books")
    op.drop_column("books", "authors_json")
    op.drop_column("books", "google_books_id")
    op.drop_column("books", "category")
    op.drop_column("books", "published_date")
    op.drop_column("books", "publisher")
    op.drop_column("books", "description")
    op.drop_column("books", "subtitle")
