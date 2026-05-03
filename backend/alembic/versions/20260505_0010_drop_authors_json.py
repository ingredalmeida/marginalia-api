"""drop authors_json from books (single author via author_id)

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("books", "authors_json")


def downgrade() -> None:
    op.add_column("books", sa.Column("authors_json", sa.JSON(), nullable=True))
