from dataclasses import dataclass
from typing import Protocol, Optional
from uuid import UUID, uuid4
import mimetypes

from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import ResourceNotFoundError, DomainValidationError
from app.application.ports.repository_ports import ImageRepository, ProjectRepository, SpaceRepository
from app.application.ports.storage_port import StoragePort
from app.application.ports.task_queue_port import TaskQueuePort


@dataclass
class UploadImageCommand:
    project_id: UUID
    filename: str
    content_type: str
    file_data: bytes
    space_id: UUID | None = None


class ThumbnailService(Protocol):
    def generate(self, image_data: bytes, max_size: tuple[int, int] = (400, 400)) -> bytes:
        ...

    def get_image_dimensions(self, image_data: bytes) -> tuple[int, int]:
        ...


class UploadImageUseCase:
    def __init__(
        self,
        image_repo: ImageRepository,
        project_repo: ProjectRepository,
        space_repo: SpaceRepository,
        storage: StoragePort,
        thumbnail_service: ThumbnailService,
        allowed_mime_types: list[str],
        max_upload_size_mb: int,
        task_queue: Optional[TaskQueuePort] = None,
    ):
        self.image_repo = image_repo
        self.project_repo = project_repo
        self.space_repo = space_repo
        self.storage = storage
        self.thumbnail_service = thumbnail_service
        self.allowed_mime_types = allowed_mime_types
        self.max_upload_size_mb = max_upload_size_mb
        self.task_queue = task_queue

    async def execute(self, command: UploadImageCommand) -> ImageAsset:
        # Verify project exists
        project = await self.project_repo.get_by_id(command.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {command.project_id} not found")

        # Verify space exists and belongs to the project
        if command.space_id:
            space = await self.space_repo.get_by_id(command.space_id)
            if not space or space.project_id != command.project_id:
                raise ResourceNotFoundError(f"Space with ID {command.space_id} not found in this project")

        # Validate content_type against allowed_mime_types
        if command.content_type not in self.allowed_mime_types:
            raise DomainValidationError(f"Invalid content type: {command.content_type}")

        # Validate file size
        max_bytes = self.max_upload_size_mb * 1024 * 1024
        if len(command.file_data) > max_bytes:
            raise DomainValidationError(f"File size exceeds maximum allowed of {self.max_upload_size_mb} MB")

        image_id = uuid4()

        # Determine extension from filename or mimetype
        extension = ""
        if "." in command.filename:
            extension = command.filename.split(".")[-1]
        else:
            guessed_ext = mimetypes.guess_extension(command.content_type)
            if guessed_ext:
                extension = guessed_ext.lstrip(".")

        if not extension:
            extension = "jpg"

        # Get image dimensions
        try:
            width, height = self.thumbnail_service.get_image_dimensions(command.file_data)
        except Exception as e:
            raise DomainValidationError("Invalid image file format") from e

        # Generate storage path
        storage_path = f"projects/{command.project_id}/originals/{image_id}.{extension}"

        # Upload original to storage
        await self.storage.upload(command.file_data, storage_path, command.content_type)

        # Generate thumbnail
        try:
            thumbnail_bytes = self.thumbnail_service.generate(command.file_data)
        except Exception as e:
            raise DomainValidationError("Failed to generate thumbnail") from e

        thumbnail_path = f"projects/{command.project_id}/originals/{image_id}_thumb.{extension}"
        await self.storage.upload(thumbnail_bytes, thumbnail_path, command.content_type)

        # Create ImageAsset entity
        image_asset = ImageAsset(
            id=image_id,
            project_id=command.project_id,
            type="original",
            filename=command.filename,
            mime_type=command.content_type,
            width=width,
            height=height,
            storage_path=storage_path,
            thumbnail_path=thumbnail_path,
            space_id=command.space_id
        )

        saved = await self.image_repo.save(image_asset)

        # Auto-trigger scene analysis in background
        if self.task_queue:
            try:
                await self.task_queue.enqueue(
                    "app.infrastructure.tasks.celery_tasks.analyze_scene",
                    str(saved.id),
                )
            except Exception:
                pass  # Non-critical — don't fail upload if analysis enqueue fails

        return saved
