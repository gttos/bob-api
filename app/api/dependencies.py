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
