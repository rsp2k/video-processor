#!/usr/bin/env python3
"""
360° Video Processing Examples

This module demonstrates comprehensive usage of the 360° video processing system.
Run these examples to see the full capabilities in action.
"""

import asyncio
import logging
from pathlib import Path

from video_processor.config import ProcessorConfig
from video_processor.video_360 import (
    ProjectionType,
    Video360Processor,
    Video360StreamProcessor,
    ViewportConfig,
)
from video_processor.video_360.conversions import ProjectionConverter
from video_processor.video_360.spatial_audio import SpatialAudioProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example paths (adjust as needed)
SAMPLE_VIDEO = Path("./sample_360.mp4")
OUTPUT_DIR = Path("./360_output")


async def example_1_basic_360_processing():
    """Basic 360° video processing and analysis."""
    logger.info("=== Example 1: Basic 360° Processing ===")

    config = ProcessorConfig()
    processor = Video360Processor(config)

    # Analyze 360° content
    analysis = await processor.analyze_360_content(SAMPLE_VIDEO)

    print(f"Spherical Video: {analysis.metadata.is_spherical}")
    print(f"Projection: {analysis.metadata.projection.value}")
    print(f"Resolution: {analysis.metadata.width}x{analysis.metadata.height}")
    print(f"Has Spatial Audio: {analysis.metadata.has_spatial_audio}")
    print(f"Recommended Viewports: {len(analysis.recommended_viewports)}")

    return analysis


async def example_2_projection_conversion():
    """Convert between 360° projections."""
    logger.info("=== Example 2: Projection Conversion ===")

    config = ProcessorConfig()
    converter = ProjectionConverter(config)

    # Convert equirectangular to cubemap
    equirect_to_cubemap = OUTPUT_DIR / "converted_cubemap.mp4"
    result = await converter.convert_projection(
        SAMPLE_VIDEO,
        equirect_to_cubemap,
        ProjectionType.EQUIRECTANGULAR,
        ProjectionType.CUBEMAP,
        output_resolution=(2560, 1920),  # 4:3 for cubemap
    )

    if result.success:
        print(f"✅ Converted to cubemap: {equirect_to_cubemap}")
        print(f"Processing time: {result.processing_time:.2f}s")

    # Convert to stereographic (little planet)
    equirect_to_stereo = OUTPUT_DIR / "converted_stereographic.mp4"
    result = await converter.convert_projection(
        SAMPLE_VIDEO,
        equirect_to_stereo,
        ProjectionType.EQUIRECTANGULAR,
        ProjectionType.STEREOGRAPHIC,
        output_resolution=(1920, 1920),  # Square for stereographic
    )

    if result.success:
        print(f"✅ Converted to stereographic: {equirect_to_stereo}")
        print(f"Processing time: {result.processing_time:.2f}s")


async def example_3_viewport_extraction():
    """Extract specific viewports from 360° video."""
    logger.info("=== Example 3: Viewport Extraction ===")

    config = ProcessorConfig()
    processor = Video360Processor(config)

    # Define interesting viewports
    viewports = [
        ViewportConfig(
            yaw=0.0,
            pitch=0.0,  # Front center
            fov_horizontal=90.0,
            fov_vertical=60.0,
            output_width=1920,
            output_height=1080,
        ),
        ViewportConfig(
            yaw=180.0,
            pitch=0.0,  # Back center
            fov_horizontal=90.0,
            fov_vertical=60.0,
            output_width=1920,
            output_height=1080,
        ),
        ViewportConfig(
            yaw=0.0,
            pitch=90.0,  # Looking up
            fov_horizontal=120.0,
            fov_vertical=90.0,
            output_width=1920,
            output_height=1080,
        ),
    ]

    # Extract each viewport
    for i, viewport in enumerate(viewports):
        output_path = (
            OUTPUT_DIR
            / f"viewport_{i}_yaw{int(viewport.yaw)}_pitch{int(viewport.pitch)}.mp4"
        )

        result = await processor.extract_viewport(SAMPLE_VIDEO, output_path, viewport)

        if result.success:
            print(f"✅ Extracted viewport {i}: {output_path}")
        else:
            print(f"❌ Failed viewport {i}: {result.error_message}")


async def example_4_spatial_audio_processing():
    """Process spatial audio content."""
    logger.info("=== Example 4: Spatial Audio Processing ===")

    config = ProcessorConfig()
    spatial_processor = SpatialAudioProcessor()

    # Convert to binaural for headphones
    binaural_output = OUTPUT_DIR / "binaural_audio.mp4"
    result = await spatial_processor.convert_to_binaural(SAMPLE_VIDEO, binaural_output)

    if result.success:
        print(f"✅ Generated binaural audio: {binaural_output}")

    # Rotate spatial audio (simulate head movement)
    rotated_output = OUTPUT_DIR / "rotated_spatial_audio.mp4"
    result = await spatial_processor.rotate_spatial_audio(
        SAMPLE_VIDEO,
        rotated_output,
        yaw_rotation=45.0,  # 45° clockwise
        pitch_rotation=15.0,  # Look up 15°
    )

    if result.success:
        print(f"✅ Rotated spatial audio: {rotated_output}")


