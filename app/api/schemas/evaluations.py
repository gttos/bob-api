from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.evaluations.entities import Evaluation

class EvaluationCreate(BaseModel):
    geometry: int = Field(..., ge=1, le=5)
    architecture: int = Field(..., ge=1, le=5)
    perspective: int = Field(..., ge=1, le=5)
    photorealism: int = Field(..., ge=1, le=5)
    commercial_quality: int = Field(..., ge=1, le=5)
    instruction_obedience: int = Field(..., ge=1, le=5)
    style_differentiation: int = Field(..., ge=1, le=5)
    localized_edit_accuracy: int = Field(..., ge=1, le=5)
    human_retouch_needed: int = Field(..., ge=1, le=5)
    construction_company_fit: int = Field(..., ge=1, le=5)
    verdict: str
    notes: Optional[str] = None

class EvaluationUpdate(BaseModel):
    geometry: Optional[int] = Field(None, ge=1, le=5)
    architecture: Optional[int] = Field(None, ge=1, le=5)
    perspective: Optional[int] = Field(None, ge=1, le=5)
    photorealism: Optional[int] = Field(None, ge=1, le=5)
    commercial_quality: Optional[int] = Field(None, ge=1, le=5)
    instruction_obedience: Optional[int] = Field(None, ge=1, le=5)
    style_differentiation: Optional[int] = Field(None, ge=1, le=5)
    localized_edit_accuracy: Optional[int] = Field(None, ge=1, le=5)
    human_retouch_needed: Optional[int] = Field(None, ge=1, le=5)
    construction_company_fit: Optional[int] = Field(None, ge=1, le=5)
    verdict: Optional[str] = None
    notes: Optional[str] = None

class EvaluationResponse(BaseModel):
    id: UUID
    variant_id: UUID
    geometry: int
    architecture: int
    perspective: int
    photorealism: int
    commercial_quality: int
    instruction_obedience: int
    style_differentiation: int
    localized_edit_accuracy: int
    human_retouch_needed: int
    construction_company_fit: int
    verdict: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Evaluation) -> "EvaluationResponse":
        return cls(
            id=entity.id,
            variant_id=entity.variant_id,
            geometry=entity.geometry,
            architecture=entity.architecture,
            perspective=entity.perspective,
            photorealism=entity.photorealism,
            commercial_quality=entity.commercial_quality,
            instruction_obedience=entity.instruction_obedience,
            style_differentiation=entity.style_differentiation,
            localized_edit_accuracy=entity.localized_edit_accuracy,
            human_retouch_needed=entity.human_retouch_needed,
            construction_company_fit=entity.construction_company_fit,
            verdict=entity.verdict.value,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
