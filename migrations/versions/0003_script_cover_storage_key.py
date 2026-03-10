"""0003_script_cover_storage_key

Revision ID: 0003_script_cover_storage_key
Revises: 0002_booking_match_model
Create Date: 2026-03-08 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_script_cover_storage_key"
down_revision: Union[str, Sequence[str], None] = "0002_booking_match_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("script", sa.Column("cover_storage_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("script", "cover_storage_key")
