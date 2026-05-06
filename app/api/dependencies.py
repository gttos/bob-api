# Dependencies for FastAPI DI

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.projects.sqlalchemy_repository import SQLAlchemyProjectRepository
from app.infrastructure.persistence.images.sqlalchemy_repository import SQLAlchemyImageRepository
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.thumbnail.pillow_thumbnail import ThumbnailService
from app.config.settings import settings

from app.application.projects.create_project import CreateProjectUseCase
from app.application.projects.get_project import GetProjectUseCase
from app.application.projects.list_projects import ListProjectsUseCase
from app.application.projects.update_project import UpdateProjectUseCase
from app.application.projects.delete_project import DeleteProjectUseCase

from app.application.images.upload_image import UploadImageUseCase
from app.application.images.get_image import GetImageUseCase as ImageGetImageUseCase
from app.application.images.list_images import ListImagesUseCase as ImageListImagesUseCase
from app.application.images.delete_image import DeleteImageUseCase as ImageDeleteImageUseCase
from app.application.ports.storage_port import StoragePort

def get_create_project_uc(session: AsyncSession = Depends(get_session)) -> CreateProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return CreateProjectUseCase(project_repo=repo)

def get_get_project_uc(session: AsyncSession = Depends(get_session)) -> GetProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return GetProjectUseCase(project_repo=repo)

def get_list_projects_uc(session: AsyncSession = Depends(get_session)) -> ListProjectsUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return ListProjectsUseCase(project_repo=repo)

def get_update_project_uc(session: AsyncSession = Depends(get_session)) -> UpdateProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return UpdateProjectUseCase(project_repo=repo)

def get_delete_project_uc(session: AsyncSession = Depends(get_session)) -> DeleteProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return DeleteProjectUseCase(project_repo=repo)

def get_storage() -> StoragePort:
    return LocalStorageAdapter(
        base_path=settings.STORAGE_LOCAL_PATH,
        media_url_prefix=settings.MEDIA_URL_PREFIX
    )

def get_thumbnail_service() -> ThumbnailService:
    return ThumbnailService()

def get_upload_image_uc(
    session: AsyncSession = Depends(get_session),
    storage: StoragePort = Depends(get_storage),
    thumbnail_service: ThumbnailService = Depends(get_thumbnail_service)
) -> UploadImageUseCase:
    image_repo = SQLAlchemyImageRepository(session)
    project_repo = SQLAlchemyProjectRepository(session)
    allowed_mime_types = [mime.strip() for mime in settings.ALLOWED_MIME_TYPES.split(",")]

    return UploadImageUseCase(
        image_repo=image_repo,
        project_repo=project_repo,
        storage=storage,
        thumbnail_service=thumbnail_service,
        allowed_mime_types=allowed_mime_types,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB
    )

def get_get_image_uc(
    session: AsyncSession = Depends(get_session),
    storage: StoragePort = Depends(get_storage)
) -> ImageGetImageUseCase:
    image_repo = SQLAlchemyImageRepository(session)
    return ImageGetImageUseCase(image_repo=image_repo, storage=storage)

def get_list_images_uc(session: AsyncSession = Depends(get_session)) -> ImageListImagesUseCase:
    image_repo = SQLAlchemyImageRepository(session)
    return ImageListImagesUseCase(image_repo=image_repo)

def get_delete_image_uc(
    session: AsyncSession = Depends(get_session),
    storage: StoragePort = Depends(get_storage)
) -> ImageDeleteImageUseCase:
    image_repo = SQLAlchemyImageRepository(session)
    return ImageDeleteImageUseCase(image_repo=image_repo, storage=storage)

from app.infrastructure.tasks.celery_queue_adapter import CeleryTaskQueueAdapter
from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.persistence.generations.sqlalchemy_repository import SQLAlchemyGenerationRepository
from app.application.generations.request_generation import RequestGenerationUseCase
from app.application.generations.get_generation import GetGenerationUseCase
from app.application.generations.list_generations import ListGenerationsUseCase

def get_task_queue() -> CeleryTaskQueueAdapter:
    return CeleryTaskQueueAdapter(celery_app)

