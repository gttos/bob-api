from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    async def upload(self, data: bytes, path: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        pass