async def example_5_adaptive_streaming():
    """Create 360° adaptive streaming packages."""
    logger.info("=== Example 5: 360° Adaptive Streaming ===")

    config = ProcessorConfig()
    stream_processor = Video360StreamProcessor(config)

    # Create comprehensive streaming package
    streaming_dir = OUTPUT_DIR / "streaming"
    streaming_package = await stream_processor.create_360_adaptive_stream(
        video_path=SAMPLE_VIDEO,
        output_dir=streaming_dir,
        video_id="sample_360",
        streaming_formats=["hls", "dash"],
        enable_viewport_adaptive=True,
        enable_tiled_streaming=True,
    )

    print("✅ Streaming Package Created:")
    print(f"   Video ID: {streaming_package.video_id}")
    print(f"   Bitrate Levels: {len(streaming_package.bitrate_levels)}")
    print(f"   HLS Playlist: {streaming_package.hls_playlist}")
    print(f"   DASH Manifest: {streaming_package.dash_manifest}")

    if streaming_package.viewport_extractions:
        print(f"   Viewport Streams: {len(streaming_package.viewport_extractions)}")

    if streaming_package.tile_manifests:
        print(f"   Tiled Manifests: {len(streaming_package.tile_manifests)}")

    if streaming_package.spatial_audio_tracks:
        print(f"   Spatial Audio Tracks: {len(streaming_package.spatial_audio_tracks)}")


async def example_6_batch_processing():
    """Batch process multiple 360° videos."""
    logger.info("=== Example 6: Batch Processing ===")

    config = ProcessorConfig()
    converter = ProjectionConverter(config)

    # Simulate multiple input videos
    input_videos = [
        Path("./input_video_1.mp4"),
        Path("./input_video_2.mp4"),
        Path("./input_video_3.mp4"),
    ]

    # Target projections for batch conversion
    target_projections = [
        ProjectionType.CUBEMAP,
        ProjectionType.EAC,
        ProjectionType.STEREOGRAPHIC,
    ]

    # Process each video to each projection
    batch_results = []

    for video in input_videos:
        if not video.exists():
            print(f"⚠️ Skipping missing video: {video}")
            continue

        video_results = await converter.batch_convert_projections(
            input_path=video,
            output_dir=OUTPUT_DIR / "batch" / video.stem,
            target_projections=target_projections,
            parallel=True,  # Process projections in parallel
        )

        batch_results.extend(video_results)

        successful = sum(1 for result in video_results if result.success)
        print(
            f"✅ {video.name}: {successful}/{len(target_projections)} conversions successful"
        )

    total_successful = sum(1 for result in batch_results if result.success)
    print(
        f"\n📊 Batch Summary: {total_successful}/{len(batch_results)} total conversions successful"
    )


async def example_7_quality_analysis():
    """Analyze 360° video quality and recommend optimizations."""
    logger.info("=== Example 7: Quality Analysis ===")

    config = ProcessorConfig()
    processor = Video360Processor(config)

    # Comprehensive quality analysis
    analysis = await processor.analyze_360_content(SAMPLE_VIDEO)

    print("📊 360° Video Quality Analysis:")
    print(f"   Overall Score: {analysis.quality.overall_score:.2f}/10")
    print(f"   Projection Efficiency: {analysis.quality.projection_efficiency:.2f}")
    print(f"   Motion Intensity: {analysis.quality.motion_intensity:.2f}")
    print(f"   Pole Distortion: {analysis.quality.pole_distortion_score:.2f}")

    if analysis.quality.recommendations:
        print("\n💡 Recommendations:")
        for rec in analysis.quality.recommendations:
            print(f"   • {rec}")

    # AI-powered content insights
    if hasattr(analysis, "ai_analysis") and analysis.ai_analysis:
        print("\n🤖 AI Insights:")
        print(f"   Scene Description: {analysis.ai_analysis.scene_description}")
        print(
            f"   Dominant Objects: {', '.join(analysis.ai_analysis.dominant_objects)}"
        )
        print(
            f"   Mood Score: {analysis.ai_analysis.mood_analysis.dominant_mood} ({analysis.ai_analysis.mood_analysis.confidence:.2f})"
        )


async def run_all_examples():
    """Run all 360° video processing examples."""
    logger.info("🎬 Starting 360° Video Processing Examples")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Check if sample video exists
        if not SAMPLE_VIDEO.exists():
            logger.warning(f"Sample video not found: {SAMPLE_VIDEO}")
            logger.info("Creating synthetic test video...")

            # Generate synthetic 360° test video
            from video_processor.tests.fixtures.generate_360_synthetic import (
                SyntheticVideo360Generator,
            )

            generator = SyntheticVideo360Generator()
            await generator.create_equirect_grid(SAMPLE_VIDEO)
            logger.info(f"✅ Created synthetic test video: {SAMPLE_VIDEO}")

        # Run examples sequentially
        await example_1_basic_360_processing()
        await example_2_projection_conversion()
        await example_3_viewport_extraction()
        await example_4_spatial_audio_processing()
        await example_5_adaptive_streaming()
        await example_6_batch_processing()
        await example_7_quality_analysis()

        logger.info("🎉 All 360° examples completed successfully!")

    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        raise


if __name__ == "__main__":
    """Run examples from command line."""
    asyncio.run(run_all_examples())
