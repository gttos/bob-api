from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class ImageAsset:
    project_id: UUID
    type: str  # "original" or "generated"
    filename: str
    mime_type: str
    id: UUID = field(default_factory=uuid4)
    width: int | None = None
    height: int | None = None
    storage_path: str = ""
    thumbnail_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
