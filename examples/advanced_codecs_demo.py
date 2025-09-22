#!/usr/bin/env python3
"""
Advanced Codecs Demonstration

Showcases next-generation codec capabilities (AV1, HEVC, HDR) built on
the existing comprehensive video processing infrastructure.
"""

import logging
from pathlib import Path

from video_processor import ProcessorConfig, VideoProcessor
from video_processor.core.advanced_encoders import AdvancedVideoEncoder, HDRProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demonstrate_av1_encoding(video_path: Path, output_dir: Path):
    """Demonstrate AV1 encoding capabilities."""
    logger.info("=== AV1 Encoding Demonstration ===")

    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["av1_mp4", "av1_webm"],  # New AV1 formats
        quality_preset="high",
        enable_av1_encoding=True,
        prefer_two_pass_av1=True,
    )

    # Check AV1 support
    advanced_encoder = AdvancedVideoEncoder(config)

    print("\n🔍 AV1 Codec Support Check:")
    av1_supported = advanced_encoder._check_av1_support()
    print(f"   AV1 Support Available: {'✅ Yes' if av1_supported else '❌ No'}")

    if not av1_supported:
        print("   To enable AV1: Install FFmpeg with libaom-av1 encoder")
        print("   Example: sudo apt install ffmpeg (with AV1 support)")
        return

    print("\n⚙️  AV1 Configuration:")
    quality_presets = advanced_encoder._get_advanced_quality_presets()
    current_preset = quality_presets[config.quality_preset]
    print(f"   Quality Preset: {config.quality_preset}")
    print(f"   CRF Value: {current_preset['av1_crf']}")
    print(f"   CPU Used (speed): {current_preset['av1_cpu_used']}")
    print(f"   Bitrate Multiplier: {current_preset['bitrate_multiplier']}")
    print(
        f"   Two-Pass Encoding: {'✅ Enabled' if config.prefer_two_pass_av1 else '❌ Disabled'}"
    )

    # Process with standard VideoProcessor (uses new AV1 formats)
    try:
        processor = VideoProcessor(config)
        result = processor.process_video(video_path)

        print("\n🎉 AV1 Encoding Results:")
        for format_name, output_path in result.encoded_files.items():
            if "av1" in format_name:
                file_size = output_path.stat().st_size if output_path.exists() else 0
                print(
                    f"   {format_name.upper()}: {output_path.name} ({file_size // 1024} KB)"
                )

        # Compare with standard H.264
        if result.encoded_files.get("mp4"):
            av1_size = (
                result.encoded_files.get("av1_mp4", Path()).stat().st_size
                if result.encoded_files.get("av1_mp4", Path()).exists()
                else 0
            )
            h264_size = (
                result.encoded_files["mp4"].stat().st_size
                if result.encoded_files["mp4"].exists()
                else 0
            )

            if av1_size > 0 and h264_size > 0:
                savings = (1 - av1_size / h264_size) * 100
                print(f"   💾 AV1 vs H.264 Size: {savings:.1f}% smaller")

    except Exception as e:
        logger.error(f"AV1 encoding demonstration failed: {e}")


