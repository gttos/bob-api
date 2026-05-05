from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.projects.entities import Project


class ProjectRepository(ABC):
    @abstractmethod
    async def save(self, project: Project) -> Project:
        pass

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None:
        pass

    @abstractmethod
    async def list_all(self, offset: int = 0, limit: int = 20) -> list[Project]:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass

    @abstractmethod
    async def delete(self, project_id: UUID) -> None:
        pass
