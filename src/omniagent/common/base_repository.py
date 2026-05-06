"""Generic async repository pattern for database access."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self._session = session
        self._model_class = model_class

    async def get(self, entity_id: UUID) -> T | None:
        return await self._session.get(self._model_class, entity_id)

    async def list(self, offset: int = 0, limit: int = 50) -> list[T]:
        stmt = select(self._model_class).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._model_class)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self._session.merge(entity)
        await self._session.flush()
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.flush()
        return True
