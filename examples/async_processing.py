#!/usr/bin/env python3
"""
Asynchronous video processing example using Procrastinate tasks.

This example demonstrates:
- Setting up Procrastinate for background processing
- Submitting video processing tasks
- Monitoring task status
"""

import asyncio
import tempfile
from pathlib import Path

import procrastinate
from video_processor import ProcessorConfig
from video_processor.tasks import setup_procrastinate, get_worker_kwargs
from video_processor.tasks.compat import get_version_info, IS_PROCRASTINATE_3_PLUS


async def async_processing_example():
    """Demonstrate asynchronous video processing with Procrastinate."""
    
    # Database connection string (adjust for your setup)
    # For testing, you might use: "postgresql://user:password@localhost/dbname"
    database_url = "postgresql://localhost/procrastinate_test"
    
    try:
        # Print version information
        version_info = get_version_info()
        print(f"Using Procrastinate {version_info['procrastinate_version']}")
        print(f"Version 3.x+: {version_info['is_v3_plus']}")
        
        # Set up Procrastinate with version-appropriate settings
        connector_kwargs = {}
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x specific settings
            connector_kwargs["pool_size"] = 10
            
        app = setup_procrastinate(database_url, connector_kwargs=connector_kwargs)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config dictionary for serialization
            config_dict = {
                "base_path": str(temp_path),
                "output_formats": ["mp4", "webm"],
                "quality_preset": "medium",
            }
            
            # Example input file
            input_file = Path("example_input.mp4")
            
            if input_file.exists():
                print(f"Submitting async processing job for: {input_file}")
                
                # Submit video processing task
                job = await app.tasks.process_video_async.defer_async(
                    input_path=str(input_file),
                    output_dir=str(temp_path / "outputs"),
                    config_dict=config_dict
                )
                
                print(f"Job submitted with ID: {job.id}")
                print("Processing in background...")
                
                # In a real application, you would monitor the job status
                # and handle results when the task completes
                
            else:
                print(f"Input file not found: {input_file}")
                print("Create an example video file or modify the path.")
                
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Make sure PostgreSQL is running and the database exists.")


async def thumbnail_generation_example():
    """Demonstrate standalone thumbnail generation."""
    
    database_url = "postgresql://localhost/procrastinate_test"
    
    try:
        app = setup_procrastinate(database_url)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            input_file = Path("example_input.mp4")
            
            if input_file.exists():
                print("Submitting thumbnail generation job...")
                
                job = await app.tasks.generate_thumbnail_async.defer_async(
                    video_path=str(input_file),
                    output_dir=str(temp_path),
                    timestamp=30,  # 30 seconds into the video
                    video_id="example_thumb"
                )
                
                print(f"Thumbnail job submitted: {job.id}")
                
            else:
                print("Input file not found for thumbnail generation.")
                
    except Exception as e:
        print(f"Database connection failed: {e}")


if __name__ == "__main__":
    print("=== Async Video Processing Example ===")
    asyncio.run(async_processing_example())
    
    print("\n=== Thumbnail Generation Example ===")
    asyncio.run(thumbnail_generation_example())