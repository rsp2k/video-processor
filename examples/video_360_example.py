#!/usr/bin/env python3
"""
360° Video Processing Example

This example demonstrates how to use the video processor with 360° video features.

Prerequisites:
- Install with 360° support: uv add "video-processor[video-360-full]"
- Have a 360° video file to process

Features demonstrated:
- Automatic 360° video detection
- 360° thumbnail generation with multiple viewing angles
- 360° sprite sheet creation
- Configuration options for 360° processing
"""

from pathlib import Path

from video_processor import HAS_360_SUPPORT, ProcessorConfig, VideoProcessor


def check_360_dependencies():
    """Check if 360° dependencies are available."""
    print("=== 360° Video Processing Dependencies ===")
    print(f"360° Support Available: {HAS_360_SUPPORT}")

    if not HAS_360_SUPPORT:
        try:
            from video_processor import Video360Utils

            missing = Video360Utils.get_missing_dependencies()
            print(f"Missing dependencies: {missing}")
            print("\nTo install 360° support:")
            print("  uv add 'video-processor[video-360-full]'")
            print("  # or")
            print("  pip install 'video-processor[video-360-full]'")
            return False
        except ImportError:
            print("360° utilities not available")
            return False

    print("✅ All 360° dependencies available")
    return True


def basic_360_processing():
    """Demonstrate basic 360° video processing."""
    print("\n=== Basic 360° Video Processing ===")

    # Create configuration with 360° features enabled
    config = ProcessorConfig(
        base_path=Path("/tmp/video_360_output"),
        output_formats=["mp4", "webm"],
        quality_preset="high",  # Use high quality for 360° videos
        # 360° specific settings
        enable_360_processing=True,
        auto_detect_360=True,  # Automatically detect 360° videos
        generate_360_thumbnails=True,
        thumbnail_360_projections=[
            "front",
            "back",
            "up",
            "stereographic",
        ],  # Multiple viewing angles
        video_360_bitrate_multiplier=2.5,  # Higher bitrate for 360° videos
    )

    print(f"Configuration created with 360° processing: {config.enable_360_processing}")
    print(f"Auto-detect 360° videos: {config.auto_detect_360}")
    print(f"360° thumbnail projections: {config.thumbnail_360_projections}")
    print(f"Bitrate multiplier for 360° videos: {config.video_360_bitrate_multiplier}x")

    # Create processor
    processor = VideoProcessor(config)

    # Example input file (would need to be a real 360° video file)
    input_file = Path("example_360_video.mp4")

    if input_file.exists():
        print(f"\nProcessing 360° video: {input_file}")

        result = processor.process_video(input_path=input_file, output_dir="360_output")

        print("✅ Processing complete!")
        print(f"Video ID: {result.video_id}")
        print(f"Output formats: {list(result.encoded_files.keys())}")

        # Show 360° detection results
        if result.metadata and "video_360" in result.metadata:
            video_360_info = result.metadata["video_360"]
            print("\n360° Video Detection:")
            print(f"  Is 360° video: {video_360_info['is_360_video']}")
            print(f"  Projection type: {video_360_info['projection_type']}")
            print(f"  Detection confidence: {video_360_info['confidence']}")
            print(f"  Detection methods: {video_360_info['detection_methods']}")

        # Show regular thumbnails
        if result.thumbnails:
            print(f"\nRegular thumbnails generated: {len(result.thumbnails)}")
            for thumb in result.thumbnails:
                print(f"  📸 {thumb}")

        # Show 360° thumbnails
        if result.thumbnails_360:
            print(f"\n360° thumbnails generated: {len(result.thumbnails_360)}")
            for key, thumb_path in result.thumbnails_360.items():
                print(f"  🌐 {key}: {thumb_path}")

        # Show 360° sprite files
        if result.sprite_360_files:
            print(f"\n360° sprite sheets generated: {len(result.sprite_360_files)}")
            for angle, (sprite_path, webvtt_path) in result.sprite_360_files.items():
                print(f"  🎞️ {angle}:")
                print(f"    Sprite: {sprite_path}")
                print(f"    WebVTT: {webvtt_path}")

    else:
        print(f"❌ Input file not found: {input_file}")
        print("Create a 360° video file or modify the path in this example.")


