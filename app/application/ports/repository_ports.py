from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.projects.entities import Project
from app.domain.images.entities import ImageAsset


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


class ImageRepository(ABC):
    @abstractmethod
    async def save(self, image: ImageAsset) -> ImageAsset:
        pass

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> ImageAsset | None:
        pass

    @abstractmethod
    async def list_by_project(self, project_id: UUID, offset: int = 0, limit: int = 20) -> list[ImageAsset]:
        pass

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        pass

    @abstractmethod
    async def delete(self, image_id: UUID) -> None:
        pass
