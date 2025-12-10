"""add number_of_students to class_groups

Revision ID: add_number_of_students_class
Revises: add_primary_teacher_allocation
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_number_of_students_class'
down_revision: Union[str, None] = 'add_primary_teacher_allocation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add number_of_students column to class_groups
    op.add_column('class_groups', sa.Column('number_of_students', sa.Integer(), nullable=True))
    # Ensure capacity is not null (set default if needed)
    op.alter_column('classrooms', 'capacity', nullable=True, existing_nullable=True)


def downgrade() -> None:
    # Remove number_of_students column
    op.drop_column('class_groups', 'number_of_students')

