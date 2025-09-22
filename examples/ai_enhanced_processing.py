#!/usr/bin/env python3
"""
AI-Enhanced Video Processing Example

Demonstrates the new AI-powered content analysis and smart processing features
built on top of the existing comprehensive video processing infrastructure.
"""

import asyncio
import logging
from pathlib import Path

from video_processor import (
    HAS_AI_SUPPORT,
    EnhancedVideoProcessor,
    ProcessorConfig,
    VideoContentAnalyzer,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_content_example(video_path: Path):
    """Demonstrate AI content analysis without processing."""
    logger.info("=== AI Content Analysis Example ===")

    if not HAS_AI_SUPPORT:
        logger.error(
            "AI support not available. Install with: uv add 'video-processor[ai-analysis]'"
        )
        return

    analyzer = VideoContentAnalyzer()

    # Check available capabilities
    missing_deps = analyzer.get_missing_dependencies()
    if missing_deps:
        logger.warning(f"Some AI features limited. Missing: {missing_deps}")

    # Analyze video content
    analysis = await analyzer.analyze_content(video_path)

    if analysis:
        print("\n📊 Content Analysis Results:")
        print(f"   Duration: {analysis.duration:.1f} seconds")
        print(f"   Resolution: {analysis.resolution[0]}x{analysis.resolution[1]}")
        print(f"   360° Video: {analysis.is_360_video}")
        print(f"   Has Motion: {analysis.has_motion}")
        print(f"   Motion Intensity: {analysis.motion_intensity:.2f}")

        print("\n🎬 Scene Analysis:")
        print(f"   Scene Count: {analysis.scenes.scene_count}")
        print(f"   Average Scene Length: {analysis.scenes.average_scene_length:.1f}s")
        print(
            f"   Scene Boundaries: {[f'{b:.1f}s' for b in analysis.scenes.scene_boundaries[:5]]}"
        )

        print("\n📈 Quality Metrics:")
        print(f"   Overall Quality: {analysis.quality_metrics.overall_quality:.2f}")
        print(f"   Sharpness: {analysis.quality_metrics.sharpness_score:.2f}")
        print(f"   Brightness: {analysis.quality_metrics.brightness_score:.2f}")
        print(f"   Contrast: {analysis.quality_metrics.contrast_score:.2f}")
        print(f"   Noise Level: {analysis.quality_metrics.noise_level:.2f}")

        print("\n🖼️ Smart Thumbnail Recommendations:")
        for i, timestamp in enumerate(analysis.recommended_thumbnails):
            print(f"   Thumbnail {i + 1}: {timestamp:.1f}s")

    return analysis


async def enhanced_processing_example(video_path: Path, output_dir: Path):
    """Demonstrate AI-enhanced video processing."""
    logger.info("=== AI-Enhanced Processing Example ===")

    if not HAS_AI_SUPPORT:
        logger.error(
            "AI support not available. Install with: uv add 'video-processor[ai-analysis]'"
        )
        return

    # Create configuration
    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["mp4", "webm"],
        quality_preset="medium",
        generate_sprites=True,
        thumbnail_timestamps=[5],  # Will be optimized by AI
    )

    # Create enhanced processor
    processor = EnhancedVideoProcessor(config, enable_ai=True)

    # Show AI capabilities
    capabilities = processor.get_ai_capabilities()
    print("\n🤖 AI Capabilities:")
    for capability, available in capabilities.items():
        status = "✅" if available else "❌"
        print(f"   {status} {capability.replace('_', ' ').title()}")

    missing_deps = processor.get_missing_ai_dependencies()
    if missing_deps:
        print(f"\n⚠️  For full AI capabilities, install: {', '.join(missing_deps)}")

    # Process video with AI enhancements
    logger.info("Starting AI-enhanced video processing...")

    result = await processor.process_video_enhanced(
        video_path, enable_smart_thumbnails=True
    )

    print("\n✨ Enhanced Processing Results:")
    print(f"   Video ID: {result.video_id}")
    print(f"   Output Directory: {result.output_path}")
    print(f"   Encoded Formats: {list(result.encoded_files.keys())}")
    print(f"   Standard Thumbnails: {len(result.thumbnails)}")
    print(f"   Smart Thumbnails: {len(result.smart_thumbnails)}")

    if result.sprite_file:
        print(f"   Sprite Sheet: {result.sprite_file.name}")

    if result.thumbnails_360:
        print(f"   360° Thumbnails: {list(result.thumbnails_360.keys())}")

    # Show AI analysis results
    if result.content_analysis:
        analysis = result.content_analysis
        print("\n🎯 AI-Driven Optimizations:")

        if analysis.is_360_video:
            print("   ✓ Detected 360° video - enabled specialized processing")

        if analysis.motion_intensity > 0.7:
            print("   ✓ High motion detected - optimized sprite generation")
        elif analysis.motion_intensity < 0.3:
            print("   ✓ Low motion detected - reduced sprite density for efficiency")

        quality = analysis.quality_metrics.overall_quality
        if quality > 0.8:
            print("   ✓ High quality source - preserved maximum detail")
        elif quality < 0.4:
            print("   ✓ Lower quality source - optimized for efficiency")

    return result


