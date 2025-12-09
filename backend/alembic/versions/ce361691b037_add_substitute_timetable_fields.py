"""add_substitute_timetable_fields

Revision ID: ce361691b037
Revises: 461c49f679a3
Create Date: 2025-12-09 11:35:57.803180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce361691b037'
down_revision: Union[str, None] = '461c49f679a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('timetables', sa.Column('is_primary', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('timetables', sa.Column('substitute_for_date', sa.Date(), nullable=True))
    op.add_column('timetables', sa.Column('base_timetable_id', sa.Integer(), sa.ForeignKey('timetables.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('timetables', 'base_timetable_id')
    op.drop_column('timetables', 'substitute_for_date')
    op.drop_column('timetables', 'is_primary')

