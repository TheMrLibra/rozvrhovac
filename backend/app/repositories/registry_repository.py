"""
Repository for accessing the school registry.
This repository works with the registry database.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.registry import SchoolRegistry
from app.repositories.base_repository import BaseRepository

class RegistryRepository(BaseRepository[SchoolRegistry]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SchoolRegistry)
    
    async def get_by_code(self, code: str) -> Optional[SchoolRegistry]:
        """Get school registry entry by school code."""
        result = await self.db.execute(
            select(SchoolRegistry).where(SchoolRegistry.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, registry_id: int) -> Optional[SchoolRegistry]:
        """Get school registry entry by registry ID."""
        result = await self.db.execute(
            select(SchoolRegistry).where(SchoolRegistry.id == registry_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_school_id(self, school_id: int) -> Optional[SchoolRegistry]:
        """Get school registry entry by school_id (maps to School.id in school database)."""
        result = await self.db.execute(
            select(SchoolRegistry).where(SchoolRegistry.school_id == school_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_database_name(self, database_name: str) -> Optional[SchoolRegistry]:
        """Get school registry entry by database name."""
        result = await self.db.execute(
            select(SchoolRegistry).where(SchoolRegistry.database_name == database_name)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> list[SchoolRegistry]:
        """Get all active school registry entries."""
        result = await self.db.execute(
            select(SchoolRegistry).where(SchoolRegistry.is_active == True)
        )
        return list(result.scalars().all())

