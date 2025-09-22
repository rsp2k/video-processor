#!/usr/bin/env python3
"""
Docker Demo Application for Video Processor

This demo shows how to use the video processor in a containerized environment
with Procrastinate background tasks and PostgreSQL.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from video_processor import ProcessorConfig, VideoProcessor
from video_processor.tasks import setup_procrastinate
from video_processor.tasks.compat import get_version_info
from video_processor.tasks.migration import migrate_database

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_sample_video(output_path: Path) -> Path:
    """Create a sample video using ffmpeg for testing."""
    video_file = output_path / "sample_test_video.mp4"

    # Create a simple test video using ffmpeg
    import subprocess

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=10:size=640x480:rate=30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        str(video_file),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise RuntimeError("Failed to create sample video")

        logger.info(f"Created sample video: {video_file}")
        return video_file

    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg.")
        raise


async def demo_sync_processing():
    """Demonstrate synchronous video processing."""
    logger.info("🎬 Starting Synchronous Processing Demo")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create sample video
        sample_video = await create_sample_video(temp_path)

        # Configure processor
        config = ProcessorConfig(
            output_dir=temp_path / "outputs",
            output_formats=["mp4", "webm"],
            quality_preset="fast",
            generate_thumbnails=True,
            generate_sprites=True,
            enable_360_processing=True,  # Will be disabled if deps not available
        )

        # Process video
        processor = VideoProcessor(config)
        result = processor.process_video(sample_video)

        logger.info("✅ Synchronous processing completed!")
        logger.info(f"📹 Processed video ID: {result.video_id}")
        logger.info(f"📁 Output files: {len(result.encoded_files)} formats")
        logger.info(f"🖼️  Thumbnails: {len(result.thumbnails)}")

        if result.sprite_file:
            sprite_size = result.sprite_file.stat().st_size // 1024
            logger.info(f"🎯 Sprite sheet: {sprite_size}KB")

        if hasattr(result, "thumbnails_360") and result.thumbnails_360:
            logger.info(f"🌐 360° thumbnails: {len(result.thumbnails_360)}")


async def demo_async_processing():
    """Demonstrate asynchronous video processing with Procrastinate."""
    logger.info("⚡ Starting Asynchronous Processing Demo")

    # Get database URL from environment
    database_url = os.environ.get(
        "PROCRASTINATE_DATABASE_URL",
        "postgresql://video_user:video_password@postgres:5432/video_processor",
    )

    try:
        # Show version info
        version_info = get_version_info()
        logger.info(f"📦 Using Procrastinate {version_info['procrastinate_version']}")

        # Run migrations
        logger.info("🔄 Running database migrations...")
        migration_success = await migrate_database(database_url)

        if not migration_success:
            logger.error("❌ Database migration failed")
            return

        logger.info("✅ Database migrations completed")

        # Set up Procrastinate
        app = setup_procrastinate(database_url)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample video
            sample_video = await create_sample_video(temp_path)

            # Configure processing
            config_dict = {
                "base_path": str(temp_path),
                "output_formats": ["mp4"],
                "quality_preset": "fast",
                "generate_thumbnails": True,
                "sprite_interval": 5,
            }

            async with app.open_async() as app_context:
                # Submit video processing task
                logger.info("📤 Submitting async video processing job...")

                job = await app_context.configure_task(
                    "process_video_async", queue="video_processing"
                ).defer_async(
                    input_path=str(sample_video),
                    output_dir=str(temp_path / "async_outputs"),
                    config_dict=config_dict,
                )

                logger.info(f"✅ Job submitted with ID: {job.id}")
                logger.info("🔄 Job will be processed by background worker...")

                # In a real app, you would monitor job status or use webhooks
                # For demo purposes, we'll just show the job was submitted

                # Submit additional tasks
                logger.info("📤 Submitting thumbnail generation job...")

                thumb_job = await app_context.configure_task(
                    "generate_thumbnail_async", queue="thumbnail_generation"
                ).defer_async(
                    video_path=str(sample_video),
                    output_dir=str(temp_path / "thumbnails"),
                    timestamp=5,
                    video_id="demo_thumb",
                )

                logger.info(f"✅ Thumbnail job submitted: {thumb_job.id}")

    except Exception as e:
        logger.error(f"❌ Async processing demo failed: {e}")
        raise


async def demo_migration_features():
    """Demonstrate migration utilities."""
    logger.info("🔄 Migration Features Demo")

    from video_processor.tasks.migration import ProcrastinateMigrationHelper

    database_url = os.environ.get(
        "PROCRASTINATE_DATABASE_URL",
        "postgresql://video_user:video_password@postgres:5432/video_processor",
    )

    # Show migration plan
    helper = ProcrastinateMigrationHelper(database_url)
    helper.print_migration_plan()

    # Show version-specific features
    version_info = get_version_info()
    logger.info("🆕 Available Features:")
    for feature, available in version_info["features"].items():
        status = "✅" if available else "❌"
        logger.info(f"  {status} {feature}")


async def main():
    """Run all demo scenarios."""
    logger.info("🚀 Video Processor Docker Demo Starting...")

    try:
        # Run demos in sequence
        await demo_sync_processing()
        await demo_async_processing()
        await demo_migration_features()

        logger.info("🎉 All demos completed successfully!")

        # Keep the container running to show logs
        logger.info(
            "📋 Demo completed. Container will keep running for log inspection..."
        )
        logger.info("💡 Check the logs with: docker-compose logs app")
        logger.info("🛑 Stop with: docker-compose down")

        # Keep running for log inspection
        while True:
            await asyncio.sleep(30)
            logger.info("💓 Demo container heartbeat - still running...")

    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
