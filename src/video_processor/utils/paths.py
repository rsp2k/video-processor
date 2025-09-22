"""Path utilities and helper functions."""

import uuid
from pathlib import Path


class PathUtils:
    """Utility functions for path operations."""

    @staticmethod
    def generate_video_id() -> str:
        """
        Generate a unique video ID.

        Returns:
            8-character unique identifier
        """
        return str(uuid.uuid4())[:8]

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe filesystem use.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # Remove leading/trailing spaces and dots
        filename = filename.strip(" .")

        # Ensure filename is not empty
        if not filename:
            filename = "untitled"

        return filename

    @staticmethod
    def get_file_extension(file_path: Path) -> str:
        """
        Get file extension in lowercase.

        Args:
            file_path: Path to file

        Returns:
            File extension without dot (e.g., 'mp4')
        """
        return file_path.suffix.lower().lstrip(".")

    @staticmethod
    def change_extension(file_path: Path, new_extension: str) -> Path:
        """
        Change file extension.

        Args:
            file_path: Original file path
            new_extension: New extension (with or without dot)

        Returns:
            Path with new extension
        """
        if not new_extension.startswith("."):
            new_extension = "." + new_extension
        return file_path.with_suffix(new_extension)

    @staticmethod
    def ensure_directory_exists(directory: Path) -> None:
        """
        Ensure directory exists, create if necessary.

        Args:
            directory: Path to directory
        """
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> Path:
        """
        Get relative path from base path.

        Args:
            file_path: File path
            base_path: Base path

        Returns:
            Relative path
        """
        try:
            return file_path.relative_to(base_path)
        except ValueError:
            # If paths are not relative, return the filename
            return Path(file_path.name)

    @staticmethod
    def is_video_file(file_path: Path) -> bool:
        """
        Check if file appears to be a video file based on extension.

        Args:
            file_path: Path to file

        Returns:
            True if appears to be a video file
        """
        video_extensions = {
            "mp4",
            "avi",
            "mkv",
            "mov",
            "wmv",
            "flv",
            "webm",
            "ogv",
            "m4v",
            "3gp",
            "mpg",
            "mpeg",
            "ts",
            "mts",
            "f4v",
            "vob",
            "asf",
        }

        extension = PathUtils.get_file_extension(file_path)
        return extension in video_extensions

    @staticmethod
    def get_safe_output_path(
        output_dir: Path, filename: str, extension: str, video_id: str | None = None
    ) -> Path:
        """
        Get a safe output path, handling conflicts.

        Args:
            output_dir: Output directory
            filename: Desired filename (without extension)
            extension: File extension (with or without dot)
            video_id: Optional video ID to include in filename

        Returns:
            Safe output path
        """
        # Sanitize filename
        safe_filename = PathUtils.sanitize_filename(filename)

        # Add video ID if provided
        if video_id:
            safe_filename = f"{video_id}_{safe_filename}"

        # Ensure extension format
        if not extension.startswith("."):
            extension = "." + extension

        # Create initial path
        output_path = output_dir / (safe_filename + extension)

        # Handle conflicts by adding counter
        counter = 1
        while output_path.exists():
            name_with_counter = f"{safe_filename}_{counter}{extension}"
            output_path = output_dir / name_with_counter
            counter += 1

        return output_path
