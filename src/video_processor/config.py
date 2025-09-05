"""Configuration management using Pydantic."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Optional dependency detection for 360° features
try:
    from .utils.video_360 import (
        HAS_360_SUPPORT,
        ProjectionType,
        StereoMode,
        Video360Utils,
    )
except ImportError:
    # Fallback types when 360° libraries not available
    ProjectionType = str
    StereoMode = str
    HAS_360_SUPPORT = False


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

    # 360° Video settings (only active if 360° libraries are available)
    enable_360_processing: bool = Field(default=HAS_360_SUPPORT)
    auto_detect_360: bool = Field(default=True)
    force_360_projection: ProjectionType | None = Field(default=None)
    video_360_bitrate_multiplier: float = Field(default=2.5, ge=1.0, le=5.0)
    generate_360_thumbnails: bool = Field(default=True)
    thumbnail_360_projections: list[Literal["front", "back", "up", "down", "left", "right", "stereographic"]] = Field(
        default=["front", "stereographic"]
    )

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

    @field_validator("enable_360_processing")
    @classmethod
    def validate_360_processing(cls, v: bool) -> bool:
        """Validate 360° processing can be enabled."""
        if v and not HAS_360_SUPPORT:
            raise ValueError(
                "360° processing requires optional dependencies. "
                "Install with: pip install 'video-processor[video-360]' or uv add 'video-processor[video-360]'"
            )
        return v

    model_config = ConfigDict(validate_assignment=True)
