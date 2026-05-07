from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository_ports import SpaceRepository
from app.domain.spaces.entities import Space
from app.infrastructure.persistence.models import SpaceModel

class SQLAlchemySpaceRepository(SpaceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, space: Space) -> Space:
        model = await self._session.get(SpaceModel, space.id)
        if model is None:
            model = self._to_model(space)
            self._session.add(model)
        else:
            model.project_id = space.project_id
            model.name = space.name
            model.description = space.description
            model.created_at = space.created_at

        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, space_id: UUID) -> Space | None:
        model = await self._session.get(SpaceModel, space_id)
        if model is None or model.deleted_at is not None:
            return None
        return self._to_entity(model)

    async def list_by_project(self, project_id: UUID) -> list[Space]:
        result = await self._session.execute(
            select(SpaceModel)
            .where(SpaceModel.project_id == project_id)
            .where(SpaceModel.deleted_at.is_(None))
            .order_by(SpaceModel.created_at.asc())
        )
        return [self._to_entity(m) for m in result.scalars()]

    async def delete(self, space_id: UUID) -> None:
        model = await self._session.get(SpaceModel, space_id)
        if model is not None and model.deleted_at is None:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()

    def _to_entity(self, model: SpaceModel) -> Space:
        return Space(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            description=model.description,
            created_at=model.created_at
        )

    def _to_model(self, entity: Space) -> SpaceModel:
        return SpaceModel(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at
        )
