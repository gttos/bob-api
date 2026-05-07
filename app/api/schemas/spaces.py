from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.domain.spaces.entities import Space

class SpaceCreate(BaseModel):
    name: str
    description: str | None = None

class SpaceResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, space: Space) -> "SpaceResponse":
        return cls(
            id=space.id,
            project_id=space.project_id,
            name=space.name,
            description=space.description,
            created_at=space.created_at
        )
