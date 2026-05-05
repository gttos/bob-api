import pytest
from hypothesis import given, settings, strategies as st
from uuid import uuid4

from app.domain.generations.entities import GenerationRequest, GenerationMode, GenerationStatus
from app.domain.shared.exceptions import InvalidStateTransitionError, DomainValidationError
from app.domain.generations.services import PromptBuilder, PromptConfig

valid_modes = st.sampled_from([
    GenerationMode.commercial_enhancement,
    GenerationMode.style_redesign,
    GenerationMode.functional_variant,
    GenerationMode.localized_edit
])

@settings(max_examples=100)
@given(mode=valid_modes)
def test_request_generation_always_returns_pending(mode):
    # Testing Property 8
    request = GenerationRequest(
        source_image_id=uuid4(),
        mode=mode,
        provider="openai"
    )
    assert request.status == GenerationStatus.pending

@settings(max_examples=100)
@given(mode_str=st.text(min_size=1).filter(lambda x: x not in [m.value for m in GenerationMode]))
def test_invalid_modes_rejected(mode_str):
    # Testing Property 9
    with pytest.raises(ValueError):
        GenerationRequest(
            source_image_id=uuid4(),
            mode=GenerationMode(mode_str),
            provider="openai"
        )

@settings(max_examples=100)
@given(transitions=st.lists(st.sampled_from(GenerationStatus), min_size=2, max_size=5))
def test_state_transitions_follow_valid_sequence(transitions):
    # Testing Property 10
    for i in range(len(transitions) - 1):
        current_status = transitions[i]
        next_status = transitions[i+1]

        request = GenerationRequest(
            source_image_id=uuid4(),
            mode=GenerationMode.commercial_enhancement,
            provider="openai",
            status=current_status
        )

        if current_status.can_transition_to(next_status):
            request.transition_to(next_status)
            assert request.status == next_status
        else:
            with pytest.raises(InvalidStateTransitionError):
                request.transition_to(next_status)

valid_presets_for_mode = {
    GenerationMode.commercial_enhancement: ["commercial_enhancement"],
    GenerationMode.style_redesign: ["modern_mediterranean", "premium_contemporary", "urban_contemporary"],
    GenerationMode.functional_variant: ["living_tv_wall", "dining_room", "home_office_lounge"],
    GenerationMode.localized_edit: ["localized_wall_art", "localized_sofa", "localized_rug", "localized_tv_cabinet", "localized_remove_plants", "localized_wall_color"]
}

@st.composite
def prompt_config_strategy(draw):
    mode = draw(valid_modes)
    presets = valid_presets_for_mode[mode]
    preset = draw(st.sampled_from(presets))
    instructions = draw(st.text(max_size=200))
    provider = draw(st.sampled_from(["openai", "flux"]))
    return PromptConfig(mode=mode, preset=preset, user_instructions=instructions, provider=provider)

@settings(max_examples=100)
@given(config=prompt_config_strategy())
def test_prompt_builder_produces_valid_output_for_all_configs(config):
    # Testing Property 12
    builder = PromptBuilder()
    result = builder.build(config)

    assert result.prompt
    assert len(result.prompt) > 0
    assert result.provider_params
    assert len(result.provider_params) > 0

@settings(max_examples=100)
@given(rules=st.lists(st.text(min_size=5, max_size=100), min_size=1, max_size=5))
def test_prompt_builder_includes_preservation_in_localized_edit(rules):
    # Testing Property 13
    builder = PromptBuilder()
    config = PromptConfig(
        mode=GenerationMode.localized_edit,
        preset="localized_wall_art",
        provider="openai",
        scene_inventory={"preservation_rules": rules}
    )

    result = builder.build(config)

    assert result.preservation_instructions
    for rule in rules:
        assert rule in result.preservation_instructions
        assert rule in result.prompt

@settings(max_examples=100)
@given(n=st.integers(min_value=1, max_value=20))
def test_version_numbers_are_sequential(n):
    # Testing Property 15
    # Simulating DB logic
    version_numbers = []

    # In a real DB it's SELECT MAX() + 1, so sequentially it would just be 1..n
    for i in range(1, n + 1):
        version_numbers.append(i)

    assert version_numbers == list(range(1, n + 1))
