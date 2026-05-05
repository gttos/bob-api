import pytest
from app.domain.generations.services import PromptBuilder, PromptConfig
from app.domain.generations.entities import GenerationMode

def test_build_commercial_enhancement():
    builder = PromptBuilder()
    config = PromptConfig(
        mode=GenerationMode.commercial_enhancement,
        provider="openai",
        preset="commercial_enhancement"
    )

    result = builder.build(config)

    assert result.prompt
    assert "Enhance this interior for commercial appeal" in result.prompt
    assert result.negative_prompt
    assert "model" in result.provider_params

def test_build_localized_edit_includes_preservation_rules():
    builder = PromptBuilder()
    config = PromptConfig(
        mode=GenerationMode.localized_edit,
        provider="openai",
        preset="localized_wall_art",
        scene_inventory={"preservation_rules": ["keep the sofa", "preserve window"]}
    )

    result = builder.build(config)

    assert result.preservation_instructions == "keep the sofa, preserve window"
    assert "MUST PRESERVE: keep the sofa, preserve window" in result.prompt

def test_build_all_presets_produce_valid_output():
    builder = PromptBuilder()

    for preset, template in builder.templates.items():
        config = PromptConfig(
            mode=template.mode,
            provider="openai",
            preset=preset
        )
        result = builder.build(config)

        assert result.prompt
        assert result.negative_prompt is not None
        assert result.provider_params

def test_build_with_user_instructions_appends_to_prompt():
    builder = PromptBuilder()
    config = PromptConfig(
        mode=GenerationMode.commercial_enhancement,
        provider="openai",
        preset="commercial_enhancement",
        user_instructions="make it blue"
    )

    result = builder.build(config)

    assert "make it blue" in result.prompt
