import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.domain.evaluations.entities import EvaluationVerdict
from app.domain.generations.entities import ImageVariant
from app.domain.shared.exceptions import DomainValidationError, DuplicateResourceError, ResourceNotFoundError
from app.application.evaluations.create_evaluation import CreateEvaluationUseCase, CreateEvaluationCommand
from app.application.evaluations.get_evaluation import GetEvaluationUseCase
from app.application.evaluations.update_evaluation import UpdateEvaluationUseCase, UpdateEvaluationCommand

@pytest.mark.asyncio
async def test_create_evaluation_success():
    mock_eval_repo = AsyncMock()
    mock_gen_repo = AsyncMock()

    variant_id = uuid4()
    mock_gen_repo.get_variant_by_id.return_value = ImageVariant(
        source_image_id=uuid4(),
        generation_request_id=uuid4(),
        image_asset_id=uuid4(),
        version_number=1,
        provider="openai",
        id=variant_id
    )
    mock_eval_repo.get_by_variant_id.return_value = None

    def mock_save(eval):
        return eval
    mock_eval_repo.save.side_effect = mock_save

    use_case = CreateEvaluationUseCase(evaluation_repo=mock_eval_repo, generation_repo=mock_gen_repo)

    command = CreateEvaluationCommand(
        variant_id=variant_id,
        geometry=5, architecture=4, perspective=3, photorealism=5,
        commercial_quality=4, instruction_obedience=5, style_differentiation=4,
        localized_edit_accuracy=5, human_retouch_needed=1, construction_company_fit=5,
        verdict=EvaluationVerdict.approved, notes="Looks good"
    )

    result = await use_case.execute(command)

    assert result.variant_id == variant_id
    assert result.geometry == 5
    assert result.verdict == EvaluationVerdict.approved
    mock_eval_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_evaluation_invalid_score_raises():
    mock_eval_repo = AsyncMock()
    mock_gen_repo = AsyncMock()

    variant_id = uuid4()
    mock_gen_repo.get_variant_by_id.return_value = ImageVariant(
        source_image_id=uuid4(), generation_request_id=uuid4(), image_asset_id=uuid4(),
        version_number=1, provider="openai", id=variant_id
    )
    mock_eval_repo.get_by_variant_id.return_value = None

    use_case = CreateEvaluationUseCase(evaluation_repo=mock_eval_repo, generation_repo=mock_gen_repo)

    command = CreateEvaluationCommand(
        variant_id=variant_id,
        geometry=6, architecture=4, perspective=3, photorealism=5,
        commercial_quality=4, instruction_obedience=5, style_differentiation=4,
        localized_edit_accuracy=5, human_retouch_needed=1, construction_company_fit=5,
        verdict=EvaluationVerdict.approved
    )

    with pytest.raises(DomainValidationError):
        await use_case.execute(command)

@pytest.mark.asyncio
async def test_create_evaluation_duplicate_raises():
    mock_eval_repo = AsyncMock()
    mock_gen_repo = AsyncMock()

    variant_id = uuid4()
    mock_gen_repo.get_variant_by_id.return_value = ImageVariant(
        source_image_id=uuid4(), generation_request_id=uuid4(), image_asset_id=uuid4(),
        version_number=1, provider="openai", id=variant_id
    )
    mock_eval_repo.get_by_variant_id.return_value = "Existing Evaluation"

    use_case = CreateEvaluationUseCase(evaluation_repo=mock_eval_repo, generation_repo=mock_gen_repo)

    command = CreateEvaluationCommand(
        variant_id=variant_id,
        geometry=5, architecture=4, perspective=3, photorealism=5,
        commercial_quality=4, instruction_obedience=5, style_differentiation=4,
        localized_edit_accuracy=5, human_retouch_needed=1, construction_company_fit=5,
        verdict=EvaluationVerdict.approved
    )

    with pytest.raises(DuplicateResourceError):
        await use_case.execute(command)

@pytest.mark.asyncio
async def test_update_evaluation_partial():
    mock_eval_repo = AsyncMock()

    eval_id = uuid4()
    from app.domain.evaluations.entities import Evaluation
    existing_eval = Evaluation(
        variant_id=uuid4(),
        geometry=1, architecture=1, perspective=1, photorealism=1,
        commercial_quality=1, instruction_obedience=1, style_differentiation=1,
        localized_edit_accuracy=1, human_retouch_needed=1, construction_company_fit=1,
        verdict=EvaluationVerdict.rejected,
        id=eval_id
    )

    mock_eval_repo.get_by_id.return_value = existing_eval

    def mock_save(eval):
        return eval
    mock_eval_repo.save.side_effect = mock_save

    use_case = UpdateEvaluationUseCase(evaluation_repo=mock_eval_repo)

    command = UpdateEvaluationCommand(
        evaluation_id=eval_id,
        scores={"geometry": 5},
        verdict=EvaluationVerdict.approved
    )

    result = await use_case.execute(command)

    assert result.geometry == 5
    assert result.architecture == 1
    assert result.verdict == EvaluationVerdict.approved
    mock_eval_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_get_evaluation_not_found():
    mock_eval_repo = AsyncMock()
    mock_eval_repo.get_by_variant_id.return_value = None

    use_case = GetEvaluationUseCase(evaluation_repo=mock_eval_repo)

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid4())