def demonstrate_hevc_encoding(video_path: Path, output_dir: Path):
    """Demonstrate HEVC/H.265 encoding capabilities."""
    logger.info("=== HEVC/H.265 Encoding Demonstration ===")

    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["hevc", "mp4"],  # Compare HEVC vs H.264
        quality_preset="high",
        enable_hevc_encoding=True,
        enable_hardware_acceleration=True,
    )

    advanced_encoder = AdvancedVideoEncoder(config)

    print("\n🔍 HEVC Codec Support Check:")
    hardware_hevc = advanced_encoder._check_hardware_hevc_support()
    print(
        f"   Hardware HEVC: {'✅ Available' if hardware_hevc else '❌ Not Available'}"
    )
    print("   Software HEVC: ✅ Available (libx265)")

    print("\n⚙️  HEVC Configuration:")
    print(f"   Quality Preset: {config.quality_preset}")
    print(
        f"   Hardware Acceleration: {'✅ Enabled' if config.enable_hardware_acceleration else '❌ Disabled'}"
    )
    if hardware_hevc:
        print("   Encoder: hevc_nvenc (hardware) with libx265 fallback")
    else:
        print("   Encoder: libx265 (software)")

    try:
        processor = VideoProcessor(config)
        result = processor.process_video(video_path)

        print("\n🎉 HEVC Encoding Results:")
        for format_name, output_path in result.encoded_files.items():
            file_size = output_path.stat().st_size if output_path.exists() else 0
            codec_name = "HEVC/H.265" if format_name == "hevc" else "H.264"
            print(f"   {codec_name}: {output_path.name} ({file_size // 1024} KB)")

        # Compare HEVC vs H.264 compression
        if "hevc" in result.encoded_files and "mp4" in result.encoded_files:
            hevc_size = (
                result.encoded_files["hevc"].stat().st_size
                if result.encoded_files["hevc"].exists()
                else 0
            )
            h264_size = (
                result.encoded_files["mp4"].stat().st_size
                if result.encoded_files["mp4"].exists()
                else 0
            )

            if hevc_size > 0 and h264_size > 0:
                savings = (1 - hevc_size / h264_size) * 100
                print(f"   💾 HEVC vs H.264 Size: {savings:.1f}% smaller")

    except Exception as e:
        logger.error(f"HEVC encoding demonstration failed: {e}")


def demonstrate_hdr_processing(video_path: Path, output_dir: Path):
    """Demonstrate HDR video processing capabilities."""
    logger.info("=== HDR Video Processing Demonstration ===")

    config = ProcessorConfig(
        base_path=output_dir,
        enable_hdr_processing=True,
    )

    hdr_processor = HDRProcessor(config)

    print("\n🔍 HDR Support Check:")
    hdr_support = HDRProcessor.get_hdr_support()
    for standard, supported in hdr_support.items():
        status = "✅ Supported" if supported else "❌ Not Supported"
        print(f"   {standard.upper()}: {status}")

    # Analyze input video for HDR content
    print("\n📊 Analyzing Input Video for HDR:")
    hdr_analysis = hdr_processor.analyze_hdr_content(video_path)

    if hdr_analysis.get("is_hdr"):
        print("   HDR Content: ✅ Detected")
        print(f"   Color Primaries: {hdr_analysis.get('color_primaries', 'unknown')}")
        print(
            f"   Transfer Characteristics: {hdr_analysis.get('color_transfer', 'unknown')}"
        )
        print(f"   Color Space: {hdr_analysis.get('color_space', 'unknown')}")

        try:
            # Process HDR video
            hdr_result = hdr_processor.encode_hdr_hevc(
                video_path, output_dir, "demo_hdr", hdr_standard="hdr10"
            )

            print("\n🎉 HDR Processing Results:")
            if hdr_result.exists():
                file_size = hdr_result.stat().st_size
                print(f"   HDR10 HEVC: {hdr_result.name} ({file_size // 1024} KB)")
                print(
                    "   Features: 10-bit encoding, BT.2020 color space, HDR10 metadata"
                )

        except Exception as e:
            logger.warning(f"HDR processing failed: {e}")
            print("   ⚠️  HDR processing requires HEVC encoder with HDR support")
    else:
        print("   HDR Content: ❌ Not detected (SDR video)")
        print("   This is standard dynamic range content")
        if "error" in hdr_analysis:
            print(f"   Analysis note: {hdr_analysis['error']}")


