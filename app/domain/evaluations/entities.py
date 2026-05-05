from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict
from uuid import UUID, uuid4

from app.domain.shared.exceptions import DomainValidationError

class EvaluationVerdict(str, Enum):
    approved = "approved"
    usable_with_retouch = "usable_with_retouch"
    rejected = "rejected"

@dataclass
class Evaluation:
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
    verdict: EvaluationVerdict
    notes: Optional[str] = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        scores = [
            self.geometry, self.architecture, self.perspective, self.photorealism,
            self.commercial_quality, self.instruction_obedience, self.style_differentiation,
            self.localized_edit_accuracy, self.human_retouch_needed, self.construction_company_fit
        ]
        for score in scores:
            if not (1 <= score <= 5):
                raise DomainValidationError("All evaluation scores must be between 1 and 5")

        if not isinstance(self.verdict, EvaluationVerdict):
            try:
                self.verdict = EvaluationVerdict(self.verdict)
            except ValueError:
                 raise DomainValidationError(f"Invalid verdict: {self.verdict}")

    def update(self, scores_dict: Dict[str, int], verdict: Optional[EvaluationVerdict], notes: Optional[str]) -> None:
        for key, value in scores_dict.items():
            if hasattr(self, key):
                if not (1 <= value <= 5):
                     raise DomainValidationError(f"Score {key} must be between 1 and 5")
                setattr(self, key, value)

        if verdict is not None:
             if not isinstance(verdict, EvaluationVerdict):
                  try:
                      verdict = EvaluationVerdict(verdict)
                  except ValueError:
                      raise DomainValidationError(f"Invalid verdict: {verdict}")
             self.verdict = verdict

        if notes is not None:
            self.notes = notes

        self.updated_at = datetime.now(timezone.utc)
