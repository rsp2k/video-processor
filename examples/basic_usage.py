#!/usr/bin/env python3
"""
Basic usage example for the video processor module.

This example demonstrates:
- Creating a processor configuration
- Processing a video file to multiple formats
- Generating thumbnails and sprites
"""

import tempfile
from pathlib import Path

from video_processor import ProcessorConfig, VideoProcessor


def basic_processing_example():
    """Demonstrate basic video processing functionality."""
    
    # Create a temporary directory for outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create configuration
        config = ProcessorConfig(
            base_path=temp_path,
            output_formats=["mp4", "webm"],
            quality_preset="medium",
        )
        
        # Initialize processor
        processor = VideoProcessor(config)
        
        # Example input file (replace with actual video file path)
        input_file = Path("example_input.mp4")
        
        if input_file.exists():
            print(f"Processing video: {input_file}")
            
            # Process the video
            result = processor.process_video(
                input_path=input_file,
                output_dir=temp_path / "outputs"
            )
            
            print(f"Processing complete!")
            print(f"Video ID: {result.video_id}")
            print(f"Formats created: {list(result.encoded_files.keys())}")
            
            # Display output files
            for format_name, file_path in result.encoded_files.items():
                print(f"  {format_name}: {file_path}")
            
            if result.thumbnail_file:
                print(f"Thumbnail: {result.thumbnail_file}")
            
            if result.sprite_files:
                sprite_img, sprite_vtt = result.sprite_files
                print(f"Sprite image: {sprite_img}")
                print(f"Sprite WebVTT: {sprite_vtt}")
        
        else:
            print(f"Input file not found: {input_file}")
            print("Create an example video file or modify the path in this script.")


if __name__ == "__main__":
    basic_processing_example()