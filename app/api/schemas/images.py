from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.domain.images.entities import ImageAsset
from app.application.ports.storage_port import StoragePort


class ImageResponse(BaseModel):
    id: UUID
    project_id: UUID
    type: str
    filename: str
    mime_type: str
    width: int | None
    height: int | None
    url: str
    thumbnail_url: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, image: ImageAsset, storage: StoragePort) -> "ImageResponse":
        url = storage.get_url(image.storage_path) if image.storage_path else ""
        thumbnail_url = storage.get_url(image.thumbnail_path) if image.thumbnail_path else None

        return cls(
            id=image.id,
            project_id=image.project_id,
            type=image.type,
            filename=image.filename,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
            url=url,
            thumbnail_url=thumbnail_url,
            created_at=image.created_at,
        )
