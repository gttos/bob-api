from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.evaluations.entities import Evaluation, EvaluationVerdict
from app.application.ports.repository_ports import EvaluationRepository, GenerationRepository
from app.domain.shared.exceptions import ResourceNotFoundError, DuplicateResourceError

@dataclass
class CreateEvaluationCommand:
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

class CreateEvaluationUseCase:
    def __init__(self, evaluation_repo: EvaluationRepository, generation_repo: GenerationRepository):
        self.evaluation_repo = evaluation_repo
        self.generation_repo = generation_repo

    async def execute(self, command: CreateEvaluationCommand) -> Evaluation:
        variant = await self.generation_repo.get_variant_by_id(command.variant_id)
        if not variant:
            raise ResourceNotFoundError(f"Variant {command.variant_id} not found")

        existing = await self.evaluation_repo.get_by_variant_id(command.variant_id)
        if existing:
            raise DuplicateResourceError(f"Evaluation for variant {command.variant_id} already exists")

        evaluation = Evaluation(
            variant_id=command.variant_id,
            geometry=command.geometry,
            architecture=command.architecture,
            perspective=command.perspective,
            photorealism=command.photorealism,
            commercial_quality=command.commercial_quality,
            instruction_obedience=command.instruction_obedience,
            style_differentiation=command.style_differentiation,
            localized_edit_accuracy=command.localized_edit_accuracy,
            human_retouch_needed=command.human_retouch_needed,
            construction_company_fit=command.construction_company_fit,
            verdict=command.verdict,
            notes=command.notes
        )

        return await self.evaluation_repo.save(evaluation)
