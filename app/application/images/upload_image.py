from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4
import mimetypes

from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import ResourceNotFoundError, DomainValidationError
from app.application.ports.repository_ports import ImageRepository, ProjectRepository
from app.application.ports.storage_port import StoragePort


@dataclass
class UploadImageCommand:
    project_id: UUID
    filename: str
    content_type: str
    file_data: bytes


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
        storage: StoragePort,
        thumbnail_service: ThumbnailService,
        allowed_mime_types: list[str],
        max_upload_size_mb: int
    ):
        self.image_repo = image_repo
        self.project_repo = project_repo
        self.storage = storage
        self.thumbnail_service = thumbnail_service
        self.allowed_mime_types = allowed_mime_types
        self.max_upload_size_mb = max_upload_size_mb

    async def execute(self, command: UploadImageCommand) -> ImageAsset:
        # Verify project exists
        project = await self.project_repo.get_by_id(command.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {command.project_id} not found")

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
            extension = "jpg" # default fallback

        # Get image dimensions
        try:
            width, height = self.thumbnail_service.get_image_dimensions(command.file_data)
        except Exception as e:
            raise DomainValidationError("Invalid image file format") from e

        # Generate storage path
        storage_path = f"projects/{command.project_id}/originals/{image_id}.{extension}"

        # Upload original to storage
        await self.storage.upload(command.file_data, storage_path, command.content_type)

        # Generate thumbnail bytes
        try:
            thumbnail_bytes = self.thumbnail_service.generate(command.file_data)
        except Exception as e:
            raise DomainValidationError("Failed to generate thumbnail") from e

        # Generate thumbnail path
        thumbnail_path = f"projects/{command.project_id}/originals/{image_id}_thumb.{extension}"

        # Upload thumbnail to storage
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
            thumbnail_path=thumbnail_path
        )

        # Save to repository and return
        return await self.image_repo.save(image_asset)