def get_request_generation_uc(
    session: AsyncSession = Depends(get_session),
    task_queue: CeleryTaskQueueAdapter = Depends(get_task_queue)
) -> RequestGenerationUseCase:
    generation_repo = SQLAlchemyGenerationRepository(session)
    image_repo = SQLAlchemyImageRepository(session)
    return RequestGenerationUseCase(
        generation_repo=generation_repo,
        image_repo=image_repo,
        task_queue=task_queue
    )

def get_get_generation_uc(
    session: AsyncSession = Depends(get_session)
) -> GetGenerationUseCase:
    generation_repo = SQLAlchemyGenerationRepository(session)
    return GetGenerationUseCase(generation_repo=generation_repo)

def get_list_generations_uc(
    session: AsyncSession = Depends(get_session)
) -> ListGenerationsUseCase:
    generation_repo = SQLAlchemyGenerationRepository(session)
    return ListGenerationsUseCase(generation_repo=generation_repo)

from app.infrastructure.ai_providers.registry import AIProviderRegistry
from app.infrastructure.ai_providers.openai_provider import OpenAIProvider

def get_ai_provider_registry() -> AIProviderRegistry:
    registry = AIProviderRegistry()
    registry.register(OpenAIProvider(api_key=settings.OPENAI_API_KEY))
    return registry

from app.infrastructure.persistence.generations.scene_inventory_repository import SQLAlchemySceneInventoryRepository
from app.application.generations.analyze_scene import AnalyzeSceneUseCase
from app.application.generations.get_scene_inventory import GetSceneInventoryUseCase

def get_analyze_scene_uc(
    session: AsyncSession = Depends(get_session),
    task_queue: CeleryTaskQueueAdapter = Depends(get_task_queue)
) -> AnalyzeSceneUseCase:
    scene_repo = SQLAlchemySceneInventoryRepository(session)
    image_repo = SQLAlchemyImageRepository(session)
    return AnalyzeSceneUseCase(
        scene_repo=scene_repo,
        image_repo=image_repo,
        task_queue=task_queue
    )

def get_get_scene_inventory_uc(
    session: AsyncSession = Depends(get_session)
) -> GetSceneInventoryUseCase:
    scene_repo = SQLAlchemySceneInventoryRepository(session)
    return GetSceneInventoryUseCase(scene_repo=scene_repo)

from app.infrastructure.persistence.evaluations.sqlalchemy_repository import SQLAlchemyEvaluationRepository
from app.application.evaluations.create_evaluation import CreateEvaluationUseCase
from app.application.evaluations.get_evaluation import GetEvaluationUseCase as EvalGetEvaluationUseCase
from app.application.evaluations.update_evaluation import UpdateEvaluationUseCase

def get_create_evaluation_uc(
    session: AsyncSession = Depends(get_session)
) -> CreateEvaluationUseCase:
    eval_repo = SQLAlchemyEvaluationRepository(session)
    gen_repo = SQLAlchemyGenerationRepository(session)
    return CreateEvaluationUseCase(evaluation_repo=eval_repo, generation_repo=gen_repo)

def get_get_evaluation_uc(
    session: AsyncSession = Depends(get_session)
) -> EvalGetEvaluationUseCase:
    eval_repo = SQLAlchemyEvaluationRepository(session)
    return EvalGetEvaluationUseCase(evaluation_repo=eval_repo)

def get_update_evaluation_uc(
    session: AsyncSession = Depends(get_session)
) -> UpdateEvaluationUseCase:
    eval_repo = SQLAlchemyEvaluationRepository(session)
    return UpdateEvaluationUseCase(evaluation_repo=eval_repo)

from app.application.generations.get_comparison import GetComparisonUseCase
from app.application.stats.get_generation_stats import GetGenerationStatsUseCase

def get_comparison_uc(
    session: AsyncSession = Depends(get_session),
    storage: StoragePort = Depends(get_storage)
) -> GetComparisonUseCase:
    img_repo = SQLAlchemyImageRepository(session)
    gen_repo = SQLAlchemyGenerationRepository(session)
    return GetComparisonUseCase(image_repo=img_repo, generation_repo=gen_repo, storage=storage)

def get_generation_stats_uc(
    session: AsyncSession = Depends(get_session)
) -> GetGenerationStatsUseCase:
    gen_repo = SQLAlchemyGenerationRepository(session)
    return GetGenerationStatsUseCase(generation_repo=gen_repo)
