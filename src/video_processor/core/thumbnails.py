"""Thumbnail and sprite generation using FFmpeg and msprites2."""

from pathlib import Path

import ffmpeg

from ..config import ProcessorConfig
from ..exceptions import EncodingError, FFmpegError
from ..utils.sprite_generator import FixedSpriteGenerator


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
            raise EncodingError("Thumbnail generation failed - output file not created")

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

        try:
            # Use our fixed sprite generator
            sprite_path, webvtt_path = FixedSpriteGenerator.create_sprite_sheet(
                video_path=video_path,
                thumbnail_dir=thumbnail_dir,
                sprite_file=sprite_file,
                webvtt_file=webvtt_file,
                ips=1.0 / self.config.sprite_interval,
                width=160,
                height=90,
                cols=10,
                rows=10,
                cleanup=True,
            )

        except Exception as e:
            raise EncodingError(f"Sprite generation failed: {e}") from e

        if not sprite_path.exists():
            raise EncodingError("Sprite generation failed - sprite file not created")

        if not webvtt_path.exists():
            raise EncodingError("Sprite generation failed - WebVTT file not created")

        return sprite_path, webvtt_path
