import pytest
from hypothesis import given, settings
from uuid import uuid4

from app.domain.generations.entities import SceneInventory

from hypothesis import strategies as st

# SceneInventory con reglas de preservación
scene_inventories = st.fixed_dictionaries({
    "scene_type": st.sampled_from(["living_room", "bedroom", "kitchen", "bathroom", "office"]),
    "preservation_rules": st.lists(st.text(min_size=5, max_size=200), min_size=1, max_size=5),
    "architecture": st.fixed_dictionaries({
        "must_preserve": st.just(True),
        "elements": st.lists(st.fixed_dictionaries({
            "type": st.sampled_from(["wall", "floor", "ceiling", "window", "door"]),
            "material": st.text(min_size=1, max_size=50)
        }), min_size=1, max_size=10)
    })
})

@given(inventory_data=scene_inventories)
@settings(max_examples=100)
def test_completed_inventory_has_required_fields(inventory_data):
    # Property 7: SceneInventory completado contiene campos requeridos

    inv = SceneInventory(
        image_id=uuid4(),
        status="completed",
        inventory_data=inventory_data,
        provider="openai",
        model="gpt-4o"
    )

    # Validating the generated dictionary meets the spec
    assert inv.inventory_data is not None
    assert "scene_type" in inv.inventory_data
    assert "architecture" in inv.inventory_data
    assert "preservation_rules" in inv.inventory_data

    assert inv.provider is not None
    assert inv.model is not None