def compare_processing_modes_example(video_path: Path, output_dir: Path):
    """Compare standard vs AI-enhanced processing."""
    logger.info("=== Processing Mode Comparison ===")

    if not HAS_AI_SUPPORT:
        logger.error("AI support not available for comparison.")
        return

    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["mp4"],
        quality_preset="medium",
    )

    # Standard processor
    from video_processor import VideoProcessor

    standard_processor = VideoProcessor(config)

    # Enhanced processor
    enhanced_processor = EnhancedVideoProcessor(config, enable_ai=True)

    print("\n📊 Processing Capabilities Comparison:")
    print("   Standard Processor:")
    print("   ✓ Multi-format encoding (MP4, WebM, OGV)")
    print("   ✓ Quality presets (low/medium/high/ultra)")
    print("   ✓ Thumbnail generation")
    print("   ✓ Sprite sheet creation")
    print("   ✓ 360° video processing (if enabled)")

    print("\n   AI-Enhanced Processor (all above plus):")
    print("   ✨ Intelligent content analysis")
    print("   ✨ Scene-based thumbnail selection")
    print("   ✨ Quality-aware processing optimization")
    print("   ✨ Motion-adaptive sprite generation")
    print("   ✨ Automatic 360° detection")
    print("   ✨ Smart configuration optimization")


async def main():
    """Main demonstration function."""
    # Use a test video (you can replace with your own)
    video_path = Path("tests/fixtures/videos/big_buck_bunny_720p_1mb.mp4")
    output_dir = Path("/tmp/ai_demo_output")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("🎬 AI-Enhanced Video Processing Demonstration")
    print("=" * 50)

    if not video_path.exists():
        print(f"⚠️  Test video not found: {video_path}")
        print(
            "   Please provide a video file path or use the test suite to generate fixtures."
        )
        print(
            "   Example: python -m video_processor.examples.ai_enhanced_processing /path/to/your/video.mp4"
        )
        return

    try:
        # 1. Content analysis example
        analysis = await analyze_content_example(video_path)

        # 2. Enhanced processing example
        if HAS_AI_SUPPORT:
            result = await enhanced_processing_example(video_path, output_dir)

        # 3. Comparison example
        compare_processing_modes_example(video_path, output_dir)

        print(f"\n🎉 Demonstration complete! Check outputs in: {output_dir}")

    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Allow custom video path
    if len(sys.argv) > 1:
        custom_video_path = Path(sys.argv[1])
        if custom_video_path.exists():
            # Override default path

            main_module = sys.modules[__name__]

            async def custom_main():
                output_dir = Path("/tmp/ai_demo_output")
                output_dir.mkdir(exist_ok=True)

                print("🎬 AI-Enhanced Video Processing Demonstration")
                print("=" * 50)
                print(f"Using custom video: {custom_video_path}")

                analysis = await analyze_content_example(custom_video_path)
                if HAS_AI_SUPPORT:
                    result = await enhanced_processing_example(
                        custom_video_path, output_dir
                    )
                compare_processing_modes_example(custom_video_path, output_dir)

                print(f"\n🎉 Demonstration complete! Check outputs in: {output_dir}")

            main_module.main = custom_main

    asyncio.run(main())