def manual_360_detection():
    """Demonstrate manual 360° video detection."""
    print("\n=== Manual 360° Video Detection ===")

    from video_processor import Video360Detection

    # Example: Test detection on various metadata scenarios
    test_cases = [
        {
            "name": "Aspect Ratio Detection (4K 360°)",
            "metadata": {
                "video": {"width": 3840, "height": 1920},
                "filename": "sample_video.mp4",
            },
        },
        {
            "name": "Filename Pattern Detection",
            "metadata": {
                "video": {"width": 1920, "height": 1080},
                "filename": "my_360_VR_video.mp4",
            },
        },
        {
            "name": "Spherical Metadata Detection",
            "metadata": {
                "video": {"width": 2560, "height": 1280},
                "filename": "video.mp4",
                "format": {
                    "tags": {
                        "Spherical": "1",
                        "ProjectionType": "equirectangular",
                        "StereoMode": "mono",
                    }
                },
            },
        },
        {
            "name": "Regular Video (No 360°)",
            "metadata": {
                "video": {"width": 1920, "height": 1080},
                "filename": "regular_video.mp4",
            },
        },
    ]

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        result = Video360Detection.detect_360_video(test_case["metadata"])

        print(f"  360° Video: {result['is_360_video']}")
        if result["is_360_video"]:
            print(f"  Projection: {result['projection_type']}")
            print(f"  Confidence: {result['confidence']:.1f}")
            print(f"  Methods: {result['detection_methods']}")


def advanced_360_configuration():
    """Demonstrate advanced 360° configuration options."""
    print("\n=== Advanced 360° Configuration ===")

    from video_processor import Video360Utils

    # Show bitrate recommendations
    print("Bitrate multipliers by projection type:")
    projection_types = ["equirectangular", "cubemap", "cylindrical", "stereographic"]
    for projection in projection_types:
        multiplier = Video360Utils.get_recommended_bitrate_multiplier(projection)
        print(f"  {projection}: {multiplier}x")

    # Show optimal resolutions
    print("\nOptimal resolutions for equirectangular 360° videos:")
    resolutions = Video360Utils.get_optimal_resolutions("equirectangular")
    for width, height in resolutions[:5]:  # Show first 5
        print(f"  {width}x{height} ({width // 1000}K)")

    # Create specialized configurations
    print("\nSpecialized Configuration Examples:")

    # High-quality archival processing
    archival_config = ProcessorConfig(
        enable_360_processing=True,
        quality_preset="ultra",
        video_360_bitrate_multiplier=3.0,  # Even higher quality
        thumbnail_360_projections=[
            "front",
            "back",
            "left",
            "right",
            "up",
            "down",
        ],  # All angles
        generate_360_thumbnails=True,
        auto_detect_360=True,
    )
    print(
        f"  📚 Archival config: {archival_config.quality_preset} quality, {archival_config.video_360_bitrate_multiplier}x bitrate"
    )

    # Mobile-optimized processing
    mobile_config = ProcessorConfig(
        enable_360_processing=True,
        quality_preset="medium",
        video_360_bitrate_multiplier=2.0,  # Lower for mobile
        thumbnail_360_projections=["front", "stereographic"],  # Minimal angles
        generate_360_thumbnails=True,
        auto_detect_360=True,
    )
    print(
        f"  📱 Mobile config: {mobile_config.quality_preset} quality, {mobile_config.video_360_bitrate_multiplier}x bitrate"
    )


def main():
    """Run all 360° video processing examples."""
    print("🌐 360° Video Processing Examples")
    print("=" * 50)

    # Check dependencies first
    if not check_360_dependencies():
        print("\n⚠️  360° processing features are not fully available.")
        print("Some examples will be skipped or show limited functionality.")

        # Still show detection examples that work without full dependencies
        manual_360_detection()
        return

    # Run all examples
    try:
        basic_360_processing()
        manual_360_detection()
        advanced_360_configuration()

        print("\n✅ All 360° video processing examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during 360° processing: {e}")
        print("Make sure you have:")
        print(
            "  1. Installed 360° dependencies: uv add 'video-processor[video-360-full]'"
        )
        print("  2. A valid 360° video file to process")


if __name__ == "__main__":
    main()
