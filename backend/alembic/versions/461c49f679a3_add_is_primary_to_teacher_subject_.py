"""add_is_primary_to_teacher_subject_capability

Revision ID: 461c49f679a3
Revises: add_teacher_classroom
Create Date: 2025-12-09 11:28:27.600623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '461c49f679a3'
down_revision: Union[str, None] = 'add_teacher_classroom'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teacher_subject_capabilities', sa.Column('is_primary', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('teacher_subject_capabilities', 'is_primary')

