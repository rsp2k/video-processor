"""Tests for 360° video functionality."""

import pytest

from video_processor import ProcessorConfig, HAS_360_SUPPORT
from video_processor.utils.video_360 import Video360Detection, Video360Utils


class TestVideo360Detection:
    """Tests for 360° video detection."""

    def test_aspect_ratio_detection(self):
        """Test 360° detection based on aspect ratio."""
        # Mock metadata for 2:1 aspect ratio (typical 360° video)
        metadata = {
            "video": {
                "width": 3840,
                "height": 1920,
            },
            "filename": "test_video.mp4",
        }
        
        result = Video360Detection.detect_360_video(metadata)
        
        assert result["is_360_video"] is True
        assert "aspect_ratio" in result["detection_methods"]
        assert result["confidence"] >= 0.8

    def test_filename_pattern_detection(self):
        """Test 360° detection based on filename patterns."""
        metadata = {
            "video": {"width": 1920, "height": 1080},
            "filename": "my_360_video.mp4",
        }
        
        result = Video360Detection.detect_360_video(metadata)
        
        assert result["is_360_video"] is True
        assert "filename" in result["detection_methods"]
        assert result["projection_type"] == "equirectangular"

    def test_spherical_metadata_detection(self):
        """Test 360° detection based on spherical metadata."""
        metadata = {
            "video": {"width": 1920, "height": 1080},
            "filename": "test.mp4",
            "format": {
                "tags": {
                    "Spherical": "1",
                    "ProjectionType": "equirectangular"
                }
            }
        }
        
        result = Video360Detection.detect_360_video(metadata)
        
        assert result["is_360_video"] is True
        assert "spherical_metadata" in result["detection_methods"]
        assert result["confidence"] == 1.0
        assert result["projection_type"] == "equirectangular"

    def test_no_360_detection(self):
        """Test that regular videos are not detected as 360°."""
        metadata = {
            "video": {"width": 1920, "height": 1080},
            "filename": "regular_video.mp4",
        }
        
        result = Video360Detection.detect_360_video(metadata)
        
        assert result["is_360_video"] is False
        assert result["confidence"] == 0.0
        assert len(result["detection_methods"]) == 0


class TestVideo360Utils:
    """Tests for 360° video utilities."""

    def test_bitrate_multipliers(self):
        """Test bitrate multipliers for different projection types."""
        assert Video360Utils.get_recommended_bitrate_multiplier("equirectangular") == 2.5
        assert Video360Utils.get_recommended_bitrate_multiplier("cubemap") == 2.0
        assert Video360Utils.get_recommended_bitrate_multiplier("unknown") == 2.0

    def test_optimal_resolutions(self):
        """Test optimal resolution recommendations."""
        equirect_resolutions = Video360Utils.get_optimal_resolutions("equirectangular")
        assert (3840, 1920) in equirect_resolutions  # 4K 360°
        assert (1920, 960) in equirect_resolutions   # 2K 360°

    def test_missing_dependencies(self):
        """Test missing dependency detection."""
        missing = Video360Utils.get_missing_dependencies()
        assert isinstance(missing, list)
        
        # Without optional dependencies, these should be missing
        if not HAS_360_SUPPORT:
            assert "opencv-python" in missing
            assert "py360convert" in missing


class TestProcessorConfig360:
    """Tests for 360° configuration."""

    def test_default_360_settings(self):
        """Test default 360° configuration values."""
        config = ProcessorConfig()
        
        assert config.enable_360_processing == HAS_360_SUPPORT
        assert config.auto_detect_360 is True
        assert config.force_360_projection is None
        assert config.video_360_bitrate_multiplier == 2.5
        assert config.generate_360_thumbnails is True
        assert "front" in config.thumbnail_360_projections
        assert "stereographic" in config.thumbnail_360_projections

    def test_360_validation_without_dependencies(self):
        """Test that 360° processing can't be enabled without dependencies."""
        if not HAS_360_SUPPORT:
            with pytest.raises(ValueError, match="360° processing requires optional dependencies"):
                ProcessorConfig(enable_360_processing=True)

    @pytest.mark.skipif(not HAS_360_SUPPORT, reason="360° dependencies not available")
    def test_360_validation_with_dependencies(self):
        """Test that 360° processing can be enabled with dependencies."""
        config = ProcessorConfig(enable_360_processing=True)
        assert config.enable_360_processing is True

    def test_bitrate_multiplier_validation(self):
        """Test bitrate multiplier validation."""
        # Valid range
        config = ProcessorConfig(video_360_bitrate_multiplier=3.0)
        assert config.video_360_bitrate_multiplier == 3.0
        
        # Invalid range should raise validation error
        with pytest.raises(ValueError):
            ProcessorConfig(video_360_bitrate_multiplier=0.5)  # Below minimum
            
        with pytest.raises(ValueError):
            ProcessorConfig(video_360_bitrate_multiplier=6.0)  # Above maximum

    def test_custom_360_settings(self):
        """Test custom 360° configuration."""
        config = ProcessorConfig(
            auto_detect_360=False,
            video_360_bitrate_multiplier=2.0,
            generate_360_thumbnails=False,
            thumbnail_360_projections=["front", "back"],
        )
        
        assert config.auto_detect_360 is False
        assert config.video_360_bitrate_multiplier == 2.0
        assert config.generate_360_thumbnails is False
        assert config.thumbnail_360_projections == ["front", "back"]


# Integration test for basic video processor
class TestVideoProcessor360Integration:
    """Integration tests for 360° video processing."""

    def test_processor_creation_without_360_support(self):
        """Test that video processor works without 360° support."""
        from video_processor import VideoProcessor
        
        config = ProcessorConfig()  # 360° disabled by default when deps missing
        processor = VideoProcessor(config)
        
        assert processor.thumbnail_360_generator is None

    @pytest.mark.skipif(not HAS_360_SUPPORT, reason="360° dependencies not available") 
    def test_processor_creation_with_360_support(self):
        """Test that video processor works with 360° support."""
        from video_processor import VideoProcessor
        
        config = ProcessorConfig(enable_360_processing=True)
        processor = VideoProcessor(config)
        
        assert processor.thumbnail_360_generator is not None