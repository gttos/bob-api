import os
from pathlib import Path

from app.application.ports.storage_port import StoragePort


class LocalStorageAdapter(StoragePort):
    def __init__(self, base_path: str, media_url_prefix: str):
        self.base_path = Path(base_path)
        self.media_url_prefix = media_url_prefix

    async def upload(self, data: bytes, path: str, content_type: str) -> str:
        file_path = self.base_path / path
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Write bytes directly
        file_path.write_bytes(data)
        return path

    async def download(self, path: str) -> bytes:
        file_path = self.base_path / path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_bytes()

    async def delete(self, path: str) -> None:
        file_path = self.base_path / path
        if file_path.exists():
            file_path.unlink()

    def get_url(self, path: str) -> str:
        # Avoid double slashes if prefix ends with slash
        prefix = self.media_url_prefix.rstrip("/")
        # Avoid issue if path starts with slash
        clean_path = path.lstrip("/")
        return f"{prefix}/{clean_path}"
