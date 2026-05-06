from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.domain.generations.entities import SceneInventory

class SceneInventoryResponse(BaseModel):
    id: UUID
    image_id: UUID
    inventory_data: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, entity: SceneInventory) -> "SceneInventoryResponse":
        return cls(
            id=entity.id,
            image_id=entity.image_id,
            inventory_data=entity.inventory_data,
            status=entity.status,
            error_message=entity.error_message,
            provider=entity.provider,
            model=entity.model,
            created_at=entity.created_at,
            completed_at=entity.completed_at
        )