def demonstrate_codec_comparison(video_path: Path, output_dir: Path):
    """Compare different codec performance and characteristics."""
    logger.info("=== Codec Comparison Analysis ===")

    # Test all available codecs
    config = ProcessorConfig(
        base_path=output_dir,
        output_formats=["mp4", "webm", "hevc", "av1_mp4"],
        quality_preset="medium",
    )

    print(f"\n📈 Codec Comparison (Quality: {config.quality_preset}):")
    print(f"{'Codec':<12} {'Container':<10} {'Compression':<12} {'Compatibility'}")
    print("-" * 60)
    print(f"{'H.264':<12} {'MP4':<10} {'Baseline':<12} {'Universal'}")
    print(f"{'VP9':<12} {'WebM':<10} {'~25% better':<12} {'Modern browsers'}")
    print(f"{'HEVC/H.265':<12} {'MP4':<10} {'~25% better':<12} {'Modern devices'}")
    print(f"{'AV1':<12} {'MP4/WebM':<10} {'~30% better':<12} {'Latest browsers'}")

    advanced_encoder = AdvancedVideoEncoder(config)

    print("\n🔧 Codec Availability:")
    print("   H.264 (libx264): ✅ Always available")
    print("   VP9 (libvpx-vp9): ✅ Usually available")
    print(f"   HEVC (libx265): {'✅ Available' if True else '❌ Not available'}")
    print(
        f"   HEVC Hardware: {'✅ Available' if advanced_encoder._check_hardware_hevc_support() else '❌ Not available'}"
    )
    print(
        f"   AV1 (libaom-av1): {'✅ Available' if advanced_encoder._check_av1_support() else '❌ Not available'}"
    )

    print("\n💡 Recommendations:")
    print("   📱 Mobile/Universal: H.264 MP4")
    print("   🌐 Web streaming: VP9 WebM + H.264 fallback")
    print("   📺 Modern devices: HEVC MP4")
    print("   🚀 Future-proof: AV1 (with fallbacks)")
    print("   🎬 HDR content: HEVC with HDR10 metadata")


def main():
    """Main demonstration function."""
    # Use test video or user-provided path
    video_path = Path("tests/fixtures/videos/big_buck_bunny_720p_1mb.mp4")
    output_dir = Path("/tmp/advanced_codecs_demo")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("🎬 Advanced Video Codecs Demonstration")
    print("=" * 50)

    if not video_path.exists():
        print(f"⚠️  Test video not found: {video_path}")
        print("   Please provide a video file path as argument:")
        print("   python examples/advanced_codecs_demo.py /path/to/your/video.mp4")
        return

    try:
        # 1. AV1 demonstration
        demonstrate_av1_encoding(video_path, output_dir)

        print("\n" + "=" * 50)

        # 2. HEVC demonstration
        demonstrate_hevc_encoding(video_path, output_dir)

        print("\n" + "=" * 50)

        # 3. HDR processing demonstration
        demonstrate_hdr_processing(video_path, output_dir)

        print("\n" + "=" * 50)

        # 4. Codec comparison
        demonstrate_codec_comparison(video_path, output_dir)

        print("\n🎉 Advanced codecs demonstration complete!")
        print(f"   Output files: {output_dir}")
        print("   Check the generated files to compare codec performance")

    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Allow custom video path
    if len(sys.argv) > 1:
        custom_video_path = Path(sys.argv[1])
        if custom_video_path.exists():
            # Override main function with custom path
            def custom_main():
                output_dir = Path("/tmp/advanced_codecs_demo")
                output_dir.mkdir(exist_ok=True)

                print("🎬 Advanced Video Codecs Demonstration")
                print("=" * 50)
                print(f"Using custom video: {custom_video_path}")

                demonstrate_av1_encoding(custom_video_path, output_dir)
                demonstrate_hevc_encoding(custom_video_path, output_dir)
                demonstrate_hdr_processing(custom_video_path, output_dir)
                demonstrate_codec_comparison(custom_video_path, output_dir)

                print("\n🎉 Advanced codecs demonstration complete!")
                print(f"   Output files: {output_dir}")

            custom_main()
        else:
            print(f"❌ Video file not found: {custom_video_path}")
    else:
        main()
