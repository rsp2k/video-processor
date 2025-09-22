#!/usr/bin/env python3
"""
Streaming & Real-Time Processing Demonstration

Showcases adaptive streaming capabilities (HLS, DASH) built on the existing
comprehensive video processing infrastructure with AI optimization.
"""

import asyncio
import logging
from pathlib import Path

from video_processor import ProcessorConfig
from video_processor.streaming import AdaptiveStreamProcessor, BitrateLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_adaptive_streaming(video_path: Path, output_dir: Path):
    """Demonstrate adaptive streaming creation."""
    logger.info("=== Adaptive Streaming Demonstration ===")

    # Configure for streaming with multiple formats and AI optimization
    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["mp4", "hevc", "av1_mp4"],  # Multiple codec options
        quality_preset="high",
        enable_av1_encoding=True,
        enable_hevc_encoding=True,
        generate_sprites=True,
        sprite_interval=5,  # More frequent for streaming
    )

    # Create adaptive stream processor with AI optimization
    processor = AdaptiveStreamProcessor(config, enable_ai_optimization=True)

    print("\n🔍 Streaming Capabilities:")
    capabilities = processor.get_streaming_capabilities()
    for capability, available in capabilities.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"   {capability.replace('_', ' ').title()}: {status}")

    print("\n🎯 Creating Adaptive Streaming Package...")
    print(f"   Source: {video_path}")
    print(f"   Output: {output_dir}")

    try:
        # Create adaptive streaming package
        streaming_package = await processor.create_adaptive_stream(
            video_path=video_path,
            output_dir=output_dir,
            video_id="demo_stream",
            streaming_formats=["hls", "dash"],
        )

        print("\n🎉 Streaming Package Created Successfully!")
        print(f"   Video ID: {streaming_package.video_id}")
        print(f"   Output Directory: {streaming_package.output_dir}")
        print(f"   Segment Duration: {streaming_package.segment_duration}s")

        # Display bitrate ladder information
        print(f"\n📊 Bitrate Ladder ({len(streaming_package.bitrate_levels)} levels):")
        for level in streaming_package.bitrate_levels:
            print(
                f"   {level.name:<6} | {level.width}x{level.height:<4} | {level.bitrate:>4}k | {level.codec.upper()}"
            )

        # Display generated files
        print("\n📁 Generated Files:")
        if streaming_package.hls_playlist:
            print(f"   HLS Playlist: {streaming_package.hls_playlist}")
        if streaming_package.dash_manifest:
            print(f"   DASH Manifest: {streaming_package.dash_manifest}")
        if streaming_package.thumbnail_track:
            print(f"   Thumbnail Track: {streaming_package.thumbnail_track}")

        return streaming_package

    except Exception as e:
        logger.error(f"Adaptive streaming failed: {e}")
        raise


async def demonstrate_custom_bitrate_ladder(video_path: Path, output_dir: Path):
    """Demonstrate custom bitrate ladder configuration."""
    logger.info("=== Custom Bitrate Ladder Demonstration ===")

    # Define custom bitrate ladder optimized for mobile streaming
    mobile_ladder = [
        BitrateLevel("240p", 426, 240, 300, 450, "h264", "mp4"),  # Very low bandwidth
        BitrateLevel("360p", 640, 360, 600, 900, "h264", "mp4"),  # Low bandwidth
        BitrateLevel("480p", 854, 480, 1200, 1800, "hevc", "mp4"),  # Medium with HEVC
        BitrateLevel("720p", 1280, 720, 2400, 3600, "av1", "mp4"),  # High with AV1
    ]

    print("\n📱 Mobile-Optimized Bitrate Ladder:")
    print(f"{'Level':<6} | {'Resolution':<10} | {'Bitrate':<8} | {'Codec'}")
    print("-" * 45)
    for level in mobile_ladder:
        print(
            f"{level.name:<6} | {level.width}x{level.height:<6} | {level.bitrate:>4}k    | {level.codec.upper()}"
        )

    config = ProcessorConfig(
        base_path=output_dir / "mobile",
        quality_preset="medium",
    )

    processor = AdaptiveStreamProcessor(config)

    try:
        # Create streaming package with custom ladder
        streaming_package = await processor.create_adaptive_stream(
            video_path=video_path,
            output_dir=output_dir / "mobile",
            video_id="mobile_stream",
            streaming_formats=["hls"],  # HLS for mobile
            custom_bitrate_ladder=mobile_ladder,
        )

        print("\n🎉 Mobile Streaming Package Created!")
        print(f"   HLS Playlist: {streaming_package.hls_playlist}")
        print("   Optimized for: Mobile devices and low bandwidth")

        return streaming_package

    except Exception as e:
        logger.error(f"Mobile streaming failed: {e}")
        raise


