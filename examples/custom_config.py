#!/usr/bin/env python3
"""
Custom configuration examples for the video processor.

This example demonstrates:
- Creating custom quality presets
- Configuring different output formats
- Using custom FFmpeg paths
- Storage backend configuration
"""

import tempfile
from pathlib import Path

from video_processor import ProcessorConfig, VideoProcessor


def high_quality_processing():
    """Example of high-quality video processing configuration."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # High-quality configuration
        config = ProcessorConfig(
            base_path=temp_path,
            output_formats=["mp4", "webm", "ogv"],  # All formats
            quality_preset="ultra",  # Highest quality
            sprite_interval=5.0,  # Sprite every 5 seconds
            thumbnail_timestamp=10,  # Thumbnail at 10 seconds
            # ffmpeg_path="/usr/local/bin/ffmpeg",  # Custom FFmpeg path if needed
        )
        
        processor = VideoProcessor(config)
        
        print("High-quality processor configured:")
        print(f"  Quality preset: {config.quality_preset}")
        print(f"  Output formats: {config.output_formats}")
        print(f"  Sprite interval: {config.sprite_interval}s")
        print(f"  FFmpeg path: {config.ffmpeg_path}")


def mobile_optimized_processing():
    """Example of mobile-optimized processing configuration."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Mobile-optimized configuration
        config = ProcessorConfig(
            base_path=temp_path,
            output_formats=["mp4"],  # Just MP4 for mobile compatibility
            quality_preset="low",  # Lower bitrate for mobile
            sprite_interval=10.0,  # Fewer sprites to save bandwidth
        )
        
        processor = VideoProcessor(config)
        
        print("\nMobile-optimized processor configured:")
        print(f"  Quality preset: {config.quality_preset}")
        print(f"  Output formats: {config.output_formats}")
        print(f"  Sprite interval: {config.sprite_interval}s")


def custom_paths_and_storage():
    """Example of custom paths and storage configuration."""
    
    # Custom base path
    custom_base = Path("/tmp/video_processing")
    custom_base.mkdir(exist_ok=True)
    
    config = ProcessorConfig(
        base_path=custom_base,
        storage_backend="local",  # Could be "s3" in the future
        output_formats=["mp4", "webm"],
        quality_preset="medium",
    )
    
    # The processor will use the custom paths
    processor = VideoProcessor(config)
    
    print(f"\nCustom paths processor:")
    print(f"  Base path: {config.base_path}")
    print(f"  Storage backend: {config.storage_backend}")
    
    # Clean up
    if custom_base.exists():
        try:
            custom_base.rmdir()
        except OSError:
            pass  # Directory not empty


def validate_config_examples():
    """Demonstrate configuration validation."""
    
    print(f"\nConfiguration validation examples:")
    
    try:
        # This should work fine
        config = ProcessorConfig(
            base_path=Path("/tmp"),
            quality_preset="medium"
        )
        print("✓ Valid configuration created")
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
    
    try:
        # This should fail due to invalid quality preset
        config = ProcessorConfig(
            base_path=Path("/tmp"),
            quality_preset="invalid_preset"  # This will cause validation error
        )
        print("✓ This shouldn't print - validation should fail")
        
    except Exception as e:
        print(f"✓ Expected validation error: {e}")


if __name__ == "__main__":
    print("=== Video Processor Configuration Examples ===")
    
    high_quality_processing()
    mobile_optimized_processing() 
    custom_paths_and_storage()
    validate_config_examples()