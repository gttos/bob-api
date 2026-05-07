from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository_ports import ProjectRepository
from app.domain.projects.entities import Project
from app.infrastructure.persistence.models import ProjectModel


class SQLAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, project: Project) -> Project:
        model = await self._session.get(ProjectModel, project.id)
        if model is None:
            model = self._to_model(project)
            self._session.add(model)
        else:
            model.name = project.name
            model.description = project.description
            model.owner_id = project.owner_id
            model.created_at = project.created_at
            model.updated_at = project.updated_at

        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, project_id: UUID) -> Project | None:
        model = await self._session.get(ProjectModel, project_id)
        if model is None or model.deleted_at is not None:
            return None
        return self._to_entity(model)

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel)
            .where(ProjectModel.deleted_at.is_(None))
            .order_by(ProjectModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]

    async def count(self) -> int:
        result = await self._session.execute(
            select(func.count(ProjectModel.id))
            .where(ProjectModel.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def delete(self, project_id: UUID) -> None:
        model = await self._session.get(ProjectModel, project_id)
        if model is not None:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()

    def _to_entity(self, model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Project) -> ProjectModel:
        return ProjectModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            owner_id=entity.owner_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
