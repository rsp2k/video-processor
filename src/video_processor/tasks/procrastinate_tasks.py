"""Procrastinate background tasks for video processing."""

import logging
from pathlib import Path

from procrastinate import App

from ..config import ProcessorConfig
from ..core.processor import VideoProcessor
from ..exceptions import VideoProcessorError

logger = logging.getLogger(__name__)

# Create Procrastinate app instance
app = App(connector=None)  # Connector will be set during setup


def setup_procrastinate(database_url: str) -> App:
    """
    Set up Procrastinate with database connection.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        Configured Procrastinate app
    """
    from procrastinate import AiopgConnector

    connector = AiopgConnector(conninfo=database_url)
    app.connector = connector

    return app


@app.task(queue="video_processing")
def process_video_async(
    input_path: str,
    output_dir: str | None = None,
    video_id: str | None = None,
    config_dict: dict | None = None,
) -> dict:
    """
    Process video asynchronously.

    Args:
        input_path: Path to input video file
        output_dir: Output directory (optional)
        video_id: Unique video identifier (optional)
        config_dict: Configuration dictionary

    Returns:
        Dictionary with processing results
    """
    logger.info(f"Starting async video processing for {input_path}")

    try:
        # Create config from dict or use defaults
        if config_dict:
            config = ProcessorConfig(**config_dict)
        else:
            config = ProcessorConfig()

        # Create processor and process video
        processor = VideoProcessor(config)
        result = processor.process_video(
            input_path=Path(input_path),
            output_dir=Path(output_dir) if output_dir else None,
            video_id=video_id,
        )

        # Convert result to serializable dictionary
        result_dict = {
            "video_id": result.video_id,
            "input_path": str(result.input_path),
            "output_path": str(result.output_path),
            "encoded_files": {
                fmt: str(path) for fmt, path in result.encoded_files.items()
            },
            "thumbnails": [str(path) for path in result.thumbnails],
            "sprite_file": str(result.sprite_file) if result.sprite_file else None,
            "webvtt_file": str(result.webvtt_file) if result.webvtt_file else None,
            "metadata": result.metadata,
        }

        logger.info(f"Completed async video processing for {input_path}")
        return result_dict

    except Exception as e:
        logger.error(f"Async video processing failed for {input_path}: {e}")
        raise VideoProcessorError(f"Async processing failed: {e}") from e


@app.task(queue="thumbnail_generation")
def generate_thumbnail_async(
    video_path: str,
    output_dir: str,
    timestamp: int,
    video_id: str,
    config_dict: dict | None = None,
) -> str:
    """
    Generate thumbnail asynchronously.

    Args:
        video_path: Path to video file
        output_dir: Output directory
        timestamp: Time in seconds to extract thumbnail
        video_id: Unique video identifier
        config_dict: Configuration dictionary

    Returns:
        Path to generated thumbnail
    """
    logger.info(f"Starting async thumbnail generation for {video_path} at {timestamp}s")

    try:
        # Create config from dict or use defaults
        if config_dict:
            config = ProcessorConfig(**config_dict)
        else:
            config = ProcessorConfig()

        # Create thumbnail generator
        from ..core.thumbnails import ThumbnailGenerator

        generator = ThumbnailGenerator(config)

        # Generate thumbnail
        thumbnail_path = generator.generate_thumbnail(
            video_path=Path(video_path),
            output_dir=Path(output_dir),
            timestamp=timestamp,
            video_id=video_id,
        )

        logger.info(f"Completed async thumbnail generation: {thumbnail_path}")
        return str(thumbnail_path)

    except Exception as e:
        logger.error(f"Async thumbnail generation failed: {e}")
        raise VideoProcessorError(f"Async thumbnail generation failed: {e}") from e


@app.task(queue="sprite_generation")
def generate_sprites_async(
    video_path: str,
    output_dir: str,
    video_id: str,
    config_dict: dict | None = None,
) -> dict[str, str]:
    """
    Generate video sprites asynchronously.

    Args:
        video_path: Path to video file
        output_dir: Output directory
        video_id: Unique video identifier
        config_dict: Configuration dictionary

    Returns:
        Dictionary with sprite and webvtt file paths
    """
    logger.info(f"Starting async sprite generation for {video_path}")

    try:
        # Create config from dict or use defaults
        if config_dict:
            config = ProcessorConfig(**config_dict)
        else:
            config = ProcessorConfig()

        # Create thumbnail generator
        from ..core.thumbnails import ThumbnailGenerator

        generator = ThumbnailGenerator(config)

        # Generate sprites
        sprite_file, webvtt_file = generator.generate_sprites(
            video_path=Path(video_path),
            output_dir=Path(output_dir),
            video_id=video_id,
        )

        result = {
            "sprite_file": str(sprite_file),
            "webvtt_file": str(webvtt_file),
        }

        logger.info(f"Completed async sprite generation: {result}")
        return result

    except Exception as e:
        logger.error(f"Async sprite generation failed: {e}")
        raise VideoProcessorError(f"Async sprite generation failed: {e}") from e
