from uuid import UUID
from fastapi import APIRouter, Depends

from app.api.schemas.evaluations import EvaluationCreate, EvaluationUpdate, EvaluationResponse
from app.application.evaluations.create_evaluation import CreateEvaluationUseCase, CreateEvaluationCommand
from app.application.evaluations.get_evaluation import GetEvaluationUseCase
from app.application.evaluations.update_evaluation import UpdateEvaluationUseCase, UpdateEvaluationCommand
from app.api.dependencies import get_create_evaluation_uc, get_get_evaluation_uc, get_update_evaluation_uc

router = APIRouter(tags=["Evaluations"])

@router.post("/image-variants/{variant_id}/evaluation", response_model=EvaluationResponse, status_code=201)
async def create_evaluation(
    variant_id: UUID,
    request: EvaluationCreate,
    use_case: CreateEvaluationUseCase = Depends(get_create_evaluation_uc)
):
    command = CreateEvaluationCommand(
        variant_id=variant_id,
        geometry=request.geometry,
        architecture=request.architecture,
        perspective=request.perspective,
        photorealism=request.photorealism,
        commercial_quality=request.commercial_quality,
        instruction_obedience=request.instruction_obedience,
        style_differentiation=request.style_differentiation,
        localized_edit_accuracy=request.localized_edit_accuracy,
        human_retouch_needed=request.human_retouch_needed,
        construction_company_fit=request.construction_company_fit,
        verdict=request.verdict,
        notes=request.notes
    )
    evaluation = await use_case.execute(command)
    return EvaluationResponse.from_entity(evaluation)

@router.get("/image-variants/{variant_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(
    variant_id: UUID,
    use_case: GetEvaluationUseCase = Depends(get_get_evaluation_uc)
):
    evaluation = await use_case.execute(variant_id)
    return EvaluationResponse.from_entity(evaluation)

@router.patch("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def update_evaluation(
    evaluation_id: UUID,
    request: EvaluationUpdate,
    use_case: UpdateEvaluationUseCase = Depends(get_update_evaluation_uc)
):
    # Extract only provided scores
    scores_dict = {}
    for field_name in [
        "geometry", "architecture", "perspective", "photorealism",
        "commercial_quality", "instruction_obedience", "style_differentiation",
        "localized_edit_accuracy", "human_retouch_needed", "construction_company_fit"
    ]:
        val = getattr(request, field_name)
        if val is not None:
            scores_dict[field_name] = val

    command = UpdateEvaluationCommand(
        evaluation_id=evaluation_id,
        scores=scores_dict,
        verdict=request.verdict,
        notes=request.notes
    )
    evaluation = await use_case.execute(command)
    return EvaluationResponse.from_entity(evaluation)
