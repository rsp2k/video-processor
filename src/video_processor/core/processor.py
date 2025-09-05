"""Main video processor class."""

import uuid
from pathlib import Path

from ..config import ProcessorConfig
from ..exceptions import ValidationError, VideoProcessorError
from ..storage.backends import LocalStorageBackend, StorageBackend
from .encoders import VideoEncoder
from .metadata import VideoMetadata
from .thumbnails import ThumbnailGenerator


class VideoProcessingResult:
    """Result of video processing operation."""

    def __init__(
        self,
        video_id: str,
        input_path: Path,
        output_path: Path,
        encoded_files: dict[str, Path],
        thumbnails: list[Path],
        sprite_file: Path | None = None,
        webvtt_file: Path | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.video_id = video_id
        self.input_path = input_path
        self.output_path = output_path
        self.encoded_files = encoded_files
        self.thumbnails = thumbnails
        self.sprite_file = sprite_file
        self.webvtt_file = webvtt_file
        self.metadata = metadata


class VideoProcessor:
    """Main video processing class."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config
        self.storage = self._create_storage_backend()
        self.encoder = VideoEncoder(config)
        self.thumbnail_generator = ThumbnailGenerator(config)
        self.metadata_extractor = VideoMetadata(config)

    def _create_storage_backend(self) -> StorageBackend:
        """Create storage backend based on configuration."""
        if self.config.storage_backend == "local":
            return LocalStorageBackend(self.config)
        elif self.config.storage_backend == "s3":
            # TODO: Implement S3StorageBackend
            raise NotImplementedError("S3 storage backend not implemented yet")
        else:
            raise ValidationError(
                f"Unknown storage backend: {self.config.storage_backend}"
            )

    def process_video(
        self,
        input_path: Path | str,
        output_dir: Path | str | None = None,
        video_id: str | None = None,
    ) -> VideoProcessingResult:
        """
        Process a video file with encoding, thumbnails, and sprites.

        Args:
            input_path: Path to input video file
            output_dir: Output directory (defaults to config base_path)
            video_id: Unique identifier for video (auto-generated if None)

        Returns:
            VideoProcessingResult with all generated files
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise ValidationError(f"Input file does not exist: {input_path}")

        # Generate unique video ID if not provided
        if video_id is None:
            video_id = str(uuid.uuid4())[:8]

        # Set up output directory
        if output_dir is None:
            output_dir = self.config.base_path / video_id
        else:
            output_dir = Path(output_dir) / video_id

        # Create output directory
        self.storage.create_directory(output_dir)

        try:
            # Extract metadata first
            metadata = self.metadata_extractor.extract_metadata(input_path)

            # Encode video in requested formats
            encoded_files = {}
            for format_name in self.config.output_formats:
                encoded_file = self.encoder.encode_video(
                    input_path, output_dir, format_name, video_id
                )
                encoded_files[format_name] = encoded_file

            # Generate thumbnails
            thumbnails = []
            for timestamp in self.config.thumbnail_timestamps:
                thumbnail = self.thumbnail_generator.generate_thumbnail(
                    encoded_files.get("mp4", input_path),
                    output_dir,
                    timestamp,
                    video_id,
                )
                thumbnails.append(thumbnail)

            # Generate sprites if enabled
            sprite_file = None
            webvtt_file = None
            if self.config.generate_sprites and "mp4" in encoded_files:
                sprite_file, webvtt_file = self.thumbnail_generator.generate_sprites(
                    encoded_files["mp4"], output_dir, video_id
                )

            return VideoProcessingResult(
                video_id=video_id,
                input_path=input_path,
                output_path=output_dir,
                encoded_files=encoded_files,
                thumbnails=thumbnails,
                sprite_file=sprite_file,
                webvtt_file=webvtt_file,
                metadata=metadata,
            )

        except Exception as e:
            # Clean up on failure
            if output_dir.exists():
                self.storage.cleanup_directory(output_dir)
            raise VideoProcessorError(f"Video processing failed: {e}") from e
