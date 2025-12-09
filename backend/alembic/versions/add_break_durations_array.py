"""add break_durations array

Revision ID: add_break_durations
Revises: ce361691b037
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_break_durations'
down_revision: Union[str, None] = 'ce361691b037'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add break_durations JSON column
    op.add_column('school_settings', sa.Column('break_durations', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove break_durations column
    op.drop_column('school_settings', 'break_durations')

