"""Core 360° video processor."""

import asyncio
import json
import logging
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from ..config import ProcessorConfig
from ..exceptions import VideoProcessorError
from .models import (
    ProjectionType,
    SphericalMetadata,
    StereoMode,
    Video360Analysis,
    Video360ProcessingResult,
    Video360Quality,
    ViewportConfig,
)

# Optional AI integration
try:
    from ..ai.content_analyzer import VideoContentAnalyzer

    HAS_AI_SUPPORT = True
except ImportError:
    HAS_AI_SUPPORT = False

logger = logging.getLogger(__name__)


class Video360Processor:
    """
    Core 360° video processing engine.

    Provides projection conversion, viewport extraction, stereoscopic processing,
    and spatial audio handling for 360° videos.
    """

    def __init__(self, config: ProcessorConfig):
        self.config = config

        # Initialize AI analyzer if available
        self.content_analyzer = None
        if HAS_AI_SUPPORT and config.enable_ai_analysis:
            self.content_analyzer = VideoContentAnalyzer()

        logger.info(
            f"Video360Processor initialized with AI support: {self.content_analyzer is not None}"
        )

    async def extract_spherical_metadata(self, video_path: Path) -> SphericalMetadata:
        """
        Extract spherical metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            SphericalMetadata object with detected properties
        """
        try:
            # Use ffprobe to extract video metadata
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(video_path),
            ]

            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, check=True
            )

            probe_data = json.loads(result.stdout)

            # Initialize metadata object
            metadata = SphericalMetadata()

            # Extract basic video properties
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    metadata.width = stream.get("width", 0)
                    metadata.height = stream.get("height", 0)
                    if metadata.width > 0 and metadata.height > 0:
                        metadata.aspect_ratio = metadata.width / metadata.height
                    break

            # Check for spherical metadata in format tags
            format_tags = probe_data.get("format", {}).get("tags", {})
            metadata = self._parse_spherical_tags(format_tags, metadata)

            # Check for spherical metadata in stream tags
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    stream_tags = stream.get("tags", {})
                    metadata = self._parse_spherical_tags(stream_tags, metadata)
                    break

            # If no metadata found, try to infer from video properties
            if not metadata.is_spherical:
                metadata = self._infer_360_properties(metadata, video_path)

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract spherical metadata: {e}")
            raise VideoProcessorError(f"Metadata extraction failed: {e}")

    def _parse_spherical_tags(
        self, tags: dict, metadata: SphericalMetadata
    ) -> SphericalMetadata:
        """Parse spherical metadata tags."""
        # Google spherical video standard tags
        spherical_indicators = {
            "spherical": True,
            "Spherical": True,
            "spherical-video": True,
            "SphericalVideo": True,
        }

        # Check for spherical indicators
        for tag_name, tag_value in tags.items():
            if tag_name in spherical_indicators:
                metadata.is_spherical = True
                metadata.confidence = 1.0
                metadata.detection_methods.append("spherical_metadata")
                break

        # Parse projection type
        projection_tags = ["ProjectionType", "projection_type", "projection"]
        for tag in projection_tags:
            if tag in tags:
                proj_value = tags[tag].lower()
                if "equirectangular" in proj_value:
                    metadata.projection = ProjectionType.EQUIRECTANGULAR
                elif "cubemap" in proj_value:
                    metadata.projection = ProjectionType.CUBEMAP
                elif "eac" in proj_value:
                    metadata.projection = ProjectionType.EAC
                elif "fisheye" in proj_value:
                    metadata.projection = ProjectionType.FISHEYE
                break

        # Parse stereo mode
        stereo_tags = ["StereoMode", "stereo_mode", "StereoscopicMode"]
        for tag in stereo_tags:
            if tag in tags:
                stereo_value = tags[tag].lower()
                if "top-bottom" in stereo_value or "tb" in stereo_value:
                    metadata.stereo_mode = StereoMode.TOP_BOTTOM
                elif "left-right" in stereo_value or "lr" in stereo_value:
                    metadata.stereo_mode = StereoMode.LEFT_RIGHT
                break

        # Parse initial view
        view_tags = {
            "initial_view_heading_degrees": "initial_view_heading",
            "initial_view_pitch_degrees": "initial_view_pitch",
            "initial_view_roll_degrees": "initial_view_roll",
        }

        for tag, attr in view_tags.items():
            if tag in tags:
                try:
                    setattr(metadata, attr, float(tags[tag]))
                except ValueError:
                    pass

        # Parse field of view
        fov_tags = {"fov_horizontal": "fov_horizontal", "fov_vertical": "fov_vertical"}

        for tag, attr in fov_tags.items():
            if tag in tags:
                try:
                    setattr(metadata, attr, float(tags[tag]))
                except ValueError:
                    pass

        return metadata

    def _infer_360_properties(
        self, metadata: SphericalMetadata, video_path: Path
    ) -> SphericalMetadata:
        """Infer 360° properties from video characteristics."""
        # Check aspect ratio for equirectangular
        if metadata.aspect_ratio > 0:
            if 1.9 <= metadata.aspect_ratio <= 2.1:
                metadata.is_spherical = True
                metadata.projection = ProjectionType.EQUIRECTANGULAR
                metadata.confidence = 0.8
                metadata.detection_methods.append("aspect_ratio")

                # Higher confidence for exact 2:1 ratio
                if 1.98 <= metadata.aspect_ratio <= 2.02:
                    metadata.confidence = 0.9

        # Check filename patterns
        filename = video_path.name.lower()
        patterns_360 = ["360", "vr", "spherical", "equirectangular", "panoramic"]

        for pattern in patterns_360:
            if pattern in filename:
                if not metadata.is_spherical:
                    metadata.is_spherical = True
                    metadata.projection = ProjectionType.EQUIRECTANGULAR
                    metadata.confidence = 0.6
                metadata.detection_methods.append("filename")
                break

        # Check for stereoscopic indicators in filename
        if any(pattern in filename for pattern in ["stereo", "3d", "sbs", "tb"]):
            if "sbs" in filename:
                metadata.stereo_mode = StereoMode.LEFT_RIGHT
            elif "tb" in filename:
                metadata.stereo_mode = StereoMode.TOP_BOTTOM

        return metadata

    async def analyze_360_content(self, video_path: Path) -> Video360Analysis:
        """
        Perform comprehensive 360° video analysis.

        Args:
            video_path: Path to 360° video file

        Returns:
            Video360Analysis with metadata, quality metrics, and recommendations
        """
        # Extract spherical metadata
        metadata = await self.extract_spherical_metadata(video_path)

        # Analyze quality
        quality = await self._analyze_360_quality(video_path, metadata)

        # Create analysis object
        analysis = Video360Analysis(
            metadata=metadata,
            quality=quality,
            supports_viewport_adaptive=metadata.is_spherical,
            supports_tiled_encoding=metadata.is_spherical and metadata.width >= 3840,
        )

        # Generate recommendations
        if metadata.is_spherical:
            analysis.optimal_projections = self._get_optimal_projections(metadata)
            analysis.recommended_viewports = self._generate_recommended_viewports(metadata)

        return analysis

    async def _analyze_360_quality(self, video_path: Path, metadata: SphericalMetadata) -> Video360Quality:
        """Analyze quality metrics for 360° video."""
        quality = Video360Quality()

        # Basic quality analysis (simplified)
        if metadata.is_spherical:
            # Projection quality based on type
            projection_quality_map = {
                ProjectionType.EQUIRECTANGULAR: 0.7,  # Pole distortion issues
                ProjectionType.CUBEMAP: 0.85,
                ProjectionType.EAC: 0.9,
                ProjectionType.FISHEYE: 0.75,
                ProjectionType.STEREOGRAPHIC: 0.6,
            }
            quality.projection_quality = projection_quality_map.get(metadata.projection, 0.5)

            # Viewport quality (based on resolution)
            if metadata.width >= 3840:
                quality.viewport_quality = 0.9
            elif metadata.width >= 1920:
                quality.viewport_quality = 0.7
            else:
                quality.viewport_quality = 0.5

            # Seam quality (better for higher order projections)
            if metadata.projection in [ProjectionType.CUBEMAP, ProjectionType.EAC]:
                quality.seam_quality = 0.9
            else:
                quality.seam_quality = 0.7

            # Pole distortion (mainly affects equirectangular)
            if metadata.projection == ProjectionType.EQUIRECTANGULAR:
                quality.pole_distortion = 0.3  # Higher distortion
            else:
                quality.pole_distortion = 0.1  # Lower distortion

        return quality

    def _get_optimal_projections(self, metadata: SphericalMetadata) -> list[ProjectionType]:
        """Get optimal projections for content."""
        if metadata.projection == ProjectionType.EQUIRECTANGULAR:
            return [ProjectionType.EAC, ProjectionType.CUBEMAP, ProjectionType.STEREOGRAPHIC]
        elif metadata.projection == ProjectionType.CUBEMAP:
            return [ProjectionType.EAC, ProjectionType.EQUIRECTANGULAR]
        else:
            return [ProjectionType.EQUIRECTANGULAR, ProjectionType.CUBEMAP]

    def _generate_recommended_viewports(self, metadata: SphericalMetadata) -> list[ViewportConfig]:
        """Generate recommended viewports for content."""
        viewports = [
            ViewportConfig(yaw=0, pitch=0, fov=90, width=1920, height=1080),     # Front
            ViewportConfig(yaw=180, pitch=0, fov=90, width=1920, height=1080),   # Back
            ViewportConfig(yaw=90, pitch=0, fov=90, width=1920, height=1080),    # Right
            ViewportConfig(yaw=-90, pitch=0, fov=90, width=1920, height=1080),   # Left
            ViewportConfig(yaw=0, pitch=90, fov=90, width=1920, height=1080),    # Up
            ViewportConfig(yaw=0, pitch=-90, fov=90, width=1920, height=1080),   # Down
        ]
        return viewports

    async def extract_viewport(
        self,
        input_path: Path,
        output_path: Path,
        viewport: ViewportConfig
    ) -> Video360ProcessingResult:
        """
        Extract viewport from 360° video.

        Args:
            input_path: Source 360° video
            output_path: Output viewport video
            viewport: Viewport configuration

        Returns:
            Video360ProcessingResult with extraction details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="viewport_extraction")

        try:
            if not viewport.validate():
                raise VideoProcessorError("Invalid viewport configuration")

            # Build v360 filter for viewport extraction
            v360_filter = (
                f"v360=e:flat"
                f":yaw={viewport.yaw}"
                f":pitch={viewport.pitch}"
                f":roll={viewport.roll}"
                f":h_fov={viewport.fov}"
                f":v_fov={viewport.fov * 9/16}"  # 16:9 aspect ratio
                f":w={viewport.width}"
                f":h={viewport.height}"
            )

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i", str(input_path),
                "-vf", v360_filter,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "copy",
                str(output_path),
                "-y"
            ]

            # Execute extraction
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                logger.info(f"Viewport extraction successful: {viewport.yaw}°/{viewport.pitch}°")
            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Viewport extraction error: {e}")

        result.processing_time = time.time() - start_time
        return result

    async def convert_projection(
        self,
        input_path: Path,
        output_path: Path,
        target_projection: ProjectionType,
        output_resolution: tuple | None = None,
        source_projection: ProjectionType | None = None,
    ) -> Video360ProcessingResult:
        """
        Convert between different 360° projections.

        Args:
            input_path: Source video path
            output_path: Output video path
            target_projection: Target projection type
            output_resolution: Optional (width, height) tuple
            source_projection: Source projection (auto-detect if None)

        Returns:
            Video360ProcessingResult with conversion details
        """
        start_time = time.time()
        result = Video360ProcessingResult(
            operation=f"projection_conversion_to_{target_projection.value}"
        )

        try:
            # Extract source metadata
            source_metadata = await self.extract_spherical_metadata(input_path)
            result.input_metadata = source_metadata

            # Determine source projection
            if source_projection is None:
                source_projection = source_metadata.projection
                if source_projection == ProjectionType.UNKNOWN:
                    source_projection = (
                        ProjectionType.EQUIRECTANGULAR
                    )  # Default assumption
                    result.add_warning(
                        "Unknown source projection, assuming equirectangular"
                    )

            # Build FFmpeg v360 filter command
            v360_filter = self._build_v360_filter(
                source_projection, target_projection, output_resolution
            )

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-vf",
                v360_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",  # Copy audio unchanged
                str(output_path),
                "-y",
            ]

            # Add spherical metadata for output
            if target_projection != ProjectionType.FLAT:
                cmd.extend(
                    [
                        "-metadata",
                        "spherical=1",
                        "-metadata",
                        f"projection={target_projection.value}",
                    ]
                )

            # Execute conversion
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                # Create output metadata
                output_metadata = SphericalMetadata(
                    is_spherical=(target_projection != ProjectionType.FLAT),
                    projection=target_projection,
                    stereo_mode=source_metadata.stereo_mode,
                    width=output_resolution[0]
                    if output_resolution
                    else source_metadata.width,
                    height=output_resolution[1]
                    if output_resolution
                    else source_metadata.height,
                )
                result.output_metadata = output_metadata

                logger.info(
                    f"Projection conversion successful: {source_projection.value} -> {target_projection.value}"
                )

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")
                logger.error(f"Projection conversion failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Conversion error: {e}")
            logger.error(f"Projection conversion error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_v360_filter(
        self,
        source_proj: ProjectionType,
        target_proj: ProjectionType,
        output_resolution: tuple | None = None,
    ) -> str:
        """Build FFmpeg v360 filter string."""
        # Map projection types to v360 format codes
        projection_map = {
            ProjectionType.EQUIRECTANGULAR: "e",
            ProjectionType.CUBEMAP: "c3x2",
            ProjectionType.EAC: "eac",
            ProjectionType.FISHEYE: "fisheye",
            ProjectionType.DUAL_FISHEYE: "dfisheye",
            ProjectionType.FLAT: "flat",
            ProjectionType.STEREOGRAPHIC: "sg",
            ProjectionType.MERCATOR: "mercator",
            ProjectionType.PANNINI: "pannini",
            ProjectionType.CYLINDRICAL: "cylindrical",
            ProjectionType.LITTLE_PLANET: "sg",  # Stereographic for little planet
        }

        source_format = projection_map.get(source_proj, "e")
        target_format = projection_map.get(target_proj, "e")

        filter_parts = [f"v360={source_format}:{target_format}"]

        # Add resolution if specified
        if output_resolution:
            filter_parts.append(f"w={output_resolution[0]}:h={output_resolution[1]}")

        return ":".join(filter_parts)

    async def extract_viewport(
        self, input_path: Path, output_path: Path, viewport_config: ViewportConfig
    ) -> Video360ProcessingResult:
        """
        Extract flat viewport from 360° video.

        Args:
            input_path: Source 360° video
            output_path: Output flat video
            viewport_config: Viewport extraction settings

        Returns:
            Video360ProcessingResult with extraction details
        """
        if not viewport_config.validate():
            raise VideoProcessorError("Invalid viewport configuration")

        start_time = time.time()
        result = Video360ProcessingResult(operation="viewport_extraction")

        try:
            # Extract source metadata
            source_metadata = await self.extract_spherical_metadata(input_path)
            result.input_metadata = source_metadata

            if not source_metadata.is_spherical:
                result.add_warning("Source video may not be 360°")

            # Build v360 filter for viewport extraction
            v360_filter = (
                f"v360={source_metadata.projection.value}:flat:"
                f"yaw={viewport_config.yaw}:"
                f"pitch={viewport_config.pitch}:"
                f"roll={viewport_config.roll}:"
                f"fov={viewport_config.fov}:"
                f"w={viewport_config.width}:"
                f"h={viewport_config.height}"
            )

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-vf",
                v360_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                str(output_path),
                "-y",
            ]

            # Execute extraction
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                # Output is flat video (no spherical metadata)
                output_metadata = SphericalMetadata(
                    is_spherical=False,
                    projection=ProjectionType.FLAT,
                    width=viewport_config.width,
                    height=viewport_config.height,
                )
                result.output_metadata = output_metadata

                logger.info(
                    f"Viewport extraction successful: yaw={viewport_config.yaw}, pitch={viewport_config.pitch}"
                )

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Viewport extraction error: {e}")

        result.processing_time = time.time() - start_time
        return result

    async def extract_animated_viewport(
        self,
        input_path: Path,
        output_path: Path,
        viewport_function: Callable[[float], tuple],
    ) -> Video360ProcessingResult:
        """
        Extract animated viewport with camera movement.

        Args:
            input_path: Source 360° video
            output_path: Output flat video
            viewport_function: Function that takes time (seconds) and returns
                             (yaw, pitch, roll, fov) tuple

        Returns:
            Video360ProcessingResult with extraction details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="animated_viewport_extraction")

        try:
            # Get video duration first
            duration = await self._get_video_duration(input_path)

            # Sample viewport function to create expression
            sample_times = [0, duration / 4, duration / 2, 3 * duration / 4, duration]
            sample_viewports = [viewport_function(t) for t in sample_times]

            # For now, use a simplified linear interpolation
            # In a full implementation, this would generate complex FFmpeg expressions
            start_yaw, start_pitch, start_roll, start_fov = sample_viewports[0]
            end_yaw, end_pitch, end_roll, end_fov = sample_viewports[-1]

            # Create animated v360 filter
            v360_filter = (
                f"v360=e:flat:"
                f"yaw='({start_yaw})+({end_yaw}-{start_yaw})*t/{duration}':"
                f"pitch='({start_pitch})+({end_pitch}-{start_pitch})*t/{duration}':"
                f"roll='({start_roll})+({end_roll}-{start_roll})*t/{duration}':"
                f"fov='({start_fov})+({end_fov}-{start_fov})*t/{duration}':"
                f"w=1920:h=1080"
            )

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-vf",
                v360_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                str(output_path),
                "-y",
            ]

            # Execute extraction
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                logger.info("Animated viewport extraction successful")
            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Animated viewport extraction error: {e}")

        result.processing_time = time.time() - start_time
        return result

    async def stereo_to_mono(
        self, input_path: Path, output_path: Path, eye: str = "left"
    ) -> Video360ProcessingResult:
        """
        Convert stereoscopic 360° video to monoscopic.

        Args:
            input_path: Source stereoscopic video
            output_path: Output monoscopic video
            eye: Which eye to extract ("left" or "right")

        Returns:
            Video360ProcessingResult with conversion details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation=f"stereo_to_mono_{eye}")

        try:
            # Extract source metadata
            source_metadata = await self.extract_spherical_metadata(input_path)
            result.input_metadata = source_metadata

            if source_metadata.stereo_mode == StereoMode.MONO:
                result.add_warning("Source video is already monoscopic")
                # Copy file instead of processing
                import shutil

                shutil.copy2(input_path, output_path)
                result.success = True
                result.output_path = output_path
                return result

            # Build crop filter based on stereo mode
            if source_metadata.stereo_mode == StereoMode.TOP_BOTTOM:
                if eye == "left":
                    crop_filter = "crop=iw:ih/2:0:0"  # Top half
                else:
                    crop_filter = "crop=iw:ih/2:0:ih/2"  # Bottom half
            elif source_metadata.stereo_mode == StereoMode.LEFT_RIGHT:
                if eye == "left":
                    crop_filter = "crop=iw/2:ih:0:0"  # Left half
                else:
                    crop_filter = "crop=iw/2:ih:iw/2:0"  # Right half
            else:
                raise VideoProcessorError(
                    f"Unsupported stereo mode: {source_metadata.stereo_mode}"
                )

            # Scale back to original resolution
            if source_metadata.stereo_mode == StereoMode.TOP_BOTTOM:
                scale_filter = "scale=iw:ih*2"
            else:  # LEFT_RIGHT
                scale_filter = "scale=iw*2:ih"

            # Combine filters
            video_filter = f"{crop_filter},{scale_filter}"

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-vf",
                video_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                "-metadata",
                "spherical=1",
                "-metadata",
                f"projection={source_metadata.projection.value}",
                "-metadata",
                "stereo_mode=mono",
                str(output_path),
                "-y",
            ]

            # Execute conversion
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                # Create output metadata
                output_metadata = source_metadata
                output_metadata.stereo_mode = StereoMode.MONO
                result.output_metadata = output_metadata

                logger.info(
                    f"Stereo to mono conversion successful: {eye} eye extracted"
                )

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Stereo to mono conversion error: {e}")

        result.processing_time = time.time() - start_time
        return result

    async def convert_stereo_mode(
        self, input_path: Path, output_path: Path, target_mode: StereoMode
    ) -> Video360ProcessingResult:
        """
        Convert between stereoscopic modes (e.g., top-bottom to side-by-side).

        Args:
            input_path: Source stereoscopic video
            output_path: Output video with new stereo mode
            target_mode: Target stereoscopic mode

        Returns:
            Video360ProcessingResult with conversion details
        """
        start_time = time.time()
        result = Video360ProcessingResult(
            operation=f"stereo_mode_conversion_to_{target_mode.value}"
        )

        try:
            # Extract source metadata
            source_metadata = await self.extract_spherical_metadata(input_path)
            result.input_metadata = source_metadata

            if not source_metadata.is_stereoscopic:
                raise VideoProcessorError("Source video is not stereoscopic")

            if source_metadata.stereo_mode == target_mode:
                result.add_warning("Source already in target stereo mode")
                import shutil

                shutil.copy2(input_path, output_path)
                result.success = True
                result.output_path = output_path
                return result

            # Build conversion filter
            conversion_filter = self._build_stereo_conversion_filter(
                source_metadata.stereo_mode, target_mode
            )

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-vf",
                conversion_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                "-metadata",
                "spherical=1",
                "-metadata",
                f"projection={source_metadata.projection.value}",
                "-metadata",
                f"stereo_mode={target_mode.value}",
                str(output_path),
                "-y",
            ]

            # Execute conversion
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                # Create output metadata
                output_metadata = source_metadata
                output_metadata.stereo_mode = target_mode
                result.output_metadata = output_metadata

                logger.info(
                    f"Stereo mode conversion successful: {source_metadata.stereo_mode.value} -> {target_mode.value}"
                )

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Stereo mode conversion error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_stereo_conversion_filter(
        self, source_mode: StereoMode, target_mode: StereoMode
    ) -> str:
        """Build FFmpeg filter for stereo mode conversion."""
        if (
            source_mode == StereoMode.TOP_BOTTOM
            and target_mode == StereoMode.LEFT_RIGHT
        ):
            # TB to SBS: split top/bottom, place side by side
            return (
                "[0:v]crop=iw:ih/2:0:0[left];"
                "[0:v]crop=iw:ih/2:0:ih/2[right];"
                "[left][right]hstack"
            )
        elif (
            source_mode == StereoMode.LEFT_RIGHT
            and target_mode == StereoMode.TOP_BOTTOM
        ):
            # SBS to TB: split left/right, stack vertically
            return (
                "[0:v]crop=iw/2:ih:0:0[left];"
                "[0:v]crop=iw/2:ih:iw/2:0[right];"
                "[left][right]vstack"
            )
        else:
            raise VideoProcessorError(
                f"Unsupported stereo conversion: {source_mode} -> {target_mode}"
            )

    async def analyze_360_content(self, video_path: Path) -> Video360Analysis:
        """
        Analyze 360° video content for optimization recommendations.

        Args:
            video_path: Path to 360° video

        Returns:
            Video360Analysis with detailed analysis results
        """
        try:
            # Extract spherical metadata
            metadata = await self.extract_spherical_metadata(video_path)

            # Initialize quality assessment
            quality = Video360Quality()

            # Use AI analyzer if available
            if self.content_analyzer:
                try:
                    ai_analysis = await self.content_analyzer.analyze_content(
                        video_path
                    )
                    quality.motion_intensity = ai_analysis.motion_intensity
                    # Map AI analysis to 360° specific metrics
                    quality.projection_quality = 0.8  # Default good quality
                    quality.viewport_quality = 0.8
                except Exception as e:
                    logger.warning(f"AI analysis failed: {e}")

            # Analyze projection-specific characteristics
            if metadata.projection == ProjectionType.EQUIRECTANGULAR:
                quality.pole_distortion = self._analyze_pole_distortion(metadata)
                quality.seam_quality = 0.9  # Equirectangular has good seam continuity

            # Generate recommendations
            analysis = Video360Analysis(metadata=metadata, quality=quality)

            # Recommend optimal projections based on content
            analysis.optimal_projections = self._recommend_projections(
                metadata, quality
            )

            # Recommend viewports for thumbnail generation
            analysis.recommended_viewports = self._recommend_viewports(metadata)

            # Streaming recommendations
            analysis.supports_viewport_adaptive = (
                metadata.projection
                in [ProjectionType.EQUIRECTANGULAR, ProjectionType.CUBEMAP]
                and quality.motion_intensity
                < 0.8  # Low motion suitable for tiled streaming
            )

            analysis.supports_tiled_encoding = (
                metadata.width >= 3840  # Minimum 4K for tiling benefits
                and metadata.projection
                in [ProjectionType.EQUIRECTANGULAR, ProjectionType.EAC]
            )

            return analysis

        except Exception as e:
            logger.error(f"360° content analysis failed: {e}")
            raise VideoProcessorError(f"Content analysis failed: {e}")

    def _analyze_pole_distortion(self, metadata: SphericalMetadata) -> float:
        """Analyze pole distortion for equirectangular projection."""
        # Simplified analysis - in practice would analyze actual pixel data
        if metadata.projection == ProjectionType.EQUIRECTANGULAR:
            # Distortion increases with resolution height
            distortion_factor = min(metadata.height / 2000, 1.0)  # Normalize to 2K
            return distortion_factor * 0.3  # Max 30% distortion
        return 0.0

    def _recommend_projections(
        self, metadata: SphericalMetadata, quality: Video360Quality
    ) -> list[ProjectionType]:
        """Recommend optimal projections based on content analysis."""
        recommendations = []

        # Always include source projection
        recommendations.append(metadata.projection)

        # Add complementary projections
        if metadata.projection == ProjectionType.EQUIRECTANGULAR:
            recommendations.extend([ProjectionType.CUBEMAP, ProjectionType.EAC])
        elif metadata.projection == ProjectionType.CUBEMAP:
            recommendations.extend([ProjectionType.EQUIRECTANGULAR, ProjectionType.EAC])

        # Add viewport extraction for high-motion content
        if quality.motion_intensity > 0.6:
            recommendations.append(ProjectionType.FLAT)

        return recommendations[:3]  # Limit to top 3

    def _recommend_viewports(self, metadata: SphericalMetadata) -> list[ViewportConfig]:
        """Recommend viewports for thumbnail generation."""
        viewports = []

        # Standard viewing angles
        standard_views = [
            ViewportConfig(yaw=0, pitch=0, fov=90),  # Front
            ViewportConfig(yaw=90, pitch=0, fov=90),  # Right
            ViewportConfig(yaw=180, pitch=0, fov=90),  # Back
            ViewportConfig(yaw=270, pitch=0, fov=90),  # Left
            ViewportConfig(yaw=0, pitch=90, fov=90),  # Up
            ViewportConfig(yaw=0, pitch=-90, fov=90),  # Down
        ]

        viewports.extend(standard_views)

        # Add initial view from metadata
        if metadata.initial_view_heading != 0 or metadata.initial_view_pitch != 0:
            viewports.append(
                ViewportConfig(
                    yaw=metadata.initial_view_heading,
                    pitch=metadata.initial_view_pitch,
                    roll=metadata.initial_view_roll,
                    fov=90,
                )
            )

        return viewports

    async def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds."""
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video_path),
        ]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        return float(result.stdout.strip())
