"""Projection conversion utilities for 360° videos."""

import asyncio
import logging
import subprocess
import time
from pathlib import Path

from ..exceptions import VideoProcessorError
from .models import ProjectionType, Video360ProcessingResult

logger = logging.getLogger(__name__)


class ProjectionConverter:
    """
    Handles conversion between different 360° video projections.

    Supports conversion between:
    - Equirectangular
    - Cubemap (various layouts)
    - Equi-Angular Cubemap (EAC)
    - Fisheye
    - Stereographic (Little Planet)
    - Flat (viewport extraction)
    """

    def __init__(self):
        # Mapping of projection types to FFmpeg v360 format codes
        self.projection_formats = {
            ProjectionType.EQUIRECTANGULAR: "e",
            ProjectionType.CUBEMAP: "c3x2",
            ProjectionType.EAC: "eac",
            ProjectionType.FISHEYE: "fisheye",
            ProjectionType.DUAL_FISHEYE: "dfisheye",
            ProjectionType.CYLINDRICAL: "cylindrical",
            ProjectionType.STEREOGRAPHIC: "sg",
            ProjectionType.PANNINI: "pannini",
            ProjectionType.MERCATOR: "mercator",
            ProjectionType.LITTLE_PLANET: "sg",  # Same as stereographic
            ProjectionType.FLAT: "flat",
            ProjectionType.HALF_EQUIRECTANGULAR: "hequirect",
        }

        # Quality presets for different conversion scenarios
        self.quality_presets = {
            "fast": {"preset": "fast", "crf": "26"},
            "balanced": {"preset": "medium", "crf": "23"},
            "quality": {"preset": "slow", "crf": "20"},
            "archive": {"preset": "veryslow", "crf": "18"},
        }

    async def convert_projection(
        self,
        input_path: Path,
        output_path: Path,
        source_projection: ProjectionType,
        target_projection: ProjectionType,
        output_resolution: tuple[int, int] | None = None,
        quality_preset: str = "balanced",
        preserve_metadata: bool = True,
    ) -> Video360ProcessingResult:
        """
        Convert between 360° projections.

        Args:
            input_path: Source video path
            output_path: Output video path
            source_projection: Source projection type
            target_projection: Target projection type
            output_resolution: Optional (width, height) for output
            quality_preset: Encoding quality preset
            preserve_metadata: Whether to preserve spherical metadata

        Returns:
            Video360ProcessingResult with conversion details
        """
        start_time = time.time()
        result = Video360ProcessingResult(
            operation=f"projection_conversion_{source_projection.value}_to_{target_projection.value}"
        )

        try:
            # Validate projections are supported
            if source_projection not in self.projection_formats:
                raise VideoProcessorError(
                    f"Unsupported source projection: {source_projection}"
                )

            if target_projection not in self.projection_formats:
                raise VideoProcessorError(
                    f"Unsupported target projection: {target_projection}"
                )

            # Get format codes
            source_format = self.projection_formats[source_projection]
            target_format = self.projection_formats[target_projection]

            # Build v360 filter
            v360_filter = self._build_v360_filter(
                source_format,
                target_format,
                output_resolution,
                source_projection,
                target_projection,
            )

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build FFmpeg command
            cmd = self._build_conversion_command(
                input_path,
                output_path,
                v360_filter,
                quality_preset,
                preserve_metadata,
                target_projection,
            )

            # Execute conversion
            logger.info(
                f"Converting {source_projection.value} -> {target_projection.value}"
            )
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                logger.info(f"Projection conversion successful: {output_path}")

            else:
                result.add_error(f"FFmpeg conversion failed: {process_result.stderr}")
                logger.error(f"Conversion failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Conversion error: {e}")
            logger.error(f"Projection conversion error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_v360_filter(
        self,
        source_format: str,
        target_format: str,
        output_resolution: tuple[int, int] | None,
        source_projection: ProjectionType,
        target_projection: ProjectionType,
    ) -> str:
        """Build FFmpeg v360 filter string."""

        filter_parts = [f"v360={source_format}:{target_format}"]

        # Add resolution if specified
        if output_resolution:
            filter_parts.append(f"w={output_resolution[0]}:h={output_resolution[1]}")

        # Add projection-specific parameters
        if target_projection == ProjectionType.STEREOGRAPHIC:
            # Little planet effect parameters
            filter_parts.extend(
                [
                    "pitch=-90",  # Look down for little planet
                    "h_fov=360",
                    "v_fov=180",
                ]
            )

        elif target_projection == ProjectionType.FISHEYE:
            # Fisheye parameters
            filter_parts.extend(["h_fov=190", "v_fov=190"])

        elif target_projection == ProjectionType.PANNINI:
            # Pannini projection parameters
            filter_parts.extend(["h_fov=120", "v_fov=90"])

        elif source_projection == ProjectionType.DUAL_FISHEYE:
            # Dual fisheye specific handling
            filter_parts.extend(
                [
                    "ih_flip=1",  # Input horizontal flip
                    "iv_flip=1",  # Input vertical flip
                ]
            )

        return ":".join(filter_parts)

    def _build_conversion_command(
        self,
        input_path: Path,
        output_path: Path,
        v360_filter: str,
        quality_preset: str,
        preserve_metadata: bool,
        target_projection: ProjectionType,
    ) -> list[str]:
        """Build complete FFmpeg command."""

        # Get quality settings
        quality_settings = self.quality_presets.get(
            quality_preset, self.quality_presets["balanced"]
        )

        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vf",
            v360_filter,
            "-c:v",
            "libx264",
            "-preset",
            quality_settings["preset"],
            "-crf",
            quality_settings["crf"],
            "-c:a",
            "copy",  # Copy audio unchanged
            "-movflags",
            "+faststart",  # Web-friendly
        ]

        # Add metadata preservation
        if preserve_metadata and target_projection != ProjectionType.FLAT:
            cmd.extend(
                [
                    "-metadata",
                    "spherical=1",
                    "-metadata",
                    f"projection={target_projection.value}",
                    "-metadata",
                    "stitched=1",
                ]
            )

        cmd.extend([str(output_path), "-y"])

        return cmd

    async def batch_convert_projections(
        self,
        input_path: Path,
        output_dir: Path,
        target_projections: list[ProjectionType],
        source_projection: ProjectionType = ProjectionType.EQUIRECTANGULAR,
        base_filename: str = None,
        parallel: bool = True,
    ) -> list[Video360ProcessingResult]:
        """
        Convert single video to multiple projections.

        Args:
            input_path: Source video
            output_dir: Output directory
            source_projection: Source projection type
            target_projections: List of target projections
            base_filename: Base name for output files

        Returns:
            Dictionary of projection type to conversion result
        """
        if base_filename is None:
            base_filename = input_path.stem

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []

        # Process conversions
        for target_projection in target_projections:
            if target_projection == source_projection:
                continue  # Skip same projection

            output_filename = f"{base_filename}_{target_projection.value}.mp4"
            output_path = output_dir / output_filename

            try:
                result = await self.convert_projection(
                    input_path, output_path, source_projection, target_projection
                )
                results.append(result)

                if result.success:
                    logger.info(
                        f"Batch conversion successful: {target_projection.value}"
                    )
                else:
                    logger.error(f"Batch conversion failed: {target_projection.value}")

            except Exception as e:
                logger.error(
                    f"Batch conversion error for {target_projection.value}: {e}"
                )
                error_result = Video360ProcessingResult(
                    operation=f"batch_convert_{target_projection.value}", success=False
                )
                error_result.add_error(str(e))
                results.append(error_result)

        return results

    async def create_cubemap_layouts(
        self,
        input_path: Path,
        output_dir: Path,
        source_projection: ProjectionType = ProjectionType.EQUIRECTANGULAR,
    ) -> dict[str, Video360ProcessingResult]:
        """
        Create different cubemap layouts from source video.

        Args:
            input_path: Source video (typically equirectangular)
            output_dir: Output directory
            source_projection: Source projection type

        Returns:
            Dictionary of layout name to conversion result
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Different cubemap layouts
        layouts = {
            "3x2": "c3x2",  # YouTube standard
            "6x1": "c6x1",  # Horizontal strip
            "1x6": "c1x6",  # Vertical strip
            "2x3": "c2x3",  # Alternative layout
        }

        results = {}
        base_filename = input_path.stem

        for layout_name, format_code in layouts.items():
            output_filename = f"{base_filename}_cubemap_{layout_name}.mp4"
            output_path = output_dir / output_filename

            # Build custom v360 filter for this layout
            v360_filter = (
                f"v360={self.projection_formats[source_projection]}:{format_code}"
            )

            # Build command
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
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=cubemap",
                "-metadata",
                f"cubemap_layout={layout_name}",
                str(output_path),
                "-y",
            ]

            try:
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True
                )

                processing_result = Video360ProcessingResult(
                    operation=f"cubemap_layout_{layout_name}"
                )

                if result.returncode == 0:
                    processing_result.success = True
                    processing_result.output_path = output_path
                    logger.info(f"Created cubemap layout: {layout_name}")
                else:
                    processing_result.add_error(f"FFmpeg failed: {result.stderr}")

                results[layout_name] = processing_result

            except Exception as e:
                logger.error(f"Cubemap layout creation failed for {layout_name}: {e}")
                results[layout_name] = Video360ProcessingResult(
                    operation=f"cubemap_layout_{layout_name}", success=False
                )
                results[layout_name].add_error(str(e))

        return results

    async def create_projection_preview_grid(
        self,
        input_path: Path,
        output_path: Path,
        source_projection: ProjectionType = ProjectionType.EQUIRECTANGULAR,
        grid_size: tuple[int, int] = (2, 3),
    ) -> Video360ProcessingResult:
        """
        Create a preview grid showing different projections.

        Args:
            input_path: Source video
            output_path: Output preview video
            source_projection: Source projection type
            grid_size: Grid dimensions (cols, rows)

        Returns:
            Video360ProcessingResult with preview creation details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="projection_preview_grid")

        try:
            # Define projections to show in grid
            preview_projections = [
                ProjectionType.EQUIRECTANGULAR,
                ProjectionType.CUBEMAP,
                ProjectionType.STEREOGRAPHIC,
                ProjectionType.FISHEYE,
                ProjectionType.PANNINI,
                ProjectionType.MERCATOR,
            ]

            cols, rows = grid_size
            max_projections = cols * rows
            preview_projections = preview_projections[:max_projections]

            # Create temporary files for each projection
            temp_dir = output_path.parent / "temp_projections"
            temp_dir.mkdir(exist_ok=True)

            temp_files = []

            # Convert to each projection
            for i, proj in enumerate(preview_projections):
                temp_file = temp_dir / f"proj_{i}_{proj.value}.mp4"

                if proj == source_projection:
                    # Copy original
                    import shutil

                    shutil.copy2(input_path, temp_file)
                else:
                    # Convert projection
                    conversion_result = await self.convert_projection(
                        input_path, temp_file, source_projection, proj
                    )

                    if not conversion_result.success:
                        logger.warning(f"Failed to convert to {proj.value} for preview")
                        continue

                temp_files.append(temp_file)

            # Create grid layout using FFmpeg
            if len(temp_files) >= 4:  # Minimum for 2x2 grid
                filter_complex = self._build_grid_filter(temp_files, cols, rows)

                cmd = ["ffmpeg"]

                # Add all input files
                for temp_file in temp_files:
                    cmd.extend(["-i", str(temp_file)])

                cmd.extend(
                    [
                        "-filter_complex",
                        filter_complex,
                        "-c:v",
                        "libx264",
                        "-preset",
                        "medium",
                        "-crf",
                        "25",
                        "-t",
                        "10",  # Limit to 10 seconds for preview
                        str(output_path),
                        "-y",
                    ]
                )

                process_result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True
                )

                if process_result.returncode == 0:
                    result.success = True
                    result.output_path = output_path
                    logger.info("Projection preview grid created successfully")
                else:
                    result.add_error(f"Grid creation failed: {process_result.stderr}")
            else:
                result.add_error("Insufficient projections for grid")

            # Cleanup temp files
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            result.add_error(f"Preview grid creation error: {e}")
            logger.error(f"Preview grid error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_grid_filter(self, input_files: list[Path], cols: int, rows: int) -> str:
        """Build FFmpeg filter for grid layout."""
        # Simple 2x2 grid filter (can be extended for other sizes)
        if cols == 2 and rows == 2 and len(input_files) >= 4:
            return (
                "[0:v]scale=iw/2:ih/2[v0];"
                "[1:v]scale=iw/2:ih/2[v1];"
                "[2:v]scale=iw/2:ih/2[v2];"
                "[3:v]scale=iw/2:ih/2[v3];"
                "[v0][v1]hstack[top];"
                "[v2][v3]hstack[bottom];"
                "[top][bottom]vstack[out]"
            )
        elif cols == 3 and rows == 2 and len(input_files) >= 6:
            return (
                "[0:v]scale=iw/3:ih/2[v0];"
                "[1:v]scale=iw/3:ih/2[v1];"
                "[2:v]scale=iw/3:ih/2[v2];"
                "[3:v]scale=iw/3:ih/2[v3];"
                "[4:v]scale=iw/3:ih/2[v4];"
                "[5:v]scale=iw/3:ih/2[v5];"
                "[v0][v1][v2]hstack=inputs=3[top];"
                "[v3][v4][v5]hstack=inputs=3[bottom];"
                "[top][bottom]vstack[out]"
            )
        else:
            # Fallback to simple 2x2
            return (
                "[0:v]scale=iw/2:ih/2[v0];[1:v]scale=iw/2:ih/2[v1];[v0][v1]hstack[out]"
            )

    def get_supported_projections(self) -> list[ProjectionType]:
        """Get list of supported projection types."""
        return list(self.projection_formats.keys())

    def get_conversion_matrix(self) -> dict[ProjectionType, list[ProjectionType]]:
        """Get matrix of supported conversions."""
        conversions = {}

        # Most projections can convert to most others
        all_projections = self.get_supported_projections()

        for source in all_projections:
            conversions[source] = [
                target for target in all_projections if target != source
            ]

        return conversions

    def estimate_conversion_time(
        self,
        source_projection: ProjectionType,
        target_projection: ProjectionType,
        input_resolution: tuple[int, int],
        duration_seconds: float,
    ) -> float:
        """
        Estimate conversion time in seconds.

        Args:
            source_projection: Source projection
            target_projection: Target projection
            input_resolution: Input video resolution
            duration_seconds: Input video duration

        Returns:
            Estimated processing time in seconds
        """
        # Base processing rate (pixels per second, rough estimate)
        base_rate = 2000000  # 2M pixels per second

        # Complexity multipliers
        complexity_multipliers = {
            (ProjectionType.EQUIRECTANGULAR, ProjectionType.CUBEMAP): 1.2,
            (ProjectionType.EQUIRECTANGULAR, ProjectionType.STEREOGRAPHIC): 1.5,
            (ProjectionType.CUBEMAP, ProjectionType.EQUIRECTANGULAR): 1.1,
            (ProjectionType.FISHEYE, ProjectionType.EQUIRECTANGULAR): 1.8,
        }

        # Calculate total pixels to process
        width, height = input_resolution
        total_pixels = width * height * duration_seconds * 30  # Assume 30fps

        # Get complexity multiplier
        conversion_pair = (source_projection, target_projection)
        multiplier = complexity_multipliers.get(conversion_pair, 1.0)

        # Estimate time
        estimated_time = (total_pixels / base_rate) * multiplier

        # Add overhead (20%)
        estimated_time *= 1.2

        return max(estimated_time, 1.0)  # Minimum 1 second
