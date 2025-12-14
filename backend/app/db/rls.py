"""
PostgreSQL Row Level Security (RLS) preparation module.

This module contains functions and SQL templates for enabling RLS on tenant-owned tables.
RLS is NOT enabled by default - these are preparation functions for future use.

When RLS is enabled:
1. Call set_tenant_context() before each database operation
2. Enable RLS policies on all tenant-owned tables
3. Remove manual tenant filtering from repositories (RLS handles it)
"""
from uuid import UUID
from sqlalchemy.engine import Connection
from typing import List


def set_tenant_context(connection: Connection, tenant_id: UUID) -> None:
    """
    Set tenant context on a database connection for RLS.
    
    This sets a session-local variable that RLS policies can use to filter rows.
    
    Args:
        connection: SQLAlchemy connection object
        tenant_id: UUID of the tenant
    
    Example:
        ```python
        async with AsyncSessionLocal() as session:
            set_tenant_context(session.connection(), tenant_id)
            # All queries will now be filtered by RLS policies
        ```
    """
    connection.execute(
        f"SET LOCAL app.tenant_id = '{tenant_id}'"
    )


def get_rls_policy_sql(table_name: str) -> str:
    """
    Generate RLS policy SQL for a tenant-owned table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        SQL string for creating the policy (not executed automatically)
    
    Example:
        ```sql
        CREATE POLICY tenant_isolation ON teachers
          USING (tenant_id = current_setting('app.tenant_id')::uuid);
        ```
    """
    return f"""
        CREATE POLICY tenant_isolation ON {table_name}
          USING (tenant_id = current_setting('app.tenant_id')::uuid);
    """


def get_enable_rls_sql(table_name: str) -> str:
    """
    Generate SQL to enable RLS on a table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        SQL string for enabling RLS (not executed automatically)
    """
    return f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"


def get_disable_rls_sql(table_name: str) -> str:
    """
    Generate SQL to disable RLS on a table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        SQL string for disabling RLS (not executed automatically)
    """
    return f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;"


# List of tenant-owned tables that will need RLS policies
TENANT_OWNED_TABLES: List[str] = [
    "users",
    "schools",
    "school_settings",
    "teachers",
    "teacher_subject_capabilities",
    "subjects",
    "class_subject_allocations",
    "class_groups",
    "classrooms",
    "grade_levels",
    "timetables",
    "timetable_entries",
    "teacher_absences",
    "substitutions",
]


def get_all_rls_setup_sql() -> List[str]:
    """
    Get all SQL statements needed to enable RLS on all tenant-owned tables.
    
    Returns:
        List of SQL strings (not executed automatically)
    
    Usage:
        ```python
        sql_statements = get_all_rls_setup_sql()
        for sql in sql_statements:
            connection.execute(sql)
        ```
    """
    statements = []
    
    # First, ensure the app.tenant_id setting can be used
    statements.append("""
        -- Create a function to validate tenant_id setting
        CREATE OR REPLACE FUNCTION check_tenant_context()
        RETURNS void AS $$
        BEGIN
            IF current_setting('app.tenant_id', true) IS NULL THEN
                RAISE EXCEPTION 'app.tenant_id must be set before querying tenant-owned tables';
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Enable RLS on all tables
    for table in TENANT_OWNED_TABLES:
        statements.append(get_enable_rls_sql(table))
        statements.append(get_rls_policy_sql(table))
    
    return statements


def get_all_rls_teardown_sql() -> List[str]:
    """
    Get all SQL statements needed to disable RLS on all tenant-owned tables.
    
    Returns:
        List of SQL strings (not executed automatically)
    """
    statements = []
    
    # Drop policies
    for table in TENANT_OWNED_TABLES:
        statements.append(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
    
    # Disable RLS
    for table in TENANT_OWNED_TABLES:
        statements.append(get_disable_rls_sql(table))
    
    # Drop function
    statements.append("DROP FUNCTION IF EXISTS check_tenant_context();")
    
    return statements

