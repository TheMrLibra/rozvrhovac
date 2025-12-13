"""set_default_false_for_allow_multiple_in_one_day

Revision ID: ebc5f9a610cb
Revises: f0c0d15322f7
Create Date: 2025-12-13 11:45:02.526742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebc5f9a610cb'
down_revision: Union[str, None] = 'f0c0d15322f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing NULL values to False
    op.execute("UPDATE class_subject_allocations SET allow_multiple_in_one_day = FALSE WHERE allow_multiple_in_one_day IS NULL")
    
    # Set default value and make column NOT NULL
    op.alter_column('class_subject_allocations', 'allow_multiple_in_one_day',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default=sa.false())


def downgrade() -> None:
    # Revert to nullable with no default
    op.alter_column('class_subject_allocations', 'allow_multiple_in_one_day',
                    existing_type=sa.Boolean(),
                    nullable=True,
                    server_default=None)

