"""360° video streaming integration with viewport-adaptive capabilities."""

import asyncio
import json
import logging
from pathlib import Path

from ..config import ProcessorConfig
from ..streaming.adaptive import AdaptiveStreamProcessor, BitrateLevel
from .models import (
    BitrateLevel360,
    ProjectionType,
    SpatialAudioType,
    SphericalMetadata,
    Video360StreamingPackage,
    ViewportConfig,
)
from .processor import Video360Processor

logger = logging.getLogger(__name__)


class Video360StreamProcessor:
    """
    Adaptive streaming processor for 360° videos.

    Extends standard adaptive streaming with 360° specific features:
    - Viewport-adaptive streaming
    - Tiled encoding for bandwidth optimization
    - Projection-specific bitrate ladders
    - Spatial audio streaming
    """

    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.video360_processor = Video360Processor(config)
        self.adaptive_stream_processor = AdaptiveStreamProcessor(config)

        logger.info("Video360StreamProcessor initialized")

    async def create_360_adaptive_stream(
        self,
        video_path: Path,
        output_dir: Path,
        video_id: str | None = None,
        streaming_formats: list[str] = None,
        enable_viewport_adaptive: bool = False,
        enable_tiled_streaming: bool = False,
        custom_viewports: list[ViewportConfig] | None = None,
    ) -> Video360StreamingPackage:
        """
        Create adaptive streaming package for 360° video.

        Args:
            video_path: Source 360° video
            output_dir: Output directory for streaming files
            video_id: Video identifier
            streaming_formats: List of streaming formats ("hls", "dash")
            enable_viewport_adaptive: Enable viewport-adaptive streaming
            enable_tiled_streaming: Enable tiled encoding for bandwidth efficiency
            custom_viewports: Custom viewport configurations

        Returns:
            Video360StreamingPackage with all streaming outputs
        """
        if video_id is None:
            video_id = video_path.stem

        if streaming_formats is None:
            streaming_formats = ["hls", "dash"]

        logger.info(f"Creating 360° adaptive stream: {video_path} -> {output_dir}")

        # Step 1: Analyze source 360° video
        analysis = await self.video360_processor.analyze_360_content(video_path)
        metadata = analysis.metadata

        if not metadata.is_spherical:
            logger.warning("Video may not be 360°, proceeding with standard streaming")

        # Step 2: Create output directory structure
        stream_dir = output_dir / video_id
        stream_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Generate 360°-optimized bitrate ladder
        bitrate_levels = await self._generate_360_bitrate_ladder(
            video_path, analysis, enable_tiled_streaming
        )

        # Step 4: Create streaming package
        streaming_package = Video360StreamingPackage(
            video_id=video_id,
            source_path=video_path,
            output_dir=stream_dir,
            metadata=metadata,
            bitrate_levels=bitrate_levels,
        )

        # Step 5: Generate multi-bitrate renditions
        rendition_files = await self._generate_360_renditions(
            video_path, stream_dir, video_id, bitrate_levels
        )

        # Step 6: Generate standard streaming manifests
        if "hls" in streaming_formats:
            streaming_package.hls_playlist = await self._generate_360_hls_playlist(
                stream_dir, video_id, bitrate_levels, rendition_files, metadata
            )

        if "dash" in streaming_formats:
            streaming_package.dash_manifest = await self._generate_360_dash_manifest(
                stream_dir, video_id, bitrate_levels, rendition_files, metadata
            )

        # Step 7: Generate viewport-specific content
        if enable_viewport_adaptive or custom_viewports:
            viewports = custom_viewports or analysis.recommended_viewports[:6]  # Top 6
            streaming_package.viewport_extractions = (
                await self._generate_viewport_streams(
                    video_path, stream_dir, video_id, viewports
                )
            )

        # Step 8: Generate tiled streaming manifests
        if enable_tiled_streaming and analysis.supports_tiled_encoding:
            streaming_package.tile_manifests = await self._generate_tiled_manifests(
                rendition_files, stream_dir, video_id, metadata
            )

            # Create viewport-adaptive manifest
            streaming_package.viewport_adaptive_manifest = (
                await self._create_viewport_adaptive_manifest(
                    stream_dir, video_id, streaming_package
                )
            )

        # Step 9: Generate projection-specific thumbnails
        streaming_package.thumbnail_tracks = await self._generate_projection_thumbnails(
            video_path, stream_dir, video_id, metadata
        )

        # Step 10: Handle spatial audio
        if metadata.has_spatial_audio:
            streaming_package.spatial_audio_tracks = (
                await self._generate_spatial_audio_tracks(
                    video_path, stream_dir, video_id, metadata
                )
            )

        logger.info("360° streaming package created successfully")
        return streaming_package

    async def _generate_360_bitrate_ladder(
        self, video_path: Path, analysis, enable_tiled: bool
    ) -> list[BitrateLevel360]:
        """Generate 360°-optimized bitrate ladder."""

        # Base bitrate levels adjusted for 360° content
        base_levels = [
            BitrateLevel360(
                "360p", 1280, 640, 800, 1200, analysis.metadata.projection, "h264"
            ),
            BitrateLevel360(
                "480p", 1920, 960, 1500, 2250, analysis.metadata.projection, "h264"
            ),
            BitrateLevel360(
                "720p", 2560, 1280, 3000, 4500, analysis.metadata.projection, "h264"
            ),
            BitrateLevel360(
                "1080p", 3840, 1920, 6000, 9000, analysis.metadata.projection, "hevc"
            ),
            BitrateLevel360(
                "1440p", 5120, 2560, 12000, 18000, analysis.metadata.projection, "hevc"
            ),
        ]

        # Apply 360° bitrate multiplier
        multiplier = self._get_projection_bitrate_multiplier(
            analysis.metadata.projection
        )

        optimized_levels = []
        for level in base_levels:
            # Skip levels higher than source resolution
            if (
                level.width > analysis.metadata.width
                or level.height > analysis.metadata.height
            ):
                continue

            # Apply projection-specific multiplier
            level.bitrate_multiplier = multiplier

            # Enable tiled encoding for high resolutions
            if enable_tiled and level.height >= 1920:
                level.tiled_encoding = True
                level.tile_columns = 6 if level.height >= 2560 else 4
                level.tile_rows = 3 if level.height >= 2560 else 2

            # Adjust bitrate based on motion analysis
            if hasattr(analysis.quality, "motion_intensity"):
                motion_multiplier = 1.0 + (analysis.quality.motion_intensity * 0.3)
                level.bitrate = int(level.bitrate * motion_multiplier)
                level.max_bitrate = int(level.max_bitrate * motion_multiplier)

            optimized_levels.append(level)

        # Ensure we have at least one level
        if not optimized_levels:
            optimized_levels = [base_levels[2]]  # Default to 720p

        logger.info(f"Generated {len(optimized_levels)} 360° bitrate levels")
        return optimized_levels

    def _get_projection_bitrate_multiplier(self, projection: ProjectionType) -> float:
        """Get bitrate multiplier for projection type."""
        multipliers = {
            ProjectionType.EQUIRECTANGULAR: 2.8,  # Higher due to pole distortion
            ProjectionType.CUBEMAP: 2.3,  # More efficient
            ProjectionType.EAC: 2.5,  # YouTube optimized
            ProjectionType.FISHEYE: 2.2,  # Dual fisheye
            ProjectionType.STEREOGRAPHIC: 2.0,  # Little planet style
        }

        return multipliers.get(projection, 2.5)  # Default multiplier

    async def _generate_360_renditions(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel360],
    ) -> dict[str, Path]:
        """Generate multiple 360° bitrate renditions."""
        logger.info(f"Generating {len(bitrate_levels)} 360° renditions")

        rendition_files = {}

        for level in bitrate_levels:
            rendition_name = f"{video_id}_{level.name}"
            rendition_dir = output_dir / level.name
            rendition_dir.mkdir(exist_ok=True)

            # Build FFmpeg command for 360° encoding
            cmd = [
                "ffmpeg",
                "-i",
                str(source_path),
                "-c:v",
                self._get_encoder_for_codec(level.codec),
                "-b:v",
                f"{level.get_effective_bitrate()}k",
                "-maxrate",
                f"{level.get_effective_max_bitrate()}k",
                "-bufsize",
                f"{level.get_effective_max_bitrate() * 2}k",
                "-s",
                f"{level.width}x{level.height}",
                "-preset",
                "medium",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
            ]

            # Add tiling if enabled
            if level.tiled_encoding:
                cmd.extend(
                    [
                        "-tiles",
                        f"{level.tile_columns}x{level.tile_rows}",
                        "-tile-columns",
                        str(level.tile_columns),
                        "-tile-rows",
                        str(level.tile_rows),
                    ]
                )

            # Preserve 360° metadata
            cmd.extend(
                [
                    "-metadata",
                    "spherical=1",
                    "-metadata",
                    f"projection={level.projection.value}",
                ]
            )

            output_path = rendition_dir / f"{rendition_name}.mp4"
            cmd.extend([str(output_path), "-y"])

            # Execute encoding
            try:
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True
                )

                if result.returncode == 0:
                    rendition_files[level.name] = output_path
                    logger.info(f"Generated 360° rendition: {level.name}")
                else:
                    logger.error(f"Failed to generate {level.name}: {result.stderr}")

            except Exception as e:
                logger.error(f"Error generating {level.name} rendition: {e}")

        return rendition_files

    def _get_encoder_for_codec(self, codec: str) -> str:
        """Get FFmpeg encoder for codec."""
        encoders = {
            "h264": "libx264",
            "hevc": "libx265",
            "av1": "libaom-av1",
        }
        return encoders.get(codec, "libx264")

    async def _generate_360_hls_playlist(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel360],
        rendition_files: dict[str, Path],
        metadata: SphericalMetadata,
    ) -> Path:
        """Generate HLS playlist with 360° metadata."""
        from ..streaming.hls import HLSGenerator

        # Convert to standard BitrateLevel for HLS generator
        standard_levels = []
        for level in bitrate_levels:
            if level.name in rendition_files:
                standard_level = BitrateLevel(
                    name=level.name,
                    width=level.width,
                    height=level.height,
                    bitrate=level.get_effective_bitrate(),
                    max_bitrate=level.get_effective_max_bitrate(),
                    codec=level.codec,
                    container=level.container,
                )
                standard_levels.append(standard_level)

        hls_generator = HLSGenerator()
        playlist_path = await hls_generator.create_master_playlist(
            output_dir, video_id, standard_levels, rendition_files
        )

        # Add 360° metadata to master playlist
        await self._add_360_metadata_to_hls(playlist_path, metadata)

        return playlist_path

    async def _generate_360_dash_manifest(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel360],
        rendition_files: dict[str, Path],
        metadata: SphericalMetadata,
    ) -> Path:
        """Generate DASH manifest with 360° metadata."""
        from ..streaming.dash import DASHGenerator

        # Convert to standard BitrateLevel for DASH generator
        standard_levels = []
        for level in bitrate_levels:
            if level.name in rendition_files:
                standard_level = BitrateLevel(
                    name=level.name,
                    width=level.width,
                    height=level.height,
                    bitrate=level.get_effective_bitrate(),
                    max_bitrate=level.get_effective_max_bitrate(),
                    codec=level.codec,
                    container=level.container,
                )
                standard_levels.append(standard_level)

        dash_generator = DASHGenerator()
        manifest_path = await dash_generator.create_manifest(
            output_dir, video_id, standard_levels, rendition_files
        )

        # Add 360° metadata to DASH manifest
        await self._add_360_metadata_to_dash(manifest_path, metadata)

        return manifest_path

    async def _generate_viewport_streams(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
        viewports: list[ViewportConfig],
    ) -> dict[str, Path]:
        """Generate viewport-specific streams."""
        viewport_dir = output_dir / "viewports"
        viewport_dir.mkdir(exist_ok=True)

        viewport_files = {}

        for i, viewport in enumerate(viewports):
            viewport_name = f"viewport_{i}_{int(viewport.yaw)}_{int(viewport.pitch)}"
            output_path = viewport_dir / f"{viewport_name}.mp4"

            try:
                result = await self.video360_processor.extract_viewport(
                    source_path, output_path, viewport
                )

                if result.success:
                    viewport_files[viewport_name] = output_path
                    logger.info(f"Generated viewport stream: {viewport_name}")

            except Exception as e:
                logger.error(f"Failed to generate viewport {viewport_name}: {e}")

        return viewport_files

    async def _generate_tiled_manifests(
        self,
        rendition_files: dict[str, Path],
        output_dir: Path,
        video_id: str,
        metadata: SphericalMetadata,
    ) -> dict[str, Path]:
        """Generate tiled streaming manifests."""
        tile_dir = output_dir / "tiles"
        tile_dir.mkdir(exist_ok=True)

        tile_manifests = {}

        # Generate tiled manifests for each rendition
        for level_name, rendition_file in rendition_files.items():
            tile_manifest_path = tile_dir / f"{level_name}_tiles.m3u8"

            # Create simple tiled manifest (simplified implementation)
            manifest_content = f"""#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-SPHERICAL:projection={metadata.projection.value}
#EXT-X-TILES:grid=4x4,duration=6
{level_name}_tile_000000.ts
#EXT-X-ENDLIST
"""

            with open(tile_manifest_path, "w") as f:
                f.write(manifest_content)

            tile_manifests[level_name] = tile_manifest_path
            logger.info(f"Generated tile manifest: {level_name}")

        return tile_manifests

    async def _create_viewport_adaptive_manifest(
        self,
        output_dir: Path,
        video_id: str,
        streaming_package: Video360StreamingPackage,
    ) -> Path:
        """Create viewport-adaptive streaming manifest."""
        manifest_path = output_dir / f"{video_id}_viewport_adaptive.json"

        # Create viewport-adaptive manifest
        manifest_data = {
            "version": "1.0",
            "type": "viewport_adaptive",
            "video_id": video_id,
            "projection": streaming_package.metadata.projection.value,
            "stereo_mode": streaming_package.metadata.stereo_mode.value,
            "bitrate_levels": [
                {
                    "name": level.name,
                    "width": level.width,
                    "height": level.height,
                    "bitrate": level.get_effective_bitrate(),
                    "tiled": level.tiled_encoding,
                    "tiles": f"{level.tile_columns}x{level.tile_rows}"
                    if level.tiled_encoding
                    else None,
                }
                for level in streaming_package.bitrate_levels
            ],
            "viewport_streams": {
                name: str(path.relative_to(output_dir))
                for name, path in streaming_package.viewport_extractions.items()
            },
            "tile_manifests": {
                name: str(path.relative_to(output_dir))
                for name, path in streaming_package.tile_manifests.items()
            }
            if streaming_package.tile_manifests
            else {},
            "spatial_audio": {
                "has_spatial_audio": streaming_package.metadata.has_spatial_audio,
                "audio_type": streaming_package.metadata.audio_type.value,
                "tracks": {
                    name: str(path.relative_to(output_dir))
                    for name, path in streaming_package.spatial_audio_tracks.items()
                }
                if streaming_package.spatial_audio_tracks
                else {},
            },
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)

        logger.info(f"Created viewport-adaptive manifest: {manifest_path}")
        return manifest_path

    async def _generate_projection_thumbnails(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
        metadata: SphericalMetadata,
    ) -> dict[ProjectionType, Path]:
        """Generate thumbnails for different projections."""
        thumbnail_dir = output_dir / "thumbnails"
        thumbnail_dir.mkdir(exist_ok=True)

        thumbnail_tracks = {}

        # Generate thumbnails for current projection
        current_projection_thumb = (
            thumbnail_dir / f"{video_id}_{metadata.projection.value}_thumbnails.jpg"
        )

        # Use existing thumbnail generation (simplified)
        cmd = [
            "ffmpeg",
            "-i",
            str(source_path),
            "-vf",
            "select=eq(n\\,0),scale=320:160",
            "-vframes",
            "1",
            str(current_projection_thumb),
            "-y",
        ]

        try:
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if result.returncode == 0:
                thumbnail_tracks[metadata.projection] = current_projection_thumb
                logger.info(f"Generated {metadata.projection.value} thumbnail")

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")

        # Generate stereographic (little planet) thumbnail if equirectangular
        if metadata.projection == ProjectionType.EQUIRECTANGULAR:
            stereo_thumb = thumbnail_dir / f"{video_id}_stereographic_thumbnail.jpg"

            cmd = [
                "ffmpeg",
                "-i",
                str(source_path),
                "-vf",
                "v360=e:sg,select=eq(n\\,0),scale=320:320",
                "-vframes",
                "1",
                str(stereo_thumb),
                "-y",
            ]

            try:
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True
                )

                if result.returncode == 0:
                    thumbnail_tracks[ProjectionType.STEREOGRAPHIC] = stereo_thumb
                    logger.info("Generated stereographic thumbnail")

            except Exception as e:
                logger.error(f"Stereographic thumbnail failed: {e}")

        return thumbnail_tracks

    async def _generate_spatial_audio_tracks(
        self,
        source_path: Path,
        output_dir: Path,
        video_id: str,
        metadata: SphericalMetadata,
    ) -> dict[str, Path]:
        """Generate spatial audio tracks."""
        audio_dir = output_dir / "spatial_audio"
        audio_dir.mkdir(exist_ok=True)

        spatial_tracks = {}

        # Extract original spatial audio
        original_track = audio_dir / f"{video_id}_spatial_original.aac"

        cmd = [
            "ffmpeg",
            "-i",
            str(source_path),
            "-vn",  # No video
            "-c:a",
            "aac",
            "-b:a",
            "256k",  # Higher bitrate for spatial audio
            str(original_track),
            "-y",
        ]

        try:
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if result.returncode == 0:
                spatial_tracks["original"] = original_track
                logger.info("Generated original spatial audio track")

        except Exception as e:
            logger.error(f"Spatial audio extraction failed: {e}")

        # Generate binaural version for headphone users
        if metadata.audio_type != SpatialAudioType.BINAURAL:
            from .spatial_audio import SpatialAudioProcessor

            binaural_track = audio_dir / f"{video_id}_binaural.aac"

            try:
                spatial_processor = SpatialAudioProcessor()
                result = await spatial_processor.convert_to_binaural(
                    source_path, binaural_track
                )

                if result.success:
                    spatial_tracks["binaural"] = binaural_track
                    logger.info("Generated binaural audio track")

            except Exception as e:
                logger.error(f"Binaural conversion failed: {e}")

        return spatial_tracks

    async def _add_360_metadata_to_hls(
        self, playlist_path: Path, metadata: SphericalMetadata
    ):
        """Add 360° metadata to HLS playlist."""
        # Read existing playlist
        with open(playlist_path) as f:
            content = f.read()

        # Add 360° metadata after #EXT-X-VERSION
        spherical_tag = f"#EXT-X-SPHERICAL:projection={metadata.projection.value}"
        if metadata.is_stereoscopic:
            spherical_tag += f",stereo_mode={metadata.stereo_mode.value}"

        # Insert after version tag
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-VERSION"):
                lines.insert(i + 1, spherical_tag)
                break

        # Write back
        with open(playlist_path, "w") as f:
            f.write("\n".join(lines))

    async def _add_360_metadata_to_dash(
        self, manifest_path: Path, metadata: SphericalMetadata
    ):
        """Add 360° metadata to DASH manifest."""
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            # Add spherical metadata as supplemental property
            for adaptation_set in root.findall(
                ".//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet"
            ):
                if adaptation_set.get("contentType") == "video":
                    # Add supplemental property for spherical video
                    supp_prop = ET.SubElement(adaptation_set, "SupplementalProperty")
                    supp_prop.set("schemeIdUri", "http://youtube.com/yt/spherical")
                    supp_prop.set("value", "1")

                    # Add projection property
                    proj_prop = ET.SubElement(adaptation_set, "SupplementalProperty")
                    proj_prop.set("schemeIdUri", "http://youtube.com/yt/projection")
                    proj_prop.set("value", metadata.projection.value)

                    break

            # Write back
            tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

        except Exception as e:
            logger.error(f"Failed to add 360° metadata to DASH: {e}")


import subprocess  # Add this import at the top
