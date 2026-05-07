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
            # mode: style_redesign — estilos muy diferenciados entre sí
            "mediterraneo_moderno": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="mediterraneo_moderno",
                base_prompt="Redesign with modern Mediterranean style: terracotta tones, textured plaster walls, natural wood, rattan, linen fabrics, warm ambient lighting.",
                negative_prompt="cold, industrial, neon, dark, cluttered",
                preservation_rules=[]
            ),
            "nordico_minimalista": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="nordico_minimalista",
                base_prompt="Redesign in Scandinavian minimalist style: white and light wood, clean lines, functional furniture, natural light, wool textures, few decorative objects.",
                negative_prompt="dark, ornate, heavy, cluttered, colorful",
                preservation_rules=[]
            ),
            "industrial_urbano": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="industrial_urbano",
                base_prompt="Redesign in urban industrial style: exposed brick, black metal frames, concrete accents, Edison bulbs, leather, raw wood, dark tones.",
                negative_prompt="floral, pastel, rustic country, soft, delicate",
                preservation_rules=[]
            ),
            "clasico_elegante": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="clasico_elegante",
                base_prompt="Redesign in classic elegant style: rich fabrics (velvet, silk), dark wood furniture, crown moldings, chandeliers, gold accents, symmetrical arrangement.",
                negative_prompt="modern, minimalist, industrial, cheap, plastic",
                preservation_rules=[]
            ),
            "japones_zen": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="japones_zen",
                base_prompt="Redesign in Japanese Zen style: low furniture, tatami-inspired elements, shoji screens, bonsai, natural materials, muted earth tones, extreme simplicity.",
                negative_prompt="cluttered, ornate, heavy, colorful, western traditional",
                preservation_rules=[]
            ),
            "boho_ecletico": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="boho_ecletico",
                base_prompt="Redesign in bohemian eclectic style: layered textiles, macramé, plants everywhere, mixed patterns, warm colors, vintage furniture, global influences.",
                negative_prompt="sterile, minimalist, corporate, cold, uniform",
                preservation_rules=[]
            ),
            "coastal_playa": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="coastal_playa",
                base_prompt="Redesign in coastal beach style: white and blue palette, natural fibers (jute, rattan), driftwood accents, linen, light and airy, nautical touches.",
                negative_prompt="dark, heavy, urban, industrial, ornate",
                preservation_rules=[]
            ),
            "mid_century_modern": PromptTemplate(
                mode=GenerationMode.style_redesign,
                preset="mid_century_modern",
                base_prompt="Redesign in mid-century modern style: organic curves, tapered legs, walnut wood, mustard/teal accents, iconic furniture shapes, retro lighting.",
                negative_prompt="ornate, rustic, industrial, minimalist white, traditional",
                preservation_rules=[]
            ),
            # mode: functional_variant
            "living_tv_wall": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="living_tv_wall",
                base_prompt="Transform into a modern living room with TV wall, media console, comfortable sofa, and ambient lighting.",
                negative_prompt="cluttered, old-fashioned, messy",
                preservation_rules=[]
            ),
            "dining_room": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="dining_room",
                base_prompt="Transform into an elegant dining room with central table for 6-8, stylish chairs, pendant lighting, and sideboard.",
                negative_prompt="bedroom, office, cramped",
                preservation_rules=[]
            ),
            "home_office": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="home_office",
                base_prompt="Transform into a productive home office with desk, ergonomic chair, bookshelves, task lighting, and a reading corner.",
                negative_prompt="bedroom, kitchen, cluttered",
                preservation_rules=[]
            ),
            "dormitorio_principal": PromptTemplate(
                mode=GenerationMode.functional_variant,
                preset="dormitorio_principal",
                base_prompt="Transform into a master bedroom with king bed, nightstands, soft lighting, walk-in closet area, and cozy textiles.",
                negative_prompt="office, kitchen, living room",
                preservation_rules=[]
            ),
            # mode: localized_edit — these are more generic now
            "localized_edit": PromptTemplate(
                mode=GenerationMode.localized_edit,
                preset="localized_edit",
                base_prompt="Make the following specific change to this room while keeping everything else exactly the same.",
                negative_prompt="distorted, different room, changed architecture",
                preservation_rules=[]
            ),
        }

    def build(self, config: PromptConfig) -> PromptResult:
        preset_key = config.preset
        if not preset_key or preset_key not in self.templates:
            if config.mode == GenerationMode.style_redesign:
                preset_key = "nordico_minimalista"
            elif config.mode == GenerationMode.functional_variant:
                preset_key = "living_tv_wall"
            elif config.mode == GenerationMode.localized_edit:
                preset_key = "localized_edit"
            else:
                preset_key = "nordico_minimalista"

        template = self.templates[preset_key]

        # Build preservation instructions from scene inventory
        preservation = self._build_preservation_block(config)

        # Build the full prompt
        prompt_parts = []

        # Core instruction
        prompt_parts.append(template.base_prompt)

        # User instructions
        if config.user_instructions:
            prompt_parts.append(f"Additional instructions: {config.user_instructions}")

        # Preservation block — CRITICAL for architecture preservation
        if preservation:
            prompt_parts.append(preservation)
        else:
            # Even without inventory, add generic preservation rules
            prompt_parts.append(
                "CRITICAL: Preserve the EXACT room architecture — same walls, same floor material and color, "
                "same ceiling shape, same doors (type, material, position), same windows, same room dimensions. "
                "Only change furniture, textiles, and decorative elements."
            )

        # Always add framing instruction
        prompt_parts.append(
            "IMPORTANT: Maintain the EXACT same camera angle, framing, and field of view as the original photo. "
            "Do NOT crop, zoom in, or change the composition. The output must show the same area of the room."
        )

        prompt = "\n\n".join(prompt_parts)

        provider_params = self._get_provider_params(config.provider)

        return PromptResult(
            prompt=prompt,
            negative_prompt=template.negative_prompt,
            preservation_instructions=preservation,
            provider_params=provider_params
        )

    def _build_preservation_block(self, config: PromptConfig) -> Optional[str]:
        """Build explicit preservation instructions from scene inventory."""
        if not config.scene_inventory:
            return None

        inventory = config.scene_inventory
        lines = ["CRITICAL PRESERVATION RULES — DO NOT CHANGE THESE ELEMENTS:"]

        # Architecture elements
        architecture = inventory.get("architecture", {})
        elements = architecture.get("elements", [])
        for elem in elements:
            elem_type = elem.get("type", "")
            material = elem.get("material", "")
            color = elem.get("color", "")
            desc = f"- {elem_type}"
            if material:
                desc += f" ({material}"
                if color:
                    desc += f", {color}"
                desc += ")"
            elif color:
                desc += f" ({color})"
            lines.append(desc)

        # Camera/perspective
        camera = inventory.get("camera", {})
        if camera:
            angle = camera.get("angle", "")
            perspective = camera.get("perspective", "")
            if angle or perspective:
                lines.append(f"- Camera angle and perspective ({angle}, {perspective}) — keep identical")

        # Preservation rules from inventory
        rules = inventory.get("preservation_rules", [])
        for rule in rules:
            lines.append(f"- {rule}")

        # What to change based on mode
        if config.mode == GenerationMode.localized_edit:
            lines.append("")
            lines.append("CHANGE ONLY the specific element mentioned in the instructions above.")
            lines.append("Keep EVERYTHING else pixel-perfect identical.")
        else:
            lines.append("")
            lines.append("ONLY CHANGE: furniture, textiles, decorative objects, and lighting fixtures.")
            lines.append("DO NOT CHANGE: walls, floor, ceiling, doors, windows, room shape, camera angle.")

        return "\n".join(lines)

    def _get_provider_params(self, provider: str) -> Dict[str, Any]:
        if provider == "openai":
            return {"model": "gpt-image-1", "quality": "high", "size": "1024x1024"}
        elif provider == "flux":
            return {"guidance_scale": 7.5, "num_inference_steps": 50}
        return {}
