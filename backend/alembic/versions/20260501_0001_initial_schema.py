"""initial schema users authors books loans

Revision ID: 0001
Revises:
Create Date: 2026-05-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_authors_name"), "authors", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )
    op.create_index(op.f("ix_books_author_id"), "books", ["author_id"], unique=False)
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)

    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("borrowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fine_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_loans_book_id"), "loans", ["book_id"], unique=False)
    op.create_index(op.f("ix_loans_user_id"), "loans", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_loans_user_id"), table_name="loans")
    op.drop_index(op.f("ix_loans_book_id"), table_name="loans")
    op.drop_table("loans")
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_index(op.f("ix_books_author_id"), table_name="books")
    op.drop_table("books")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_authors_name"), table_name="authors")
    op.drop_table("authors")
