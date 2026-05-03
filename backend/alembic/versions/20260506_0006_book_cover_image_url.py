"""optional book cover image URL

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("books", "cover_image_url")
