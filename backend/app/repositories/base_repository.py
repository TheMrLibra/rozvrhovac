from typing import Generic, TypeVar, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


def tenant_query(stmt, model_class, tenant_id: UUID):
    """
    Helper function to add tenant filtering to a SQLAlchemy query.
    
    Args:
        stmt: SQLAlchemy select/update/delete statement
        model_class: The model class
        tenant_id: UUID of the tenant
    
    Returns:
        Modified statement with tenant filter added
    """
    if hasattr(model_class, 'tenant_id'):
        return stmt.where(model_class.tenant_id == tenant_id)
    return stmt


class BaseRepository(Generic[ModelType]):
    """
    Base repository with tenant-aware CRUD operations.
    
    All methods require tenant_id to ensure tenant isolation.
    """
    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model
    
    def _has_tenant_id(self) -> bool:
        """Check if model has tenant_id column."""
        return hasattr(self.model, 'tenant_id')
    
    async def get_by_id(self, id: int, tenant_id: UUID) -> Optional[ModelType]:
        """Get entity by ID, filtered by tenant."""
        stmt = select(self.model).where(self.model.id == id)
        if self._has_tenant_id():
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities, filtered by tenant."""
        stmt = select(self.model)
        if self._has_tenant_id():
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, obj: ModelType, tenant_id: Optional[UUID] = None) -> ModelType:
        """
        Create entity. If tenant_id is provided and model supports it, ensure it's set.
        Note: tenant_id should be set on the object before calling create().
        """
        # Ensure tenant_id is set if model supports it
        if self._has_tenant_id() and tenant_id:
            obj.tenant_id = tenant_id
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def update(self, id: int, tenant_id: UUID, **kwargs) -> Optional[ModelType]:
        """Update entity, ensuring tenant ownership."""
        stmt = update(self.model).where(self.model.id == id)
        if self._has_tenant_id():
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        await self.db.execute(stmt.values(**kwargs))
        await self.db.commit()
        return await self.get_by_id(id, tenant_id)
    
    async def delete(self, id: int, tenant_id: UUID) -> bool:
        """Delete entity, ensuring tenant ownership."""
        stmt = delete(self.model).where(self.model.id == id)
        if self._has_tenant_id():
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

