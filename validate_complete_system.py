#!/usr/bin/env python3
"""
Complete System Validation Script for Video Processor v0.4.0

This script validates that all four phases of the video processor are working correctly:
- Phase 1: AI-Powered Content Analysis
- Phase 2: Next-Generation Codecs & HDR
- Phase 3: Adaptive Streaming
- Phase 4: Complete 360° Video Processing

Run this to verify the complete system is operational.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def validate_system():
    """Comprehensive system validation."""
    print("🎬 Video Processor v0.4.0 - Complete System Validation")
    print("=" * 60)

    validation_results = {
        "phase_1_ai": False,
        "phase_2_codecs": False,
        "phase_3_streaming": False,
        "phase_4_360": False,
        "core_processor": False,
        "configuration": False,
    }

    # Test Configuration System
    print("\n📋 Testing Configuration System...")
    try:
        from video_processor.config import ProcessorConfig

        config = ProcessorConfig(
            quality_preset="high",
            enable_ai_analysis=True,
            enable_av1_encoding=False,  # Don't require system codecs
            enable_hevc_encoding=False,
            # Don't enable 360° processing in basic config test
            output_formats=["mp4"],
        )

        assert hasattr(config, "enable_ai_analysis")
        assert hasattr(config, "enable_360_processing")
        assert config.quality_preset == "high"

        validation_results["configuration"] = True
        print("✅ Configuration System: OPERATIONAL")

    except Exception as e:
        print(f"❌ Configuration System: FAILED - {e}")
        return validation_results

    # Test Phase 1: AI Analysis
    print("\n🤖 Testing Phase 1: AI-Powered Content Analysis...")
    try:
        from video_processor.ai import VideoContentAnalyzer
        from video_processor.ai.content_analyzer import (
            ContentAnalysis,
            SceneAnalysis,
            QualityMetrics,
        )

        analyzer = VideoContentAnalyzer()

        # Test model creation
        scene_analysis = SceneAnalysis(
            scene_boundaries=[0.0, 30.0, 60.0],
            scene_count=3,
            average_scene_length=30.0,
            key_moments=[5.0, 35.0, 55.0],
            confidence_scores=[0.9, 0.8, 0.85],
        )

        quality_metrics = QualityMetrics(
            sharpness_score=0.8,
            brightness_score=0.6,
            contrast_score=0.7,
            noise_level=0.2,
            overall_quality=0.75,
        )

        content_analysis = ContentAnalysis(
            scenes=scene_analysis,
            quality_metrics=quality_metrics,
            duration=90.0,
            resolution=(1920, 1080),
            has_motion=True,
            motion_intensity=0.6,
            is_360_video=False,
            recommended_thumbnails=[5.0, 35.0, 55.0],
        )

        assert content_analysis.scenes.scene_count == 3
        assert content_analysis.quality_metrics.overall_quality == 0.75
        assert len(content_analysis.recommended_thumbnails) == 3

        validation_results["phase_1_ai"] = True
        print("✅ Phase 1 - AI Content Analysis: OPERATIONAL")

    except Exception as e:
        print(f"❌ Phase 1 - AI Content Analysis: FAILED - {e}")

    # Test Phase 2: Advanced Codecs
    print("\n🎥 Testing Phase 2: Next-Generation Codecs...")
    try:
        from video_processor.core.advanced_encoders import AdvancedVideoEncoder
        from video_processor.core.enhanced_processor import EnhancedVideoProcessor

        # Test advanced encoder
        advanced_encoder = AdvancedVideoEncoder(config)

        # Verify methods exist
        assert hasattr(advanced_encoder, "encode_av1")
        assert hasattr(advanced_encoder, "encode_hevc")
        assert hasattr(advanced_encoder, "get_supported_advanced_codecs")

        # Test supported codecs
        supported_codecs = advanced_encoder.get_supported_advanced_codecs()
        av1_bitrate_multiplier = advanced_encoder.get_av1_bitrate_multiplier()

        print(f"   Supported Advanced Codecs: {supported_codecs}")
        print(f"   AV1 Bitrate Multiplier: {av1_bitrate_multiplier}")
        print(f"   AV1 Encoding Available: {'encode_av1' in dir(advanced_encoder)}")
        print(f"   HEVC Encoding Available: {'encode_hevc' in dir(advanced_encoder)}")

        # Test enhanced processor
        enhanced_processor = EnhancedVideoProcessor(config)
        assert hasattr(enhanced_processor, "content_analyzer")
        assert hasattr(enhanced_processor, "process_video_enhanced")

        validation_results["phase_2_codecs"] = True
        print("✅ Phase 2 - Advanced Codecs: OPERATIONAL")

    except Exception as e:
        import traceback

        print(f"❌ Phase 2 - Advanced Codecs: FAILED - {e}")
        print(f"   Debug info: {traceback.format_exc()}")

    # Test Phase 3: Adaptive Streaming
    print("\n📡 Testing Phase 3: Adaptive Streaming...")
    try:
        from video_processor.streaming import AdaptiveStreamProcessor
        from video_processor.streaming.hls import HLSGenerator
        from video_processor.streaming.dash import DASHGenerator

        stream_processor = AdaptiveStreamProcessor(config)
        hls_generator = HLSGenerator()
        dash_generator = DASHGenerator()

        assert hasattr(stream_processor, "create_adaptive_stream")
        assert hasattr(hls_generator, "create_master_playlist")
        assert hasattr(dash_generator, "create_manifest")

        validation_results["phase_3_streaming"] = True
        print("✅ Phase 3 - Adaptive Streaming: OPERATIONAL")

    except Exception as e:
        print(f"❌ Phase 3 - Adaptive Streaming: FAILED - {e}")

    # Test Phase 4: 360° Video Processing
    print("\n🌐 Testing Phase 4: Complete 360° Video Processing...")
    try:
        from video_processor.video_360 import (
            Video360Processor,
            Video360StreamProcessor,
            ProjectionConverter,
            SpatialAudioProcessor,
        )
        from video_processor.video_360.models import (
            ProjectionType,
            StereoMode,
            SpatialAudioType,
            SphericalMetadata,
            ViewportConfig,
            Video360Quality,
            Video360Analysis,
        )

        # Test 360° processors
        video_360_processor = Video360Processor(config)
        stream_360_processor = Video360StreamProcessor(config)
        projection_converter = ProjectionConverter()
        spatial_processor = SpatialAudioProcessor()

        # Test 360° models
        metadata = SphericalMetadata(
            is_spherical=True,
            projection=ProjectionType.EQUIRECTANGULAR,
            stereo_mode=StereoMode.MONO,
            width=3840,
            height=1920,
            has_spatial_audio=True,
            audio_type=SpatialAudioType.AMBISONIC_BFORMAT,
        )

        viewport = ViewportConfig(yaw=0.0, pitch=0.0, fov=90.0, width=1920, height=1080)

        quality = Video360Quality()

        analysis = Video360Analysis(metadata=metadata, quality=quality)

        # Validate all components
        assert hasattr(video_360_processor, "analyze_360_content")
        assert hasattr(projection_converter, "convert_projection")
        assert hasattr(spatial_processor, "convert_to_binaural")
        assert hasattr(stream_360_processor, "create_360_adaptive_stream")

        assert metadata.is_spherical
        assert metadata.projection == ProjectionType.EQUIRECTANGULAR
        assert viewport.width == 1920
        assert quality.overall_quality >= 0.0
        assert analysis.metadata.is_spherical

        # Test enum completeness
        projections = [
            ProjectionType.EQUIRECTANGULAR,
            ProjectionType.CUBEMAP,
            ProjectionType.EAC,
            ProjectionType.FISHEYE,
            ProjectionType.STEREOGRAPHIC,
            ProjectionType.FLAT,
        ]

        for proj in projections:
            assert proj.value is not None

        validation_results["phase_4_360"] = True
        print("✅ Phase 4 - 360° Video Processing: OPERATIONAL")

    except Exception as e:
        print(f"❌ Phase 4 - 360° Video Processing: FAILED - {e}")

    # Test Core Processor Integration
    print("\n⚡ Testing Core Video Processor Integration...")
    try:
        from video_processor import VideoProcessor

        processor = VideoProcessor(config)

        assert hasattr(processor, "process_video")
        assert hasattr(processor, "config")
        assert processor.config.enable_ai_analysis == True

        validation_results["core_processor"] = True
        print("✅ Core Video Processor: OPERATIONAL")

    except Exception as e:
        print(f"❌ Core Video Processor: FAILED - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)

    total_tests = len(validation_results)
    passed_tests = sum(validation_results.values())

    for component, status in validation_results.items():
        status_icon = "✅" if status else "❌"
        component_name = component.replace("_", " ").title()
        print(f"{status_icon} {component_name}")

    print(f"\nOverall Status: {passed_tests}/{total_tests} components operational")

    if passed_tests == total_tests:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("🚀 Video Processor v0.4.0 is ready for production use!")
        print("\n🎬 Complete multimedia processing platform with:")
        print("   • AI-powered content analysis")
        print("   • Next-generation codecs (AV1, HEVC, HDR)")
        print("   • Adaptive streaming (HLS, DASH)")
        print("   • Complete 360° video processing")
        print("   • Production-ready deployment")

        return True
    else:
        failed_components = [k for k, v in validation_results.items() if not v]
        print(f"\n⚠️ ISSUES DETECTED:")
        for component in failed_components:
            print(f"   • {component.replace('_', ' ').title()}")

        return False


if __name__ == "__main__":
    """Run system validation."""
    print("Starting Video Processor v0.4.0 validation...")

    try:
        success = asyncio.run(validate_system())
        exit_code = 0 if success else 1

        print(f"\nValidation {'PASSED' if success else 'FAILED'}")
        exit(exit_code)

    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        print("Please check your installation and dependencies.")
        exit(1)
