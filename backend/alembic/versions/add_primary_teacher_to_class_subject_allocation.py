"""add primary_teacher_id to class_subject_allocations

Revision ID: add_primary_teacher_allocation
Revises: add_break_durations
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_primary_teacher_allocation'
down_revision: Union[str, None] = 'add_break_durations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add primary_teacher_id column to class_subject_allocations
    op.add_column('class_subject_allocations', sa.Column('primary_teacher_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'class_subject_allocations_primary_teacher_id_fkey',
        'class_subject_allocations',
        'teachers',
        ['primary_teacher_id'],
        ['id']
    )
    op.create_index('ix_class_subject_allocations_primary_teacher_id', 'class_subject_allocations', ['primary_teacher_id'])


def downgrade() -> None:
    # Remove primary_teacher_id column
    op.drop_index('ix_class_subject_allocations_primary_teacher_id', table_name='class_subject_allocations')
    op.drop_constraint('class_subject_allocations_primary_teacher_id_fkey', 'class_subject_allocations', type_='foreignkey')
    op.drop_column('class_subject_allocations', 'primary_teacher_id')

