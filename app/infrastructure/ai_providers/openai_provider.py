import base64
import json
import structlog
from openai import AsyncOpenAI

from app.application.ports.ai_provider_port import AIProviderPort, GenerationResult, SceneInventoryData
from app.domain.generations.services import PromptResult
from app.domain.shared.exceptions import DomainError

logger = structlog.get_logger(__name__)

class ProviderNotAvailableError(DomainError):
    pass

class GenerationFailedError(DomainError):
    pass

SCENE_ANALYSIS_PROMPT = """Analyze this interior image and return a structured JSON object with the following schema:
{
  "scene_type": "living_room|bedroom|kitchen|dining_room|office|bathroom|other",
  "camera": {
    "angle": "description of camera angle",
    "perspective": "wide|medium|close",
    "focal_point": "description"
  },
  "architecture": {
    "must_preserve": true,
    "elements": [{"type": "wall|floor|ceiling|window|door", "material": "...", "color": "..."}]
  },
  "furniture": [{"type": "...", "style": "...", "color": "...", "position": "..."}],
  "decoration": [{"type": "...", "position": "..."}],
  "editable_candidates": [{"element": "...", "edit_types": ["replace", "recolor", "remove"]}],
  "preservation_rules": ["rule 1", "rule 2"]
}
Return ONLY the JSON object, no markdown, no explanation."""


class OpenAIProvider(AIProviderPort):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate_variant(self, image: bytes, prompt_result: PromptResult) -> GenerationResult:
        model = "gpt-image-1"

        logger.info(
            "openai.generate_variant.start",
            model=model,
            prompt_length=len(prompt_result.prompt),
        )

        try:
            import io
            import tempfile
            import os
            from PIL import Image as PILImage

            # Open image and determine aspect ratio to preserve orientation
            img = PILImage.open(io.BytesIO(image)).convert("RGBA")
            w, h = img.size
            ratio = w / h

            # Choose output size based on aspect ratio
            if ratio > 1.3:
                size = "1536x1024"  # Landscape
                target_w, target_h = 1536, 1024
            elif ratio < 0.77:
                size = "1024x1536"  # Portrait
                target_w, target_h = 1024, 1536
            else:
                size = "1024x1024"  # Square-ish
                target_w, target_h = 1024, 1024

            # Resize preserving aspect ratio (thumbnail keeps ratio)
            img.thumbnail((target_w, target_h), PILImage.Resampling.LANCZOS)

            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, format="PNG", optimize=True)

            # If > 4MB, reduce further
            if os.path.getsize(tmp_path) > 4 * 1024 * 1024:
                os.unlink(tmp_path)
                img.thumbnail((target_w // 2, target_h // 2), PILImage.Resampling.LANCZOS)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                    img.save(tmp_path, format="PNG", optimize=True)

            try:
                with open(tmp_path, "rb") as f:
                    response = await self.client.images.edit(
                        model=model,
                        image=f,
                        prompt=prompt_result.prompt,
                        size=size,
                        n=1,
                    )
            finally:
                os.unlink(tmp_path)

            # gpt-image-1 returns b64_json by default
            if response.data[0].b64_json:
                image_data = base64.b64decode(response.data[0].b64_json)
            elif response.data[0].url:
                import httpx
                async with httpx.AsyncClient() as http_client:
                    img_response = await http_client.get(response.data[0].url)
                    image_data = img_response.content
            else:
                raise GenerationFailedError("OpenAI returned no image data")

            logger.info("openai.generate_variant.completed", model=model, size=size)

            return GenerationResult(
                image_data=image_data,
                provider_name=self.provider_name,
                model_name=model,
                metadata={"prompt": prompt_result.prompt, "size": size},
            )

        except GenerationFailedError:
            raise
        except Exception as e:
            logger.error("openai.generate_variant.failed", error=str(e), exc_info=True)
            raise GenerationFailedError(f"OpenAI generation failed: {str(e)}")

    async def analyze_scene(self, image: bytes) -> SceneInventoryData:
        logger.info("openai.analyze_scene.start")

        try:
            image_b64 = base64.b64encode(image).decode("utf-8")

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": "high",
                                },
                            },
                            {
                                "type": "text",
                                "text": SCENE_ANALYSIS_PROMPT,
                            },
                        ],
                    }
                ],
                max_tokens=1500,
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            inventory = json.loads(raw)

            logger.info("openai.analyze_scene.completed")

            return SceneInventoryData(
                inventory=inventory,
                provider_name=self.provider_name,
                model_name="gpt-4o",
            )

        except json.JSONDecodeError as e:
            logger.error("openai.analyze_scene.json_parse_failed", error=str(e))
            raise GenerationFailedError(f"Failed to parse scene analysis response: {str(e)}")
        except Exception as e:
            logger.error("openai.analyze_scene.failed", error=str(e), exc_info=True)
            raise GenerationFailedError(f"OpenAI scene analysis failed: {str(e)}")

