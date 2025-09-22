"""Custom sprite generator that fixes msprites2 ImageMagick compatibility issues."""

import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class FixedSpriteGenerator:
    """Fixed sprite generator with proper ImageMagick compatibility."""

    def __init__(
        self,
        video_path: str | Path,
        thumbnail_dir: str | Path,
        ips: float = 1.0,
        width: int = 160,
        height: int = 90,
        cols: int = 10,
        rows: int = 10,
    ):
        self.video_path = str(video_path)
        self.thumbnail_dir = str(thumbnail_dir)
        self.ips = ips
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.filename_format = "%04d.jpg"

        # Create thumbnail directory if it doesn't exist
        Path(self.thumbnail_dir).mkdir(parents=True, exist_ok=True)

    def generate_thumbnails(self) -> None:
        """Generate individual thumbnail frames using ffmpeg."""
        output_pattern = os.path.join(self.thumbnail_dir, self.filename_format)

        # Use ffmpeg to extract thumbnails
        cmd = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            self.video_path,
            "-r",
            f"1/{self.ips}",
            "-vf",
            f"scale={self.width}:{self.height}",
            "-y",  # Overwrite existing files
            output_pattern,
        ]

        logger.debug(f"Generating thumbnails with: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    def generate_sprite(self, sprite_file: str | Path) -> Path:
        """Generate sprite sheet using ImageMagick montage."""
        sprite_file = Path(sprite_file)

        # Count available thumbnails
        thumbnail_files = list(Path(self.thumbnail_dir).glob("*.jpg"))
        if not thumbnail_files:
            raise RuntimeError("No thumbnail files found to create sprite")

        # Sort thumbnails by name to ensure correct order
        thumbnail_files.sort()

        # Limit number of thumbnails to avoid command line length issues
        max_thumbnails = min(len(thumbnail_files), 100)  # Limit to 100 thumbnails
        thumbnail_files = thumbnail_files[:max_thumbnails]

        # Build montage command with correct syntax
        cmd = [
            "magick",
            "montage",
            "-background",
            "#336699",
            "-tile",
            f"{self.cols}x{self.rows}",
            "-geometry",
            f"{self.width}x{self.height}+0+0",
        ]

        # Add thumbnail files
        cmd.extend(str(f) for f in thumbnail_files)
        cmd.append(str(sprite_file))

        logger.debug(
            f"Generating sprite with {len(thumbnail_files)} thumbnails: {sprite_file}"
        )
        result = subprocess.run(cmd, check=False)

        if result.returncode != 0:
            raise RuntimeError(
                f"ImageMagick montage failed with return code {result.returncode}"
            )

        return sprite_file

    def generate_webvtt(self, webvtt_file: str | Path, sprite_filename: str) -> Path:
        """Generate WebVTT file for seekbar thumbnails."""
        webvtt_file = Path(webvtt_file)

        # Count thumbnail files to determine timeline
        thumbnail_files = list(Path(self.thumbnail_dir).glob("*.jpg"))
        thumbnail_files.sort()

        content_lines = ["WEBVTT\n\n"]

        for i, _ in enumerate(thumbnail_files):
            start_time = i * self.ips
            end_time = (i + 1) * self.ips

            # Calculate position in sprite grid
            row = i // self.cols
            col = i % self.cols
            x = col * self.width
            y = row * self.height

            # Format timestamps
            start_ts = self._seconds_to_timestamp(start_time)
            end_ts = self._seconds_to_timestamp(end_time)

            content_lines.extend(
                [
                    f"{start_ts} --> {end_ts}\n",
                    f"{sprite_filename}#xywh={x},{y},{self.width},{self.height}\n\n",
                ]
            )

        # Write WebVTT content
        with open(webvtt_file, "w") as f:
            f.writelines(content_lines)

        return webvtt_file

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to WebVTT timestamp format."""
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def cleanup_thumbnails(self) -> None:
        """Remove temporary thumbnail files."""
        try:
            thumbnail_files = list(Path(self.thumbnail_dir).glob("*.jpg"))
            for thumb_file in thumbnail_files:
                thumb_file.unlink()

            # Remove directory if empty
            thumb_dir = Path(self.thumbnail_dir)
            if thumb_dir.exists() and not any(thumb_dir.iterdir()):
                thumb_dir.rmdir()
        except Exception as e:
            logger.warning(f"Failed to cleanup thumbnails: {e}")

    @classmethod
    def create_sprite_sheet(
        cls,
        video_path: str | Path,
        thumbnail_dir: str | Path,
        sprite_file: str | Path,
        webvtt_file: str | Path,
        ips: float = 1.0,
        width: int = 160,
        height: int = 90,
        cols: int = 10,
        rows: int = 10,
        cleanup: bool = True,
    ) -> tuple[Path, Path]:
        """
        Complete sprite sheet generation process.

        Returns:
            Tuple of (sprite_file_path, webvtt_file_path)
        """
        generator = cls(
            video_path=video_path,
            thumbnail_dir=thumbnail_dir,
            ips=ips,
            width=width,
            height=height,
            cols=cols,
            rows=rows,
        )

        # Generate components
        generator.generate_thumbnails()
        sprite_path = generator.generate_sprite(sprite_file)
        webvtt_path = generator.generate_webvtt(webvtt_file, Path(sprite_file).name)

        # Cleanup temporary thumbnails if requested (but not the final sprite/webvtt)
        if cleanup:
            generator.cleanup_thumbnails()

        return sprite_path, webvtt_path
