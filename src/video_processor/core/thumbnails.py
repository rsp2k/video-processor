"""Thumbnail and sprite generation using FFmpeg and msprites2."""

from pathlib import Path

import ffmpeg
from msprites2 import MontageSprites

from ..config import ProcessorConfig
from ..exceptions import EncodingError, FFmpegError


class ThumbnailGenerator:
    """Handles thumbnail and sprite generation."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

    def generate_thumbnail(
        self,
        video_path: Path,
        output_dir: Path,
        timestamp: int,
        video_id: str,
    ) -> Path:
        """
        Generate a thumbnail image from video at specified timestamp.

        Args:
            video_path: Path to video file
            output_dir: Output directory
            timestamp: Time in seconds to extract thumbnail
            video_id: Unique video identifier

        Returns:
            Path to generated thumbnail
        """
        output_file = output_dir / f"{video_id}_thumb_{timestamp}.png"

        try:
            # Get video info to determine width and duration
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(
                (
                    stream
                    for stream in probe["streams"]
                    if stream["codec_type"] == "video"
                ),
                None,
            )

            if not video_stream:
                raise FFmpegError("No video stream found in input file")

            width = video_stream["width"]
            duration = float(video_stream.get("duration", 0))

            # Adjust timestamp if beyond video duration
            if timestamp >= duration:
                timestamp = max(1, int(duration // 2))

            # Generate thumbnail using ffmpeg-python
            (
                ffmpeg.input(str(video_path), ss=timestamp)
                .filter("scale", width, -1)
                .output(str(output_file), vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            raise FFmpegError(f"Thumbnail generation failed: {error_msg}") from e

        if not output_file.exists():
            raise EncodingError(
                "Thumbnail generation failed - output file not created"
            )

        return output_file

    def generate_sprites(
        self,
        video_path: Path,
        output_dir: Path,
        video_id: str,
    ) -> tuple[Path, Path]:
        """
        Generate sprite sheet and WebVTT file for seekbar thumbnails.

        Args:
            video_path: Path to video file
            output_dir: Output directory
            video_id: Unique video identifier

        Returns:
            Tuple of (sprite_file_path, webvtt_file_path)
        """
        sprite_file = output_dir / f"{video_id}_sprite.jpg"
        webvtt_file = output_dir / f"{video_id}_sprite.webvtt"
        thumbnail_dir = output_dir / "frames"

        # Create frames directory
        thumbnail_dir.mkdir(exist_ok=True)

        try:
            # Generate sprites using msprites2 (the forked library)
            MontageSprites.from_media(
                video_path=str(video_path),
                thumbnail_dir=str(thumbnail_dir),
                sprite_file=str(sprite_file),
                webvtt_file=str(webvtt_file),
                # Optional parameters - can be made configurable
                interval=self.config.sprite_interval,
                width=160,  # Individual thumbnail width
                height=90,  # Individual thumbnail height
                columns=10,  # Thumbnails per row in sprite
            )

        except Exception as e:
            raise EncodingError(f"Sprite generation failed: {e}") from e

        if not sprite_file.exists():
            raise EncodingError("Sprite generation failed - sprite file not created")

        if not webvtt_file.exists():
            raise EncodingError("Sprite generation failed - WebVTT file not created")

        # Clean up temporary frames directory
        self._cleanup_frames_directory(thumbnail_dir)

        return sprite_file, webvtt_file

    def _cleanup_frames_directory(self, frames_dir: Path) -> None:
        """Clean up temporary frame files."""
        try:
            if frames_dir.exists():
                for frame_file in frames_dir.iterdir():
                    if frame_file.is_file():
                        frame_file.unlink()
                frames_dir.rmdir()
        except Exception:
            # Don't fail the entire process if cleanup fails
            pass
