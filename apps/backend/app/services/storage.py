"""Storage provider abstraction and local filesystem implementation."""

from __future__ import annotations

import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """Abstract interface for storing resume and document files."""

    @abstractmethod
    async def upload(self, file_bytes: bytes, filename: str, user_id: uuid.UUID) -> str:
        """Upload file content and return unique storage reference/path."""
        ...

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """Download file content by storage path."""
        ...

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """Delete file by storage path."""
        ...

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """Check if file exists at storage path."""
        ...


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage implementation for development and testing."""

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir is None:
            # Default to storage directory in project root
            self.base_dir = Path("d:/ResumeForge/storage/resumes")
        else:
            self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Strip dangerous path elements and normalize filename."""
        name = os.path.basename(filename)
        # Keep alphanumeric, dot, dash, underscore
        cleaned = re.sub(r"[^\w\.-]", "_", name)
        return cleaned or "document"

    async def upload(self, file_bytes: bytes, filename: str, user_id: uuid.UUID) -> str:
        """Store bytes safely in user-scoped subfolder."""
        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds limit of {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB")

        safe_name = self._sanitize_filename(filename)
        unique_prefix = uuid.uuid4().hex[:8]
        stored_filename = f"{unique_prefix}_{safe_name}"

        user_dir = self.base_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        target_path = user_dir / stored_filename
        # Path traversal guard
        if not target_path.resolve().is_relative_to(self.base_dir.resolve()):
            raise ValueError("Path traversal attempt detected")

        target_path.write_bytes(file_bytes)
        return str(target_path.as_posix())

    async def download(self, file_path: str) -> bytes:
        """Read and return bytes from local storage."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_dir / path

        if not path.resolve().is_relative_to(self.base_dir.resolve()):
            raise ValueError("Path traversal attempt detected")

        if not path.exists():
            raise FileNotFoundError(f"Stored file not found: {file_path}")

        return path.read_bytes()

    async def delete(self, file_path: str) -> bool:
        """Remove file from local storage."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_dir / path

        if not path.resolve().is_relative_to(self.base_dir.resolve()):
            raise ValueError("Path traversal attempt detected")

        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, file_path: str) -> bool:
        """Check whether local file exists."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_dir / path

        try:
            if not path.resolve().is_relative_to(self.base_dir.resolve()):
                return False
            return path.exists()
        except Exception:
            return False

