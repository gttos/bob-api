from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository_ports import EvaluationRepository
from app.domain.evaluations.entities import Evaluation
from app.infrastructure.persistence.models import EvaluationModel

class SQLAlchemyEvaluationRepository(EvaluationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, entity: Evaluation) -> EvaluationModel:
        return EvaluationModel(
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
            verdict=entity.verdict,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _to_entity(self, model: EvaluationModel) -> Evaluation:
        return Evaluation(
            id=model.id,
            variant_id=model.variant_id,
            geometry=model.geometry,
            architecture=model.architecture,
            perspective=model.perspective,
            photorealism=model.photorealism,
            commercial_quality=model.commercial_quality,
            instruction_obedience=model.instruction_obedience,
            style_differentiation=model.style_differentiation,
            localized_edit_accuracy=model.localized_edit_accuracy,
            human_retouch_needed=model.human_retouch_needed,
            construction_company_fit=model.construction_company_fit,
            verdict=model.verdict,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def save(self, evaluation: Evaluation) -> Evaluation:
        model = await self.session.get(EvaluationModel, evaluation.id)
        if model:
            model.geometry = evaluation.geometry
            model.architecture = evaluation.architecture
            model.perspective = evaluation.perspective
            model.photorealism = evaluation.photorealism
            model.commercial_quality = evaluation.commercial_quality
            model.instruction_obedience = evaluation.instruction_obedience
            model.style_differentiation = evaluation.style_differentiation
            model.localized_edit_accuracy = evaluation.localized_edit_accuracy
            model.human_retouch_needed = evaluation.human_retouch_needed
            model.construction_company_fit = evaluation.construction_company_fit
            model.verdict = evaluation.verdict
            model.notes = evaluation.notes
            model.updated_at = evaluation.updated_at
        else:
            model = self._to_model(evaluation)
            self.session.add(model)

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_variant_id(self, variant_id: UUID) -> Evaluation | None:
        query = select(EvaluationModel).where(EvaluationModel.variant_id == variant_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        model = await self.session.get(EvaluationModel, evaluation_id)
        if not model:
            return None
        return self._to_entity(model)
