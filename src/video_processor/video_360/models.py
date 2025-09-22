"""Data models for 360° video processing."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectionType(Enum):
    """360° video projection types."""

    EQUIRECTANGULAR = "equirectangular"
    CUBEMAP = "cubemap"
    EAC = "eac"  # Equi-Angular Cubemap
    FISHEYE = "fisheye"
    DUAL_FISHEYE = "dual_fisheye"
    CYLINDRICAL = "cylindrical"
    STEREOGRAPHIC = "stereographic"
    PANNINI = "pannini"
    MERCATOR = "mercator"
    LITTLE_PLANET = "littleplanet"
    HALF_EQUIRECTANGULAR = "half_equirectangular"  # VR180
    FLAT = "flat"  # Extracted viewport
    UNKNOWN = "unknown"


class StereoMode(Enum):
    """Stereoscopic viewing modes."""

    MONO = "mono"
    TOP_BOTTOM = "top_bottom"
    LEFT_RIGHT = "left_right"
    FRAME_SEQUENTIAL = "frame_sequential"
    ANAGLYPH = "anaglyph"
    UNKNOWN = "unknown"


class SpatialAudioType(Enum):
    """Spatial audio formats."""

    NONE = "none"
    AMBISONIC_BFORMAT = "ambisonic_bformat"
    AMBISONIC_HOA = "ambisonic_hoa"  # Higher Order Ambisonics
    OBJECT_BASED = "object_based"
    HEAD_LOCKED = "head_locked"
    BINAURAL = "binaural"


@dataclass
class SphericalMetadata:
    """Spherical video metadata container."""

    is_spherical: bool = False
    projection: ProjectionType = ProjectionType.UNKNOWN
    stereo_mode: StereoMode = StereoMode.MONO

    # Spherical video properties
    stitched: bool = True
    source_count: int = 1
    initial_view_heading: float = 0.0  # degrees
    initial_view_pitch: float = 0.0  # degrees
    initial_view_roll: float = 0.0  # degrees

    # Field of view
    fov_horizontal: float = 360.0
    fov_vertical: float = 180.0

    # Spatial audio
    has_spatial_audio: bool = False
    audio_type: SpatialAudioType = SpatialAudioType.NONE
    audio_channels: int = 2

    # Detection metadata
    confidence: float = 0.0
    detection_methods: list[str] = field(default_factory=list)

    # Video properties
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0

    @property
    def is_stereoscopic(self) -> bool:
        """Check if video is stereoscopic."""
        return self.stereo_mode != StereoMode.MONO

    @property
    def is_vr180(self) -> bool:
        """Check if video is VR180 format."""
        return (
            self.projection == ProjectionType.HALF_EQUIRECTANGULAR
            and self.is_stereoscopic
        )

    @property
    def is_full_sphere(self) -> bool:
        """Check if video covers full sphere."""
        return self.fov_horizontal >= 360.0 and self.fov_vertical >= 180.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_spherical": self.is_spherical,
            "projection": self.projection.value,
            "stereo_mode": self.stereo_mode.value,
            "stitched": self.stitched,
            "source_count": self.source_count,
            "initial_view": {
                "heading": self.initial_view_heading,
                "pitch": self.initial_view_pitch,
                "roll": self.initial_view_roll,
            },
            "fov": {"horizontal": self.fov_horizontal, "vertical": self.fov_vertical},
            "spatial_audio": {
                "has_spatial_audio": self.has_spatial_audio,
                "type": self.audio_type.value,
                "channels": self.audio_channels,
            },
            "detection": {
                "confidence": self.confidence,
                "methods": self.detection_methods,
            },
            "video": {
                "width": self.width,
                "height": self.height,
                "aspect_ratio": self.aspect_ratio,
            },
        }


@dataclass
class ViewportConfig:
    """Viewport extraction configuration."""

    yaw: float = 0.0  # Horizontal rotation (-180 to 180)
    pitch: float = 0.0  # Vertical rotation (-90 to 90)
    roll: float = 0.0  # Camera roll (-180 to 180)
    fov: float = 90.0  # Field of view (degrees)

    # Output settings
    width: int = 1920
    height: int = 1080

    # Animation settings (for animated viewports)
    is_animated: bool = False
    keyframes: list[tuple[float, "ViewportConfig"]] = field(default_factory=list)

    def validate(self) -> bool:
        """Validate viewport parameters."""
        return (
            -180 <= self.yaw <= 180
            and -90 <= self.pitch <= 90
            and -180 <= self.roll <= 180
            and 10 <= self.fov <= 180
            and self.width > 0
            and self.height > 0
        )


@dataclass
class BitrateLevel360:
    """360° video bitrate level with projection-specific settings."""

    name: str
    width: int
    height: int
    bitrate: int  # kbps
    max_bitrate: int  # kbps
    projection: ProjectionType
    codec: str = "h264"
    container: str = "mp4"

    # 360° specific settings
    bitrate_multiplier: float = 2.5  # Higher bitrates for 360°
    tiled_encoding: bool = False
    tile_columns: int = 4
    tile_rows: int = 4

    def get_effective_bitrate(self) -> int:
        """Get effective bitrate with 360° multiplier applied."""
        return int(self.bitrate * self.bitrate_multiplier)

    def get_effective_max_bitrate(self) -> int:
        """Get effective max bitrate with 360° multiplier applied."""
        return int(self.max_bitrate * self.bitrate_multiplier)


@dataclass
class Video360ProcessingResult:
    """Result of 360° video processing operation."""

    success: bool = False
    output_path: Path | None = None

    # Processing metadata
    operation: str = ""
    input_metadata: SphericalMetadata | None = None
    output_metadata: SphericalMetadata | None = None

    # Quality metrics
    processing_time: float = 0.0
    file_size_before: int = 0
    file_size_after: int = 0

    # Warnings and errors
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Additional outputs (for streaming, etc.)
    additional_outputs: dict[str, Path] = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        if self.file_size_before > 0:
            return self.file_size_after / self.file_size_before
        return 0.0

    def add_warning(self, message: str) -> None:
        """Add warning message."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add error message."""
        self.errors.append(message)
        self.success = False

    @property
    def error_message(self) -> str:
        """Get combined error message."""
        return "; ".join(self.errors) if self.errors else ""


