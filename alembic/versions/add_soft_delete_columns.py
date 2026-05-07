"""add soft delete columns

Revision ID: a2b3c4d5e6f7
Revises: 391570fb9801
Create Date: 2026-05-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '391570fb9801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('image_assets', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('image_assets', 'deleted_at')
    op.drop_column('projects', 'deleted_at')
