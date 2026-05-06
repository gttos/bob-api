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

from app.domain.generations.entities import GenerationRequest, ImageVariant

class GenerationRepository(ABC):
    @abstractmethod
    async def save(self, request: GenerationRequest) -> GenerationRequest:
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> GenerationRequest | None:
        pass

    @abstractmethod
    async def list_by_image(self, image_id: UUID, offset: int, limit: int) -> list[GenerationRequest]:
        pass

    @abstractmethod
    async def count_by_image(self, image_id: UUID) -> int:
        pass

    @abstractmethod
    async def save_variant(self, variant: ImageVariant) -> ImageVariant:
        pass

    @abstractmethod
    async def get_next_version_number(self, source_image_id: UUID) -> int:
        pass

    @abstractmethod
    async def get_variant_by_id(self, variant_id: UUID) -> ImageVariant | None:
        pass

    @abstractmethod
    async def get_generation_stats(self, group_by: str, project_id: UUID | None = None) -> dict:
        pass

from app.domain.generations.entities import SceneInventory

class SceneInventoryRepository(ABC):
    @abstractmethod
    async def save(self, inventory: SceneInventory) -> SceneInventory:
        pass

    @abstractmethod
    async def get_by_image_id(self, image_id: UUID) -> SceneInventory | None:
        pass

from app.domain.evaluations.entities import Evaluation

class EvaluationRepository(ABC):
    @abstractmethod
    async def save(self, evaluation: Evaluation) -> Evaluation:
        pass

    @abstractmethod
    async def get_by_variant_id(self, variant_id: UUID) -> Evaluation | None:
        pass

    @abstractmethod
    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        pass
