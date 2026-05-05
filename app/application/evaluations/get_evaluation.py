from uuid import UUID

from app.domain.evaluations.entities import Evaluation
from app.application.ports.repository_ports import EvaluationRepository
from app.domain.shared.exceptions import ResourceNotFoundError

class GetEvaluationUseCase:
    def __init__(self, evaluation_repo: EvaluationRepository):
        self.evaluation_repo = evaluation_repo

    async def execute(self, variant_id: UUID) -> Evaluation:
        evaluation = await self.evaluation_repo.get_by_variant_id(variant_id)
        if not evaluation:
            raise ResourceNotFoundError(f"Evaluation for variant {variant_id} not found")
        return evaluation
