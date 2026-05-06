import pytest
from hypothesis import given, settings, strategies as st
from uuid import uuid4

from app.domain.evaluations.entities import Evaluation, EvaluationVerdict
from app.domain.shared.exceptions import DomainValidationError

# Property 17: Valid scores and invalid scores
@given(score=st.integers(1, 5))
@settings(max_examples=100)
def test_evaluation_valid_scores(score):
    Evaluation(
        variant_id=uuid4(), geometry=score, architecture=score, perspective=score,
        photorealism=score, commercial_quality=score, instruction_obedience=score,
        style_differentiation=score, localized_edit_accuracy=score, human_retouch_needed=score,
        construction_company_fit=score, verdict=EvaluationVerdict.approved
    )

@given(score=st.integers().filter(lambda x: x < 1 or x > 5))
@settings(max_examples=100)
def test_evaluation_invalid_scores_raises(score):
    with pytest.raises(DomainValidationError):
        Evaluation(
            variant_id=uuid4(), geometry=score, architecture=score, perspective=score,
            photorealism=score, commercial_quality=score, instruction_obedience=score,
            style_differentiation=score, localized_edit_accuracy=score, human_retouch_needed=score,
            construction_company_fit=score, verdict=EvaluationVerdict.approved
        )

# Property 19: PATCH partial preserves unmodified fields
@given(score=st.integers(1, 5))
@settings(max_examples=100)
def test_evaluation_update_preserves_fields(score):
    eval = Evaluation(
        variant_id=uuid4(), geometry=1, architecture=1, perspective=1,
        photorealism=1, commercial_quality=1, instruction_obedience=1,
        style_differentiation=1, localized_edit_accuracy=1, human_retouch_needed=1,
        construction_company_fit=1, verdict=EvaluationVerdict.rejected
    )

    eval.update({"geometry": score}, None, None)

    assert eval.geometry == score
    assert eval.architecture == 1
    assert eval.verdict == EvaluationVerdict.rejected