@dataclass
class Video360StreamingPackage:
    """360° streaming package with viewport-adaptive capabilities."""

    video_id: str
    source_path: Path
    output_dir: Path
    metadata: SphericalMetadata

    # Standard streaming outputs
    hls_playlist: Path | None = None
    dash_manifest: Path | None = None

    # 360° specific outputs
    viewport_adaptive_manifest: Path | None = None
    tile_manifests: dict[str, Path] = field(default_factory=dict)

    # Bitrate levels
    bitrate_levels: list[BitrateLevel360] = field(default_factory=list)

    # Viewport extraction outputs
    viewport_extractions: dict[str, Path] = field(default_factory=dict)

    # Thumbnail tracks for different projections
    thumbnail_tracks: dict[ProjectionType, Path] = field(default_factory=dict)

    # Spatial audio tracks
    spatial_audio_tracks: dict[str, Path] = field(default_factory=dict)

    @property
    def supports_viewport_adaptive(self) -> bool:
        """Check if package supports viewport-adaptive streaming."""
        return self.viewport_adaptive_manifest is not None

    @property
    def supports_tiled_streaming(self) -> bool:
        """Check if package supports tiled streaming."""
        return len(self.tile_manifests) > 0

    def get_projection_thumbnails(self, projection: ProjectionType) -> Path | None:
        """Get thumbnail track for specific projection."""
        return self.thumbnail_tracks.get(projection)


@dataclass
class Video360Quality:
    """360° video quality assessment metrics."""

    projection_quality: float = 0.0  # Quality of projection conversion
    viewport_quality: float = 0.0  # Quality in specific viewports
    seam_quality: float = 0.0  # Quality at projection seams
    pole_distortion: float = 0.0  # Distortion at poles (equirectangular)

    # Per-region quality (for tiled encoding)
    region_qualities: dict[str, float] = field(default_factory=dict)

    # Motion analysis
    motion_intensity: float = 0.0
    motion_distribution: dict[str, float] = field(default_factory=dict)

    # Recommended settings
    recommended_bitrate_multiplier: float = 2.5
    recommended_projections: list[ProjectionType] = field(default_factory=list)

    @property
    def overall_quality(self) -> float:
        """Calculate overall quality score."""
        scores = [
            self.projection_quality,
            self.viewport_quality,
            self.seam_quality,
            1.0 - self.pole_distortion,  # Lower distortion = higher score
        ]
        return sum(scores) / len(scores)


@dataclass
class Video360Analysis:
    """Complete 360° video analysis result."""

    metadata: SphericalMetadata
    quality: Video360Quality

    # Content analysis
    dominant_regions: list[str] = field(default_factory=list)  # "front", "back", etc.
    scene_complexity: float = 0.0
    color_distribution: dict[str, float] = field(default_factory=dict)

    # Processing recommendations
    optimal_projections: list[ProjectionType] = field(default_factory=list)
    recommended_viewports: list[ViewportConfig] = field(default_factory=list)
    optimal_bitrate_ladder: list[BitrateLevel360] = field(default_factory=list)

    # Streaming recommendations
    supports_viewport_adaptive: bool = False
    supports_tiled_encoding: bool = False
    recommended_tile_size: tuple[int, int] = (4, 4)

    def to_dict(self) -> dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "quality": {
                "projection_quality": self.quality.projection_quality,
                "viewport_quality": self.quality.viewport_quality,
                "seam_quality": self.quality.seam_quality,
                "pole_distortion": self.quality.pole_distortion,
                "overall_quality": self.quality.overall_quality,
                "motion_intensity": self.quality.motion_intensity,
            },
            "content": {
                "dominant_regions": self.dominant_regions,
                "scene_complexity": self.scene_complexity,
                "color_distribution": self.color_distribution,
            },
            "recommendations": {
                "optimal_projections": [p.value for p in self.optimal_projections],
                "viewport_adaptive": self.supports_viewport_adaptive,
                "tiled_encoding": self.supports_tiled_encoding,
                "tile_size": self.recommended_tile_size,
            },
        }
