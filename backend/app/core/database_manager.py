"""
Multi-tenant database connection manager.
Manages connections to the registry database and school-specific databases.
"""
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Registry database (stores school metadata)
registry_engine = create_async_engine(
    settings.REGISTRY_DATABASE_URL,
    echo=True,
    future=True
)

RegistrySessionLocal = async_sessionmaker(
    registry_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Cache for school-specific database engines
_school_engines: Dict[str, AsyncEngine] = {}
_school_sessions: Dict[str, async_sessionmaker] = {}

async def get_registry_db():
    """Get a session to the registry database."""
    async with RegistrySessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def build_database_url(
    database_name: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """Build a database URL for a school-specific database."""
    host = host or settings.DEFAULT_DB_HOST
    port = port or settings.DEFAULT_DB_PORT
    user = user or settings.DEFAULT_DB_USER
    password = password or settings.DEFAULT_DB_PASSWORD
    
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database_name}"

async def get_school_db(
    database_name: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
):
    """
    Get a session to a school-specific database.
    Creates and caches the engine if it doesn't exist.
    """
    # Create a cache key
    cache_key = f"{host or settings.DEFAULT_DB_HOST}:{port or settings.DEFAULT_DB_PORT}:{database_name}"
    
    # Get or create the engine
    if cache_key not in _school_engines:
        database_url = build_database_url(database_name, host, port, user, password)
        _school_engines[cache_key] = create_async_engine(
            database_url,
            echo=True,
            future=True
        )
        _school_sessions[cache_key] = async_sessionmaker(
            _school_engines[cache_key],
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info(f"Created database engine for school database: {database_name}")
    
    async with _school_sessions[cache_key]() as session:
        try:
            yield session
        finally:
            await session.close()

async def close_all_connections():
    """Close all database connections. Useful for cleanup."""
    for engine in _school_engines.values():
        await engine.dispose()
    _school_engines.clear()
    _school_sessions.clear()
    await registry_engine.dispose()