async def demonstrate_ai_optimized_streaming(video_path: Path, output_dir: Path):
    """Demonstrate AI-optimized adaptive streaming."""
    logger.info("=== AI-Optimized Streaming Demonstration ===")

    config = ProcessorConfig(
        base_path=output_dir / "ai_optimized",
        quality_preset="high",
        enable_av1_encoding=True,
        enable_hevc_encoding=True,
    )

    # Enable AI optimization
    processor = AdaptiveStreamProcessor(config, enable_ai_optimization=True)

    if not processor.enable_ai_optimization:
        print("   ⚠️  AI optimization not available (missing dependencies)")
        print("   Using intelligent defaults based on video characteristics")

    print("\n🧠 AI-Enhanced Streaming Features:")
    print("   ✅ Content-aware bitrate ladder generation")
    print("   ✅ Motion-adaptive bitrate adjustment")
    print("   ✅ Resolution-aware quality optimization")
    print("   ✅ Codec selection based on content analysis")

    try:
        # Let AI analyze and optimize the streaming package
        streaming_package = await processor.create_adaptive_stream(
            video_path=video_path,
            output_dir=output_dir / "ai_optimized",
            video_id="ai_stream",
        )

        print("\n🎯 AI Optimization Results:")
        print(f"   Generated {len(streaming_package.bitrate_levels)} bitrate levels")
        print("   Streaming formats: HLS + DASH")

        # Show how AI influenced the bitrate ladder
        total_bitrate = sum(level.bitrate for level in streaming_package.bitrate_levels)
        avg_bitrate = total_bitrate / len(streaming_package.bitrate_levels)
        print(f"   Average bitrate: {avg_bitrate:.0f}k (optimized for content)")

        # Show codec distribution
        codec_count = {}
        for level in streaming_package.bitrate_levels:
            codec_count[level.codec] = codec_count.get(level.codec, 0) + 1

        print("   Codec distribution:")
        for codec, count in codec_count.items():
            print(f"     {codec.upper()}: {count} level(s)")

        return streaming_package

    except Exception as e:
        logger.error(f"AI-optimized streaming failed: {e}")
        raise


def demonstrate_streaming_deployment(streaming_packages: list):
    """Demonstrate streaming deployment considerations."""
    logger.info("=== Streaming Deployment Guide ===")

    print("\n🚀 Production Deployment Considerations:")
    print("\n📦 CDN Distribution:")
    print("   • Upload generated HLS/DASH files to CDN")
    print("   • Configure proper MIME types:")
    print("     - .m3u8 files: application/vnd.apple.mpegurl")
    print("     - .mpd files: application/dash+xml")
    print("     - .ts/.m4s segments: video/mp2t, video/mp4")

    print("\n🌐 Web Player Integration:")
    print("   • HLS: Use hls.js for browser support")
    print("   • DASH: Use dash.js or shaka-player")
    print("   • Native support: Safari (HLS), Chrome/Edge (DASH)")

    print("\n📊 Analytics & Monitoring:")
    print("   • Track bitrate switching events")
    print("   • Monitor buffer health and stall events")
    print("   • Measure startup time and seeking performance")

    print("\n💾 Storage Optimization:")
    total_files = 0
    total_size_estimate = 0

    for i, package in enumerate(streaming_packages, 1):
        files_count = len(package.bitrate_levels) * 2  # HLS + DASH per level
        total_files += files_count

        # Rough size estimate (segments + manifests)
        size_estimate = files_count * 50  # ~50KB per segment average
        total_size_estimate += size_estimate

        print(f"   Package {i}: ~{files_count} files, ~{size_estimate}KB")

    print(f"   Total: ~{total_files} files, ~{total_size_estimate}KB")

    print("\n🔒 Security Considerations:")
    print("   • DRM integration for premium content")
    print("   • Token-based authentication for private streams")
    print("   • HTTPS delivery for all manifest and segment files")


async def main():
    """Main demonstration function."""
    video_path = Path("tests/fixtures/videos/big_buck_bunny_720p_1mb.mp4")
    output_dir = Path("/tmp/streaming_demo")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("🎬 Streaming & Real-Time Processing Demonstration")
    print("=" * 55)

    if not video_path.exists():
        print(f"⚠️  Test video not found: {video_path}")
        print("   Please provide a video file path as argument:")
        print("   python examples/streaming_demo.py /path/to/your/video.mp4")
        return

    streaming_packages = []

    try:
        # 1. Standard adaptive streaming
        package1 = await demonstrate_adaptive_streaming(video_path, output_dir)
        streaming_packages.append(package1)

        print("\n" + "=" * 55)

        # 2. Custom bitrate ladder
        package2 = await demonstrate_custom_bitrate_ladder(video_path, output_dir)
        streaming_packages.append(package2)

        print("\n" + "=" * 55)

        # 3. AI-optimized streaming
        package3 = await demonstrate_ai_optimized_streaming(video_path, output_dir)
        streaming_packages.append(package3)

        print("\n" + "=" * 55)

        # 4. Deployment guide
        demonstrate_streaming_deployment(streaming_packages)

        print("\n🎉 Streaming demonstration complete!")
        print(f"   Generated {len(streaming_packages)} streaming packages")
        print(f"   Output directory: {output_dir}")
        print("   Ready for CDN deployment and web player integration!")

    except Exception as e:
        logger.error(f"Streaming demonstration failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Allow custom video path
    if len(sys.argv) > 1:
        custom_video_path = Path(sys.argv[1])
        if custom_video_path.exists():
            # Override main function with custom path
            async def custom_main():
                output_dir = Path("/tmp/streaming_demo")
                output_dir.mkdir(exist_ok=True)

                print("🎬 Streaming & Real-Time Processing Demonstration")
                print("=" * 55)
                print(f"Using custom video: {custom_video_path}")

                streaming_packages = []

                package1 = await demonstrate_adaptive_streaming(
                    custom_video_path, output_dir
                )
                streaming_packages.append(package1)

                package2 = await demonstrate_custom_bitrate_ladder(
                    custom_video_path, output_dir
                )
                streaming_packages.append(package2)

                package3 = await demonstrate_ai_optimized_streaming(
                    custom_video_path, output_dir
                )
                streaming_packages.append(package3)

                demonstrate_streaming_deployment(streaming_packages)

                print("\n🎉 Streaming demonstration complete!")
                print(f"   Output directory: {output_dir}")

            asyncio.run(custom_main())
        else:
            print(f"❌ Video file not found: {custom_video_path}")
    else:
        asyncio.run(main())
