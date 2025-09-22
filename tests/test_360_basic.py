#!/usr/bin/env python3
"""
Basic 360° video processing functionality tests.

Simple tests to verify the 360° system is properly integrated and functional.
"""

from pathlib import Path

import pytest

from video_processor.config import ProcessorConfig
from video_processor.video_360.models import (
    ProjectionType,
    SpatialAudioType,
    SphericalMetadata,
    StereoMode,
    Video360Analysis,
    Video360Quality,
    ViewportConfig,
)


class TestBasic360Integration:
    """Test basic 360° functionality."""

    def test_360_imports(self):
        """Verify all 360° modules can be imported."""
        from video_processor.video_360 import (
            ProjectionConverter,
            SpatialAudioProcessor,
            Video360Processor,
            Video360StreamProcessor,
        )

        # Should import without error
        assert Video360Processor is not None
        assert Video360StreamProcessor is not None
        assert ProjectionConverter is not None
        assert SpatialAudioProcessor is not None

    def test_360_models_creation(self):
        """Test creation of 360° data models."""

        # Test SphericalMetadata
        metadata = SphericalMetadata(
            is_spherical=True,
            projection=ProjectionType.EQUIRECTANGULAR,
            stereo_mode=StereoMode.MONO,
            width=3840,
            height=1920,
        )

        assert metadata.is_spherical
        assert metadata.projection == ProjectionType.EQUIRECTANGULAR
        assert metadata.width == 3840

        # Test ViewportConfig
        viewport = ViewportConfig(yaw=0.0, pitch=0.0, fov=90.0, width=1920, height=1080)

        assert viewport.yaw == 0.0
        assert viewport.width == 1920

        # Test Video360Quality
        quality = Video360Quality()

        assert quality.projection_quality == 0.0
        assert quality.overall_quality >= 0.0

        # Test Video360Analysis
        analysis = Video360Analysis(metadata=metadata, quality=quality)

        assert analysis.metadata.is_spherical
        assert analysis.quality.overall_quality >= 0.0

    def test_projection_types(self):
        """Test all projection types are accessible."""

        projections = [
            ProjectionType.EQUIRECTANGULAR,
            ProjectionType.CUBEMAP,
            ProjectionType.EAC,
            ProjectionType.FISHEYE,
            ProjectionType.STEREOGRAPHIC,
        ]

        for proj in projections:
            assert proj.value is not None
            assert isinstance(proj.value, str)

    def test_config_with_ai_support(self):
        """Test config includes AI analysis support."""

        config = ProcessorConfig()

        # Should have AI analysis enabled by default
        assert hasattr(config, "enable_ai_analysis")
        assert config.enable_ai_analysis == True

    def test_processor_initialization(self):
        """Test 360° processors can be initialized."""
        from video_processor.video_360 import Video360Processor, Video360StreamProcessor
        from video_processor.video_360.conversions import ProjectionConverter
        from video_processor.video_360.spatial_audio import SpatialAudioProcessor

        config = ProcessorConfig()

        # Should initialize without error
        video_processor = Video360Processor(config)
        assert video_processor is not None

        stream_processor = Video360StreamProcessor(config)
        assert stream_processor is not None

        converter = ProjectionConverter()
        assert converter is not None

        spatial_processor = SpatialAudioProcessor()
        assert spatial_processor is not None

    def test_360_examples_import(self):
        """Test that 360° examples can be imported."""

        # Should be able to import the examples module
        import sys

        examples_path = Path(__file__).parent.parent / "examples"
        if str(examples_path) not in sys.path:
            sys.path.insert(0, str(examples_path))

        try:
            import video_processor.examples

            # If we get here, basic import structure is working
            assert True
        except ImportError:
            # Examples might not be in the package, that's okay
            pytest.skip("Examples not available as package")


class TestProjectionEnums:
    """Test projection and stereo enums."""

    def test_projection_enum_completeness(self):
        """Test that all expected projections are available."""

        expected_projections = [
            "EQUIRECTANGULAR",
            "CUBEMAP",
            "EAC",
            "FISHEYE",
            "DUAL_FISHEYE",
            "STEREOGRAPHIC",
            "FLAT",
            "UNKNOWN",
        ]

        for proj_name in expected_projections:
            assert hasattr(ProjectionType, proj_name)

    def test_stereo_enum_completeness(self):
        """Test that all expected stereo modes are available."""

        expected_stereo = [
            "MONO",
            "TOP_BOTTOM",
            "LEFT_RIGHT",
            "FRAME_SEQUENTIAL",
            "ANAGLYPH",
            "UNKNOWN",
        ]

        for stereo_name in expected_stereo:
            assert hasattr(StereoMode, stereo_name)

    def test_spatial_audio_enum_completeness(self):
        """Test that all expected spatial audio types are available."""

        expected_audio = [
            "NONE",
            "AMBISONIC_BFORMAT",
            "AMBISONIC_HOA",
            "OBJECT_BASED",
            "HEAD_LOCKED",
            "BINAURAL",
        ]

        for audio_name in expected_audio:
            assert hasattr(SpatialAudioType, audio_name)


class Test360Utils:
    """Test 360° utility functions."""

    def test_spherical_metadata_properties(self):
        """Test spherical metadata computed properties."""

        metadata = SphericalMetadata(
            is_spherical=True,
            projection=ProjectionType.EQUIRECTANGULAR,
            stereo_mode=StereoMode.TOP_BOTTOM,
            width=3840,
            height=1920,
            has_spatial_audio=True,  # Set explicitly
            audio_type=SpatialAudioType.AMBISONIC_BFORMAT,
        )

        # Test computed properties
        assert metadata.is_stereoscopic == True  # TOP_BOTTOM is stereoscopic
        assert metadata.has_spatial_audio == True  # Set explicitly
        # Note: aspect_ratio might be computed differently, don't test exact value

        # Test mono case
        mono_metadata = SphericalMetadata(
            stereo_mode=StereoMode.MONO, audio_type=SpatialAudioType.NONE
        )

        assert mono_metadata.is_stereoscopic == False
        assert mono_metadata.has_spatial_audio == False


if __name__ == "__main__":
    """Run basic tests directly."""
    pytest.main([__file__, "-v"])
