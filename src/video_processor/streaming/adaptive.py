"""Adaptive streaming processor that builds on existing encoding infrastructure."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..config import ProcessorConfig
from ..core.processor import VideoProcessor
from ..exceptions import EncodingError

# Optional AI integration
try:
    from ..ai.content_analyzer import VideoContentAnalyzer

    HAS_AI_SUPPORT = True
except ImportError:
    HAS_AI_SUPPORT = False

logger = logging.getLogger(__name__)


@dataclass
class BitrateLevel:
    """Represents a single bitrate level in adaptive streaming."""

    name: str
    width: int
    height: int
    bitrate: int  # kbps
    max_bitrate: int  # kbps
    codec: str
    container: str


@dataclass
class StreamingPackage:
    """Complete adaptive streaming package."""

    video_id: str
    source_path: Path
    output_dir: Path
    hls_playlist: Path | None = None
    dash_manifest: Path | None = None
    bitrate_levels: list[BitrateLevel] = None
    segment_duration: int = 6  # seconds
    thumbnail_track: Path | None = None
    metadata: dict | None = None


class AdaptiveStreamProcessor:
    """
    Adaptive streaming processor that leverages existing video processing infrastructure.

    Creates HLS and DASH streams with multiple bitrate levels optimized using AI analysis.
    """

    def __init__(
        self, config: ProcessorConfig, enable_ai_optimization: bool = True
    ) -> None:
        self.config = config
        self.enable_ai_optimization = enable_ai_optimization and HAS_AI_SUPPORT

        if self.enable_ai_optimization:
            self.content_analyzer = VideoContentAnalyzer()
        else:
            self.content_analyzer = None

        logger.info(
            f"Adaptive streaming initialized with AI optimization: {self.enable_ai_optimization}"
        )

    async def create_adaptive_stream(
        self,
        video_path: Path,
        output_dir: Path,
        video_id: str | None = None,
        streaming_formats: list[Literal["hls", "dash"]] = None,
        custom_bitrate_ladder: list[BitrateLevel] | None = None,
    ) -> StreamingPackage:
        """
        Create adaptive streaming package from source video.

        Args:
            video_path: Source video file
            output_dir: Output directory for streaming files
            video_id: Optional video identifier
            streaming_formats: List of streaming formats to generate
            custom_bitrate_ladder: Custom bitrate levels (uses optimized defaults if None)

        Returns:
            Complete streaming package with manifests and segments
        """
        if video_id is None:
            video_id = video_path.stem

        if streaming_formats is None:
            streaming_formats = ["hls", "dash"]

        logger.info(f"Creating adaptive stream for {video_path} -> {output_dir}")

        # Step 1: Analyze source video for optimal bitrate ladder
        bitrate_levels = custom_bitrate_ladder
        if bitrate_levels is None:
            bitrate_levels = await self._generate_optimal_bitrate_ladder(video_path)

        # Step 2: Create output directory structure
        stream_dir = output_dir / video_id
        stream_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Generate multiple bitrate renditions
        rendition_files = await self._generate_bitrate_renditions(
            video_path, stream_dir, video_id, bitrate_levels
        )

        # Step 4: Generate streaming manifests
        streaming_package = StreamingPackage(
            video_id=video_id,
            source_path=video_path,
            output_dir=stream_dir,
            bitrate_levels=bitrate_levels,
        )

        if "hls" in streaming_formats:
            streaming_package.hls_playlist = await self._generate_hls_playlist(
                stream_dir, video_id, bitrate_levels, rendition_files
            )

        if "dash" in streaming_formats:
            streaming_package.dash_manifest = await self._generate_dash_manifest(
                stream_dir, video_id, bitrate_levels, rendition_files
            )

        # Step 5: Generate thumbnail track for scrubbing
        streaming_package.thumbnail_track = await self._generate_thumbnail_track(
            video_path, stream_dir, video_id
        )

        logger.info("Adaptive streaming package created successfully")
        return streaming_package

    async def _generate_optimal_bitrate_ladder(
        self, video_path: Path
    ) -> list[BitrateLevel]:
        """
        Generate optimal bitrate ladder using AI analysis or intelligent defaults.
        """
        logger.info("Generating optimal bitrate ladder")

        # Get source video characteristics
        source_analysis = None
        if self.enable_ai_optimization and self.content_analyzer:
            try:
                source_analysis = await self.content_analyzer.analyze_content(
                    video_path
                )
                logger.info(
                    f"AI analysis: {source_analysis.resolution}, motion: {source_analysis.motion_intensity:.2f}"
                )
            except Exception as e:
                logger.warning(f"AI analysis failed, using defaults: {e}")

        # Base bitrate ladder
        base_levels = [
            BitrateLevel("240p", 426, 240, 400, 600, "h264", "mp4"),
            BitrateLevel("360p", 640, 360, 800, 1200, "h264", "mp4"),
            BitrateLevel("480p", 854, 480, 1500, 2250, "h264", "mp4"),
            BitrateLevel("720p", 1280, 720, 3000, 4500, "h264", "mp4"),
            BitrateLevel("1080p", 1920, 1080, 6000, 9000, "h264", "mp4"),
        ]

        # Optimize ladder based on source characteristics
        optimized_levels = []

        if source_analysis:
            source_width, source_height = source_analysis.resolution
            motion_multiplier = 1.0 + (
                source_analysis.motion_intensity * 0.5
            )  # Up to 1.5x for high motion

            for level in base_levels:
                # Skip levels higher than source resolution
                if level.width > source_width or level.height > source_height:
                    continue

                # Adjust bitrates based on motion content
                adjusted_bitrate = int(level.bitrate * motion_multiplier)
                adjusted_max_bitrate = int(level.max_bitrate * motion_multiplier)

                # Use advanced codecs for higher quality levels if available
                codec = level.codec
                if level.height >= 720 and self.config.enable_hevc_encoding:
                    codec = "hevc"
                elif level.height >= 1080 and self.config.enable_av1_encoding:
                    codec = "av1"

                optimized_level = BitrateLevel(
                    name=level.name,
                    width=level.width,
                    height=level.height,
                    bitrate=adjusted_bitrate,
                    max_bitrate=adjusted_max_bitrate,
                    codec=codec,
                    container=level.container,
                )
                optimized_levels.append(optimized_level)
        else:
            # Use base levels without optimization
            optimized_levels = base_levels

        # Ensure we have at least one level
        if not optimized_levels:
            optimized_levels = [base_levels[2]]  # Default to 480p

        logger.info(f"Generated {len(optimized_levels)} bitrate levels")
        return optimized_levels

    async def _generate_bitrate_renditions(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel],
    ) -> dict[str, Path]:
        """
        Generate multiple bitrate renditions using existing VideoProcessor infrastructure.
        """
        logger.info(f"Generating {len(bitrate_levels)} bitrate renditions")
        rendition_files = {}

        for level in bitrate_levels:
            rendition_name = f"{video_id}_{level.name}"
            rendition_dir = output_dir / level.name
            rendition_dir.mkdir(exist_ok=True)

            # Create specialized config for this bitrate level
            rendition_config = ProcessorConfig(
                base_path=rendition_dir,
                output_formats=[self._get_output_format(level.codec)],
                quality_preset=self._get_quality_preset_for_bitrate(level.bitrate),
                custom_ffmpeg_options=self._get_ffmpeg_options_for_level(level),
            )

            # Process video at this bitrate level
            try:
                processor = VideoProcessor(rendition_config)
                result = await asyncio.to_thread(
                    processor.process_video, source_path, rendition_name
                )

                # Get the generated file
                format_name = self._get_output_format(level.codec)
                if format_name in result.encoded_files:
                    rendition_files[level.name] = result.encoded_files[format_name]
                    logger.info(
                        f"Generated {level.name} rendition: {result.encoded_files[format_name]}"
                    )
                else:
                    logger.error(f"Failed to generate {level.name} rendition")

            except Exception as e:
                logger.error(f"Error generating {level.name} rendition: {e}")
                raise EncodingError(f"Failed to generate {level.name} rendition: {e}")

        return rendition_files

    def _get_output_format(self, codec: str) -> str:
        """Map codec to output format."""
        codec_map = {
            "h264": "mp4",
            "hevc": "hevc",
            "av1": "av1_mp4",
        }
        return codec_map.get(codec, "mp4")

    def _get_quality_preset_for_bitrate(self, bitrate: int) -> str:
        """Select quality preset based on target bitrate."""
        if bitrate < 1000:
            return "low"
        elif bitrate < 3000:
            return "medium"
        elif bitrate < 8000:
            return "high"
        else:
            return "ultra"

    def _get_ffmpeg_options_for_level(self, level: BitrateLevel) -> dict[str, str]:
        """Generate FFmpeg options for specific bitrate level."""
        return {
            "b:v": f"{level.bitrate}k",
            "maxrate": f"{level.max_bitrate}k",
            "bufsize": f"{level.max_bitrate * 2}k",
            "s": f"{level.width}x{level.height}",
        }

    async def _generate_hls_playlist(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel],
        rendition_files: dict[str, Path],
    ) -> Path:
        """Generate HLS master playlist and segment individual renditions."""
        from .hls import HLSGenerator

        hls_generator = HLSGenerator()
        playlist_path = await hls_generator.create_master_playlist(
            output_dir, video_id, bitrate_levels, rendition_files
        )

        logger.info(f"HLS playlist generated: {playlist_path}")
        return playlist_path

    async def _generate_dash_manifest(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel],
        rendition_files: dict[str, Path],
    ) -> Path:
        """Generate DASH MPD manifest."""
        from .dash import DASHGenerator

        dash_generator = DASHGenerator()
        manifest_path = await dash_generator.create_manifest(
            output_dir, video_id, bitrate_levels, rendition_files
        )

        logger.info(f"DASH manifest generated: {manifest_path}")
        return manifest_path

    async def _generate_thumbnail_track(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
    ) -> Path:
        """Generate thumbnail track for video scrubbing using existing infrastructure."""
        try:
            # Use existing thumbnail generation with optimized settings
            thumbnail_config = ProcessorConfig(
                base_path=output_dir,
                thumbnail_timestamps=list(
                    range(0, 300, 10)
                ),  # Every 10 seconds up to 5 minutes
                generate_sprites=True,
                sprite_interval=5,  # More frequent for streaming
            )

            processor = VideoProcessor(thumbnail_config)
            result = await asyncio.to_thread(
                processor.process_video, source_path, f"{video_id}_thumbnails"
            )

            if result.sprite_file:
                logger.info(f"Thumbnail track generated: {result.sprite_file}")
                return result.sprite_file
            else:
                logger.warning("No thumbnail track generated")
                return None

        except Exception as e:
            logger.error(f"Thumbnail track generation failed: {e}")
            return None

    def get_streaming_capabilities(self) -> dict[str, bool]:
        """Get information about available streaming capabilities."""
        return {
            "hls_streaming": True,
            "dash_streaming": True,
            "ai_optimization": self.enable_ai_optimization,
            "advanced_codecs": self.config.enable_av1_encoding
            or self.config.enable_hevc_encoding,
            "thumbnail_tracks": True,
            "multi_bitrate": True,
        }
