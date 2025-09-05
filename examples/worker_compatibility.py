#!/usr/bin/env python3
"""
Procrastinate worker compatibility example.

This example demonstrates how to run a Procrastinate worker that works
with both version 2.x and 3.x of Procrastinate.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from video_processor.tasks import setup_procrastinate, get_worker_kwargs
from video_processor.tasks.compat import get_version_info, IS_PROCRASTINATE_3_PLUS
from video_processor.tasks.migration import migrate_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_and_run_worker():
    """Set up and run a Procrastinate worker with version compatibility."""
    
    # Database connection
    database_url = "postgresql://localhost/procrastinate_dev"
    
    try:
        # Print version information
        version_info = get_version_info()
        logger.info(f"Starting worker with Procrastinate {version_info['procrastinate_version']}")
        logger.info(f"Available features: {list(version_info['features'].keys())}")
        
        # Optionally run database migration
        migrate_success = await migrate_database(database_url)
        if not migrate_success:
            logger.error("Database migration failed")
            return
        
        # Set up Procrastinate app
        connector_kwargs = {}
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x connection pool settings
            connector_kwargs.update({
                "pool_size": 20,
                "max_pool_size": 50,
            })
        
        app = setup_procrastinate(database_url, connector_kwargs=connector_kwargs)
        
        # Configure worker options with version compatibility
        worker_options = {
            "concurrency": 4,
            "name": "video-processor-worker",
        }
        
        # Add version-specific options
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x options
            worker_options.update({
                "fetch_job_polling_interval": 5,  # Renamed from "timeout" in 2.x
                "shutdown_graceful_timeout": 30,   # New in 3.x
                "remove_failed": True,             # Renamed from "remove_error"
                "include_failed": False,           # Renamed from "include_error"
            })
        else:
            # Procrastinate 2.x options
            worker_options.update({
                "timeout": 5,
                "remove_error": True,
                "include_error": False,
            })
        
        # Normalize options for the current version
        normalized_options = get_worker_kwargs(**worker_options)
        
        logger.info(f"Worker options: {normalized_options}")
        
        # Create and configure worker
        async with app.open_async() as app_context:
            worker = app_context.create_worker(
                queues=["video_processing", "thumbnail_generation", "sprite_generation"],
                **normalized_options
            )
            
            # Set up signal handlers for graceful shutdown
            if IS_PROCRASTINATE_3_PLUS:
                # Procrastinate 3.x has improved graceful shutdown
                def signal_handler(sig, frame):
                    logger.info(f"Received signal {sig}, shutting down gracefully...")
                    worker.stop()
                
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
            
            logger.info("Starting Procrastinate worker...")
            logger.info("Queues: video_processing, thumbnail_generation, sprite_generation")
            logger.info("Press Ctrl+C to stop")
            
            # Run the worker
            await worker.run_async()
            
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


async def test_task_submission():
    """Test task submission with both Procrastinate versions."""
    
    database_url = "postgresql://localhost/procrastinate_dev" 
    
    try:
        app = setup_procrastinate(database_url)
        
        # Test video processing task
        with Path("test_video.mp4").open("w") as f:
            f.write("")  # Create dummy file for testing
        
        async with app.open_async() as app_context:
            # Submit test task
            job = await app_context.configure_task(
                "process_video_async",
                queue="video_processing"
            ).defer_async(
                input_path="test_video.mp4",
                output_dir="/tmp/test_output",
                config_dict={"quality_preset": "fast"}
            )
            
            logger.info(f"Submitted test job: {job.id}")
            
        # Clean up
        Path("test_video.mp4").unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Task submission test failed: {e}")


def show_migration_help():
    """Show migration help for upgrading from Procrastinate 2.x to 3.x."""
    
    print("\nProcrastinate Migration Guide")
    print("=" * 40)
    
    version_info = get_version_info()
    
    if version_info['is_v3_plus']:
        print("✅ You are running Procrastinate 3.x")
        print("\nMigration steps for 3.x:")
        print("1. Apply pre-migration: python -m video_processor.tasks.migration --pre")
        print("2. Deploy new application code")
        print("3. Apply post-migration: python -m video_processor.tasks.migration --post")
        print("4. Verify: procrastinate schema --check")
    else:
        print("📦 You are running Procrastinate 2.x")
        print("\nTo upgrade to 3.x:")
        print("1. Update dependencies: uv add 'procrastinate>=3.0,<4.0'")
        print("2. Apply pre-migration: python -m video_processor.tasks.migration --pre")
        print("3. Deploy new code")
        print("4. Apply post-migration: python -m video_processor.tasks.migration --post")
    
    print(f"\nCurrent version: {version_info['procrastinate_version']}")
    print(f"Available features: {list(version_info['features'].keys())}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "worker":
            asyncio.run(setup_and_run_worker())
        elif command == "test":
            asyncio.run(test_task_submission())
        elif command == "help":
            show_migration_help()
        else:
            print("Usage: python worker_compatibility.py [worker|test|help]")
    else:
        print("Procrastinate Worker Compatibility Demo")
        print("Usage:")
        print("  python worker_compatibility.py worker  - Run worker")
        print("  python worker_compatibility.py test    - Test task submission")
        print("  python worker_compatibility.py help    - Show migration help")
        
        show_migration_help()