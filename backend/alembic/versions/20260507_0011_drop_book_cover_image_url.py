"""drop book cover_image_url

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("books", "cover_image_url")


def downgrade() -> None:
    op.add_column(
        "books",
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
    )
