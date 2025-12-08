"""add teacher classroom association

Revision ID: add_teacher_classroom
Revises: f54fd6d20054
Create Date: 2025-12-08 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_teacher_classroom'
down_revision: Union[str, None] = 'f54fd6d20054'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create association table for many-to-many relationship
    op.create_table(
        'teacher_classroom_association',
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ),
        sa.PrimaryKeyConstraint('teacher_id', 'classroom_id')
    )


def downgrade() -> None:
    op.drop_table('teacher_classroom_association')

