from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from typing import Optional

from app.domain.shared.exceptions import InvalidStateTransitionError

class GenerationMode(str, Enum):
    commercial_enhancement = "commercial_enhancement"
    style_redesign = "style_redesign"
    functional_variant = "functional_variant"
    localized_edit = "localized_edit"

class GenerationStatus(str, Enum):
    pending = "pending"
    analyzing = "analyzing"
    generating = "generating"
    completed = "completed"
    failed = "failed"

    def can_transition_to(self, next_status: "GenerationStatus") -> bool:
        transitions = {
            GenerationStatus.pending: {GenerationStatus.analyzing, GenerationStatus.failed},
            GenerationStatus.analyzing: {GenerationStatus.generating, GenerationStatus.failed},
            GenerationStatus.generating: {GenerationStatus.completed, GenerationStatus.failed},
            GenerationStatus.completed: set(),
            GenerationStatus.failed: set(),
        }
        return next_status in transitions[self]

@dataclass
class GenerationRequest:
    source_image_id: UUID
    mode: GenerationMode
    provider: str
    preset: Optional[str] = None
    instructions: Optional[str] = None
    status: GenerationStatus = GenerationStatus.pending
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    prompt_final: Optional[str] = None
    negative_prompt: Optional[str] = None
    error_message: Optional[str] = None
    model: Optional[str] = None
    output_image_id: Optional[UUID] = None
    output_variant_id: Optional[UUID] = None

    def transition_to(self, new_status: GenerationStatus) -> None:
        if not self.status.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        if new_status in {GenerationStatus.completed, GenerationStatus.failed}:
            self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = GenerationStatus.failed
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)

@dataclass
class ImageVariant:
    source_image_id: UUID
    generation_request_id: UUID
    image_asset_id: UUID
    version_number: int
    provider: str
    id: UUID = field(default_factory=uuid4)
    label: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SceneInventory:
    image_id: UUID
    inventory_data: Optional[dict] = None
    status: str = "pending"
    error_message: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
