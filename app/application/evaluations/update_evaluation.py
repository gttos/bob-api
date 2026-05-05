from dataclasses import dataclass
from typing import Optional, Dict
from uuid import UUID

from app.domain.evaluations.entities import Evaluation, EvaluationVerdict
from app.application.ports.repository_ports import EvaluationRepository
from app.domain.shared.exceptions import ResourceNotFoundError

@dataclass
class UpdateEvaluationCommand:
    evaluation_id: UUID
    scores: Optional[Dict[str, int]] = None
    verdict: Optional[EvaluationVerdict] = None
    notes: Optional[str] = None

class UpdateEvaluationUseCase:
    def __init__(self, evaluation_repo: EvaluationRepository):
        self.evaluation_repo = evaluation_repo

    async def execute(self, command: UpdateEvaluationCommand) -> Evaluation:
        evaluation = await self.evaluation_repo.get_by_id(command.evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError(f"Evaluation {command.evaluation_id} not found")

        scores_dict = command.scores or {}
        evaluation.update(scores_dict, command.verdict, command.notes)

        return await self.evaluation_repo.save(evaluation)
