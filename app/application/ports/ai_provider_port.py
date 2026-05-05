from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.domain.generations.services import PromptResult

@dataclass
class GenerationResult:
    image_data: bytes
    provider_name: str
    model_name: str
    metadata: Dict[str, Any]

@dataclass
class SceneInventoryData:
    inventory: Dict[str, Any]
    provider_name: str
    model_name: str

class AIProviderPort(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def generate_variant(self, image: bytes, prompt_result: PromptResult) -> GenerationResult:
        pass

    @abstractmethod
    async def analyze_scene(self, image: bytes) -> SceneInventoryData:
        pass
