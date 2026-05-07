"""
Prompt Optimizer — Uses GPT-4o to generate an optimized prompt for image generation.
Takes the scene inventory, user instructions, mode/preset, and produces a detailed
prompt specifically crafted for gpt-image-1.
"""
import structlog
from openai import AsyncOpenAI
from typing import Optional

from app.config.settings import settings

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are an expert interior design AI prompt engineer. Your job is to create 
the perfect prompt for an AI image generation model (gpt-image-1) that will edit an existing 
interior photo.

RULES:
1. The output image MUST preserve the exact room architecture: walls, floor, ceiling, doors, 
   windows, room shape, camera angle, and perspective. These are NON-NEGOTIABLE.
2. The output image MUST maintain the same framing and field of view as the original photo.
   Do NOT crop, zoom, or change composition.
3. Only furniture, textiles, decorative objects, and lighting fixtures should change.
4. Be extremely specific about what to preserve and what to change.
5. Write the prompt in English (the AI model works best in English).
6. Keep the prompt under 800 words.
7. Start with the main instruction, then list preservation rules, then style details.
"""

USER_TEMPLATE = """Create an optimized image generation prompt based on this context:

MODE: {mode}
PRESET/STYLE: {preset}
USER INSTRUCTIONS: {user_instructions}

SCENE INVENTORY (what's currently in the image):
{scene_inventory}

ELEMENTS TO REMOVE (user unchecked these):
{elements_to_remove}

Generate a single, detailed prompt that will transform this interior photo according to the 
mode and style requested. Be very explicit about what must NOT change (architecture, floor, 
walls, doors, windows, camera angle) and what SHOULD change (furniture, decoration, textiles).
"""


class PromptOptimizer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def optimize(
        self,
        mode: str,
        preset: str,
        user_instructions: str = "",
        scene_inventory: Optional[dict] = None,
        elements_to_remove: Optional[list[str]] = None,
    ) -> str:
        """Use GPT-4o to generate an optimized prompt for image generation."""

        inventory_text = "Not available"
        if scene_inventory:
            import json
            inventory_text = json.dumps(scene_inventory, indent=2, ensure_ascii=False)

        remove_text = "None"
        if elements_to_remove:
            remove_text = ", ".join(elements_to_remove)

        user_msg = USER_TEMPLATE.format(
            mode=mode,
            preset=preset or mode,
            user_instructions=user_instructions or "No specific instructions",
            scene_inventory=inventory_text,
            elements_to_remove=remove_text,
        )

        logger.info("prompt_optimizer.start", mode=mode, preset=preset)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            optimized_prompt = response.choices[0].message.content.strip()
            logger.info("prompt_optimizer.completed", prompt_length=len(optimized_prompt))
            return optimized_prompt

        except Exception as e:
            logger.error("prompt_optimizer.failed", error=str(e))
            # Fallback: return a basic prompt if optimizer fails
            return f"Redesign this interior in {preset or mode} style. Keep the exact same room architecture, walls, floor, ceiling, doors, and windows. Only change furniture and decoration. {user_instructions}"
