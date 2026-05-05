from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.domain.generations.entities import GenerationMode

@dataclass
class PromptConfig:
    mode: GenerationMode
    provider: str
    preset: Optional[str] = None
    user_instructions: Optional[str] = None
    scene_inventory: Optional[Dict[str, Any]] = None

@dataclass
class PromptResult:
    prompt: str
    negative_prompt: Optional[str]
    preservation_instructions: Optional[str]
    provider_params: Dict[str, Any]

@dataclass
class PromptTemplate:
    mode: GenerationMode
    preset: str
    base_prompt: str
    negative_prompt: str
    preservation_rules: list[str]

class PromptBuilder:
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {
            # mode: commercial_enhancement
            "commercial_enhancement": PromptTemplate(
                mode=GenerationMode.commercial_enhancement,
                preset="commercial_enhancement",
                base_prompt="Enhance this interior for commercial appeal, making it look professional, bright, and highly attractive for real estate listings.",
                negative_prompt="dark, gloomy, messy, low resolution, amateur, distorted",
                preservation_rules=["preserve structural elements", "keep original layout"]
            ),
            # mode: style_redesign
            "modern_mediterranean": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="modern_mediterranean",
                base_prompt="Redesign this space in a modern Mediterranean style, using warm terracotta tones, textured white walls, natural wood, and light fabrics.",
                negative_prompt="cold, industrial, neon, dark colors, cluttered, highly modern",
                preservation_rules=["preserve room geometry", "keep windows"]
            ),
            "premium_contemporary": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="premium_contemporary",
                base_prompt="Transform this room into a premium contemporary style, featuring sleek lines, high-end materials, neutral palettes, and elegant lighting.",
                negative_prompt="rustic, vintage, cheap materials, cluttered, bright neon colors",
                preservation_rules=["preserve room geometry", "keep windows"]
            ),
            "urban_contemporary": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="urban_contemporary",
                base_prompt="Redesign the room with an urban contemporary aesthetic, incorporating industrial elements, exposed brick, dark metal accents, and modern furniture.",
                negative_prompt="floral, rustic, overly bright, traditional, soft pastels",
                preservation_rules=["preserve room geometry", "keep windows"]
            ),
            # mode: functional_variant
            "living_tv_wall": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="living_tv_wall",
                base_prompt="Redesign the living room to feature a modern TV wall with integrated shelving, sleek media console, and subtle backlighting.",
                negative_prompt="cluttered, old-fashioned, CRT tv, messy wiring, overly empty",
                preservation_rules=["preserve room geometry"]
            ),
            "dining_room": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="dining_room",
                base_prompt="Convert this space into an elegant dining room with a central dining table, stylish chairs, and a striking chandelier.",
                negative_prompt="bedroom furniture, living room setup, cramped, poorly lit",
                preservation_rules=["preserve room geometry"]
            ),
            "home_office_lounge": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="home_office_lounge",
                base_prompt="Transform the room into a comfortable home office lounge, featuring a desk area, ergonomic chair, and a cozy reading nook.",
                negative_prompt="kitchen setup, dining setup, sterile, corporate cubicle",
                preservation_rules=["preserve room geometry"]
            ),
            # mode: localized_edit
            "localized_wall_art": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_wall_art",
                base_prompt="Add modern abstract wall art to the empty walls to enhance the room's aesthetic.",
                negative_prompt="distorted art, text, messy, covering windows",
                preservation_rules=[]
            ),
            "localized_sofa": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_sofa",
                base_prompt="Replace the current sofa with a modern, sleek modular sofa in a neutral tone.",
                negative_prompt="distorted furniture, clashing colors, oversized",
                preservation_rules=[]
            ),
            "localized_rug": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_rug",
                base_prompt="Add a large, stylish area rug that complements the room's color palette.",
                negative_prompt="clashing patterns, too small, wrinkled, distorted",
                preservation_rules=[]
            ),
            "localized_tv_cabinet": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_tv_cabinet",
                base_prompt="Update the TV cabinet to a minimalist, floating design with wooden textures.",
                negative_prompt="bulky, old-fashioned, messy wiring",
                preservation_rules=[]
            ),
            "localized_remove_plants": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_remove_plants",
                base_prompt="Remove all indoor plants from the scene, leaving a clean and uncluttered space.",
                negative_prompt="floating leaves, distorted background where plants were",
                preservation_rules=[]
            ),
            "localized_wall_color": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_wall_color",
                base_prompt="Change the wall color to a soft, warm neutral tone while keeping the lighting realistic.",
                negative_prompt="uneven paint, dark colors, neon, covering textures",
                preservation_rules=[]
            ),
        }

    def build(self, config: PromptConfig) -> PromptResult:
        preset_key = config.preset
        if not preset_key or preset_key not in self.templates:
            # Fallbacks if preset is not provided or invalid
            if config.mode == GenerationMode.commercial_enhancement:
                preset_key = "commercial_enhancement"
            elif config.mode == GenerationMode.style_redesign:
                preset_key = "premium_contemporary"
            elif config.mode == GenerationMode.functional_variant:
                preset_key = "living_tv_wall"
            elif config.mode == GenerationMode.localized_edit:
                preset_key = "localized_wall_art"
            else:
                preset_key = "commercial_enhancement"

        template = self.templates[preset_key]

        # Build prompt
        prompt = template.base_prompt
        if config.user_instructions:
            prompt += f" Additional instructions: {config.user_instructions}"

        preservation = None
        if config.mode == GenerationMode.localized_edit and config.scene_inventory:
            preservation_rules = config.scene_inventory.get("preservation_rules", [])
            if preservation_rules:
                preservation = ", ".join(preservation_rules)
                prompt += f" MUST PRESERVE: {preservation}"

        provider_params = self._get_provider_params(config.provider)

        return PromptResult(
            prompt=prompt,
            negative_prompt=template.negative_prompt,
            preservation_instructions=preservation,
            provider_params=provider_params
        )

    def _get_provider_params(self, provider: str) -> Dict[str, Any]:
        if provider == "openai":
            return {"model": "gpt-image-1", "quality": "high", "size": "1024x1024"}
        elif provider == "flux":
            return {"guidance_scale": 7.5, "num_inference_steps": 50}
        return {}
