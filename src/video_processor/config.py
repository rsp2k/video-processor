"""Configuration management using Pydantic."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessorConfig(BaseModel):
    """Configuration for video processor."""

    # Storage settings
    storage_backend: Literal["local", "s3"] = "local"
    base_path: Path = Field(default=Path("/tmp/videos"))

    # Encoding settings
    output_formats: list[Literal["mp4", "webm", "ogv"]] = Field(default=["mp4"])
    quality_preset: Literal["low", "medium", "high", "ultra"] = "medium"

    # FFmpeg settings
    ffmpeg_path: str = "/usr/bin/ffmpeg"

    # Thumbnail settings
    thumbnail_timestamps: list[int] = Field(default=[1])  # seconds
    thumbnail_width: int = 640

    # Sprite settings
    generate_sprites: bool = True
    sprite_interval: int = 10  # seconds between sprite frames

    # Custom FFmpeg options
    custom_ffmpeg_options: dict[str, str] = Field(default_factory=dict)

    # File permissions
    file_permissions: int = 0o644
    directory_permissions: int = 0o755

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: Path) -> Path:
        """Ensure base path is absolute."""
        return v.resolve()

    @field_validator("output_formats")
    @classmethod
    def validate_output_formats(cls, v: list[str]) -> list[str]:
        """Ensure at least one output format is specified."""
        if not v:
            raise ValueError("At least one output format must be specified")
        return v

    model_config = ConfigDict(validate_assignment=True)
