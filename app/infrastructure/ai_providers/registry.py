from app.application.ports.ai_provider_port import AIProviderPort
from app.domain.shared.exceptions import ResourceNotFoundError

class AIProviderRegistry:
    def __init__(self):
        self._providers = {}

    def register(self, provider: AIProviderPort) -> None:
        self._providers[provider.provider_name] = provider

    def get(self, name: str) -> AIProviderPort:
        if name not in self._providers:
            raise ResourceNotFoundError(f"AI Provider '{name}' not found in registry")
        return self._providers[name]
