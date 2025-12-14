"""add_tenant_id_to_all_tables

Revision ID: 3e765b7e2d53
Revises: 316b16895072
Create Date: 2025-12-14 12:45:00.000000

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3e765b7e2d53'
down_revision: Union[str, None] = '316b16895072'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get default tenant ID from environment variable
    default_tenant_id = os.getenv('MIGRATION_DEFAULT_TENANT_ID')
    if not default_tenant_id:
        raise ValueError(
            "MIGRATION_DEFAULT_TENANT_ID environment variable must be set. "
            "This should be the UUID of the default tenant to assign to existing rows."
        )
    
    # List of tenant-owned tables and their unique constraint columns
    tenant_tables = [
        ('users', ['email']),
        ('schools', ['code']),
        ('school_settings', []),
        ('teachers', []),
        ('subjects', []),
        ('class_groups', []),
        ('classrooms', []),
        ('grade_levels', []),
        ('timetables', []),
        ('timetable_entries', []),
        ('teacher_absences', []),
        ('substitutions', []),
    ]
    
    # Step 1: Add tenant_id column (nullable) to all tables
    for table_name, unique_cols in tenant_tables:
        op.add_column(
            table_name,
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True)
        )
        # Create index on tenant_id
        op.create_index(
            f'ix_{table_name}_tenant_id',
            table_name,
            ['tenant_id']
        )
    
    # Step 2: Backfill tenant_id with default tenant
    for table_name, _ in tenant_tables:
        op.execute(
            f"UPDATE {table_name} SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL"
        )
    
    # Step 3: Make tenant_id NOT NULL
    for table_name, _ in tenant_tables:
        op.alter_column(table_name, 'tenant_id', nullable=False)
    
    # Step 4: Add foreign key constraints
    for table_name, _ in tenant_tables:
        op.create_foreign_key(
            f'fk_{table_name}_tenant_id',
            table_name,
            'tenants',
            ['tenant_id'],
            ['id']
        )
    
    # Step 5: Update unique constraints to include tenant_id
    # Drop old unique constraints and create new composite ones
    
    # Users: email should be unique per tenant
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_tenant_email', 'users', ['tenant_id', 'email'], unique=True)
    
    # Schools: code should be unique per tenant
    op.drop_index('ix_schools_code', table_name='schools')
    op.create_index('ix_schools_tenant_code', 'schools', ['tenant_id', 'code'], unique=True)
    
    # Composite indexes for commonly filtered columns
    # Use raw SQL with IF NOT EXISTS to avoid errors if indexes already exist
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users (tenant_id, id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_teachers_tenant_id ON teachers (tenant_id, id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subjects_tenant_id ON subjects (tenant_id, id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_class_groups_tenant_id ON class_groups (tenant_id, id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_timetables_tenant_id ON timetables (tenant_id, id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_timetable_entries_tenant_id ON timetable_entries (tenant_id, timetable_id)")


def downgrade() -> None:
    # Remove composite indexes
    op.drop_index('ix_timetable_entries_tenant_id', table_name='timetable_entries')
    op.drop_index('ix_timetables_tenant_id', table_name='timetables')
    op.drop_index('ix_class_groups_tenant_id', table_name='class_groups')
    op.drop_index('ix_subjects_tenant_id', table_name='subjects')
    op.drop_index('ix_teachers_tenant_id', table_name='teachers')
    op.drop_index('ix_users_tenant_id', table_name='users')
    
    # Restore old unique constraints
    op.drop_index('ix_schools_tenant_code', table_name='schools')
    op.create_index('ix_schools_code', 'schools', ['code'], unique=True)
    op.drop_index('ix_users_tenant_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Remove foreign keys
    tenant_tables = [
        'users', 'schools', 'school_settings', 'teachers', 'subjects',
        'class_groups', 'classrooms', 'grade_levels', 'timetables',
        'timetable_entries', 'teacher_absences', 'substitutions'
    ]
    
    for table_name in tenant_tables:
        op.drop_constraint(f'fk_{table_name}_tenant_id', table_name, type_='foreignkey')
        op.drop_index(f'ix_{table_name}_tenant_id', table_name=table_name)
        op.drop_column(table_name, 'tenant_id')
