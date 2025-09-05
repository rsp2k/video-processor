"""Storage backend implementations."""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from ..config import ProcessorConfig
from ..exceptions import StorageError


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

    @abstractmethod
    def create_directory(self, path: Path) -> None:
        """Create a directory with proper permissions."""

    @abstractmethod
    def cleanup_directory(self, path: Path) -> None:
        """Remove a directory and all its contents."""

    @abstractmethod
    def store_file(self, source_path: Path, destination_path: Path) -> Path:
        """Store a file from source to destination."""

    @abstractmethod
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""

    @abstractmethod
    def get_file_size(self, path: Path) -> int:
        """Get file size in bytes."""


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def create_directory(self, path: Path) -> None:
        """Create a directory with proper permissions."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Set directory permissions
            os.chmod(path, self.config.directory_permissions)
        except OSError as e:
            raise StorageError(f"Failed to create directory {path}: {e}") from e

    def cleanup_directory(self, path: Path) -> None:
        """Remove a directory and all its contents."""
        try:
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
        except OSError as e:
            raise StorageError(f"Failed to cleanup directory {path}: {e}") from e

    def store_file(self, source_path: Path, destination_path: Path) -> Path:
        """Store a file from source to destination."""
        try:
            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_path, destination_path)

            # Set file permissions
            os.chmod(destination_path, self.config.file_permissions)

            return destination_path

        except OSError as e:
            raise StorageError(
                f"Failed to store file {source_path} to {destination_path}: {e}"
            ) from e

    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists() and path.is_file()

    def get_file_size(self, path: Path) -> int:
        """Get file size in bytes."""
        try:
            return path.stat().st_size
        except OSError as e:
            raise StorageError(f"Failed to get file size for {path}: {e}") from e


class S3StorageBackend(StorageBackend):
    """S3 storage backend (placeholder for future implementation)."""

    def __init__(self, config: ProcessorConfig) -> None:
        super().__init__(config)
        raise NotImplementedError("S3 storage backend not implemented yet")

    def create_directory(self, path: Path) -> None:
        """Create a directory (S3 doesn't have directories, but we can simulate)."""
        raise NotImplementedError

    def cleanup_directory(self, path: Path) -> None:
        """Remove all files with the path prefix."""
        raise NotImplementedError

    def store_file(self, source_path: Path, destination_path: Path) -> Path:
        """Upload file to S3."""
        raise NotImplementedError

    def file_exists(self, path: Path) -> bool:
        """Check if object exists in S3."""
        raise NotImplementedError

    def get_file_size(self, path: Path) -> int:
        """Get S3 object size."""
        raise NotImplementedError
