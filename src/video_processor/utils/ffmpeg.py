"""FFmpeg utilities and helper functions."""

import subprocess
from pathlib import Path

from ..exceptions import FFmpegError


class FFmpegUtils:
    """Utility functions for FFmpeg operations."""

    @staticmethod
    def check_ffmpeg_available(ffmpeg_path: str = "/usr/bin/ffmpeg") -> bool:
        """
        Check if FFmpeg is available and working.

        Args:
            ffmpeg_path: Path to FFmpeg binary

        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    @staticmethod
    def get_ffmpeg_version(ffmpeg_path: str = "/usr/bin/ffmpeg") -> str | None:
        """
        Get FFmpeg version string.

        Args:
            ffmpeg_path: Path to FFmpeg binary

        Returns:
            Version string or None if not available
        """
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split("\n")[0]
                if "version" in first_line:
                    return first_line.split("version")[1].split()[0]
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            pass
        return None

    @staticmethod
    def validate_input_file(file_path: Path) -> None:
        """
        Validate that input file exists and is readable by FFmpeg.

        Args:
            file_path: Path to input file

        Raises:
            FFmpegError: If file is invalid
        """
        if not file_path.exists():
            raise FFmpegError(f"Input file does not exist: {file_path}")

        if not file_path.is_file():
            raise FFmpegError(f"Input path is not a file: {file_path}")

        # Try to probe the file to ensure it's a valid media file
        try:
            import ffmpeg

            ffmpeg.probe(str(file_path))
        except Exception as e:
            raise FFmpegError(f"Input file is not a valid media file: {e}") from e

    @staticmethod
    def estimate_processing_time(
        input_file: Path, output_formats: list[str], quality_preset: str = "medium"
    ) -> int:
        """
        Estimate processing time in seconds based on input file and settings.

        Args:
            input_file: Path to input file
            output_formats: List of output formats
            quality_preset: Quality preset name

        Returns:
            Estimated processing time in seconds
        """
        try:
            import ffmpeg

            probe = ffmpeg.probe(str(input_file))
            duration = float(probe["format"].get("duration", 0))

            # Base multiplier for encoding (very rough estimate)
            format_multipliers = {
                "mp4": 0.5,  # Two-pass H.264
                "webm": 0.8,  # VP9 is slower
                "ogv": 0.3,  # Theora is faster
            }

            quality_multipliers = {
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5,
                "ultra": 2.0,
            }

            total_multiplier = sum(
                format_multipliers.get(fmt, 1.0) for fmt in output_formats
            )
            quality_multiplier = quality_multipliers.get(quality_preset, 1.0)

            # Base estimate: video duration * encoding complexity
            estimated_time = duration * total_multiplier * quality_multiplier

            # Add buffer time for thumbnails, sprites, etc.
            estimated_time += 30

            return max(int(estimated_time), 60)  # Minimum 1 minute

        except Exception:
            # Fallback estimate
            return 300  # 5 minutes default
