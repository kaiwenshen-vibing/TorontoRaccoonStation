"""0004_pic_key_standardization

Revision ID: 0004_pic_key_standardization
Revises: 0003_script_cover_storage_key
Create Date: 2026-03-08 00:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_pic_key_standardization"
down_revision: Union[str, Sequence[str], None] = "0003_script_cover_storage_key"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("script", "cover_storage_key", new_column_name="pic_storage_key")
    op.add_column("store", sa.Column("pic_storage_key", sa.Text(), nullable=True))
    op.add_column("store_room", sa.Column("pic_storage_key", sa.Text(), nullable=True))
    op.add_column("dm", sa.Column("pic_storage_key", sa.Text(), nullable=True))
    op.add_column("client", sa.Column("pic_storage_key", sa.Text(), nullable=True))
    op.add_column("script_character", sa.Column("pic_storage_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("script_character", "pic_storage_key")
    op.drop_column("client", "pic_storage_key")
    op.drop_column("dm", "pic_storage_key")
    op.drop_column("store_room", "pic_storage_key")
    op.drop_column("store", "pic_storage_key")
    op.alter_column("script", "pic_storage_key", new_column_name="cover_storage_key")
