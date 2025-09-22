"""Tests for AI-enhanced video processor."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from video_processor.ai.content_analyzer import (
    ContentAnalysis,
)
from video_processor.config import ProcessorConfig
from video_processor.core.enhanced_processor import (
    EnhancedVideoProcessingResult,
    EnhancedVideoProcessor,
)


class TestEnhancedVideoProcessor:
    """Test AI-enhanced video processor functionality."""

    def test_initialization_with_ai_enabled(self):
        """Test enhanced processor initialization with AI enabled."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        assert processor.enable_ai is True
        assert processor.content_analyzer is not None

    def test_initialization_with_ai_disabled(self):
        """Test enhanced processor initialization with AI disabled."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=False)

        assert processor.enable_ai is False
        assert processor.content_analyzer is None

    def test_get_ai_capabilities(self):
        """Test AI capabilities reporting."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        capabilities = processor.get_ai_capabilities()

        assert isinstance(capabilities, dict)
        assert "content_analysis" in capabilities
        assert "scene_detection" in capabilities
        assert "quality_assessment" in capabilities
        assert "motion_detection" in capabilities
        assert "smart_thumbnails" in capabilities

    def test_get_missing_ai_dependencies(self):
        """Test missing AI dependencies reporting."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        missing = processor.get_missing_ai_dependencies()
        assert isinstance(missing, list)

    def test_get_missing_ai_dependencies_when_disabled(self):
        """Test missing dependencies when AI is disabled."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=False)

        missing = processor.get_missing_ai_dependencies()
        assert missing == []

    def test_optimize_config_with_no_analysis(self):
        """Test config optimization with no AI analysis."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        optimized = processor._optimize_config_with_ai(None)

        # Should return original config when no analysis
        assert optimized.quality_preset == config.quality_preset
        assert optimized.output_formats == config.output_formats

    def test_optimize_config_with_360_detection(self):
        """Test config optimization with 360° video detection."""
        config = ProcessorConfig()  # Use default config
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock content analysis with 360° detection
        analysis = Mock(spec=ContentAnalysis)
        analysis.is_360_video = True
        analysis.quality_metrics = Mock(overall_quality=0.7)
        analysis.has_motion = False
        analysis.motion_intensity = 0.5
        analysis.duration = 30.0
        analysis.resolution = (1920, 1080)

        optimized = processor._optimize_config_with_ai(analysis)

        # Should have 360° processing attribute (value depends on dependencies)
        assert hasattr(optimized, "enable_360_processing")

    def test_optimize_config_with_low_quality_source(self):
        """Test config optimization with low quality source."""
        config = ProcessorConfig(quality_preset="ultra")
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock low quality analysis
        quality_metrics = Mock()
        quality_metrics.overall_quality = 0.3  # Low quality

        analysis = Mock(spec=ContentAnalysis)
        analysis.is_360_video = False
        analysis.quality_metrics = quality_metrics
        analysis.has_motion = True
        analysis.motion_intensity = 0.5
        analysis.duration = 30.0
        analysis.resolution = (1920, 1080)

        optimized = processor._optimize_config_with_ai(analysis)

        # Should reduce quality preset for low quality source
        assert optimized.quality_preset == "medium"

    def test_optimize_config_with_high_motion(self):
        """Test config optimization with high motion content."""
        config = ProcessorConfig(
            thumbnail_timestamps=[5], generate_sprites=True, sprite_interval=10
        )
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock high motion analysis
        analysis = Mock(spec=ContentAnalysis)
        analysis.is_360_video = False
        analysis.quality_metrics = Mock(overall_quality=0.7)
        analysis.has_motion = True
        analysis.motion_intensity = 0.8  # High motion
        analysis.duration = 60.0
        analysis.resolution = (1920, 1080)

        optimized = processor._optimize_config_with_ai(analysis)

        # Should optimize for high motion
        assert len(optimized.thumbnail_timestamps) >= 3
        assert optimized.sprite_interval <= config.sprite_interval

    def test_backward_compatibility_process_video(self):
        """Test that standard process_video method still works (backward compatibility)."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock the parent class method
        with patch.object(
            processor.__class__.__bases__[0], "process_video"
        ) as mock_parent:
            mock_result = Mock()
            mock_parent.return_value = mock_result

            result = processor.process_video(Path("test.mp4"))

            assert result == mock_result
            mock_parent.assert_called_once_with(Path("test.mp4"), None)


@pytest.mark.asyncio
class TestEnhancedVideoProcessorAsync:
    """Async tests for enhanced video processor."""

    async def test_analyze_content_only(self):
        """Test content-only analysis method."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock the content analyzer
        mock_analysis = Mock(spec=ContentAnalysis)

        with patch.object(
            processor.content_analyzer, "analyze_content", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            result = await processor.analyze_content_only(Path("test.mp4"))

            assert result == mock_analysis
            mock_analyze.assert_called_once_with(Path("test.mp4"))

    async def test_analyze_content_only_with_ai_disabled(self):
        """Test content analysis when AI is disabled."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=False)

        result = await processor.analyze_content_only(Path("test.mp4"))

        assert result is None

    @patch("video_processor.core.enhanced_processor.asyncio.to_thread")
    async def test_process_video_enhanced_without_ai(self, mock_to_thread):
        """Test enhanced processing without AI (fallback to standard)."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=False)

        # Mock standard processing result
        mock_standard_result = Mock()
        mock_standard_result.video_id = "test_id"
        mock_standard_result.input_path = Path("input.mp4")
        mock_standard_result.output_path = Path("/output")
        mock_standard_result.encoded_files = {"mp4": Path("output.mp4")}
        mock_standard_result.thumbnails = [Path("thumb.jpg")]
        mock_standard_result.sprite_file = Path("sprite.jpg")
        mock_standard_result.webvtt_file = Path("sprite.webvtt")
        mock_standard_result.metadata = {}
        mock_standard_result.thumbnails_360 = {}
        mock_standard_result.sprite_360_files = {}

        mock_to_thread.return_value = mock_standard_result

        result = await processor.process_video_enhanced(Path("input.mp4"))

        assert isinstance(result, EnhancedVideoProcessingResult)
        assert result.video_id == "test_id"
        assert result.content_analysis is None
        assert result.smart_thumbnails == []

    @patch("video_processor.core.enhanced_processor.asyncio.to_thread")
    async def test_process_video_enhanced_with_ai_analysis_failure(
        self, mock_to_thread
    ):
        """Test enhanced processing when AI analysis fails."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock content analyzer to raise exception
        with patch.object(
            processor.content_analyzer, "analyze_content", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("AI analysis failed")

            # Mock standard processing result
            mock_standard_result = Mock()
            mock_standard_result.video_id = "test_id"
            mock_standard_result.input_path = Path("input.mp4")
            mock_standard_result.output_path = Path("/output")
            mock_standard_result.encoded_files = {"mp4": Path("output.mp4")}
            mock_standard_result.thumbnails = [Path("thumb.jpg")]
            mock_standard_result.sprite_file = None
            mock_standard_result.webvtt_file = None
            mock_standard_result.metadata = None
            mock_standard_result.thumbnails_360 = {}
            mock_standard_result.sprite_360_files = {}

            mock_to_thread.return_value = mock_standard_result

            # Should not raise exception, should fall back to standard processing
            result = await processor.process_video_enhanced(Path("input.mp4"))

            assert isinstance(result, EnhancedVideoProcessingResult)
            assert result.content_analysis is None

    async def test_generate_smart_thumbnails(self):
        """Test smart thumbnail generation."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock thumbnail generator
        mock_thumbnail_gen = Mock()
        processor.thumbnail_generator = mock_thumbnail_gen

        with patch(
            "video_processor.core.enhanced_processor.asyncio.to_thread"
        ) as mock_to_thread:
            # Mock thumbnail generation results
            mock_to_thread.side_effect = [
                Path("thumb_0.jpg"),
                Path("thumb_1.jpg"),
                Path("thumb_2.jpg"),
            ]

            recommended_timestamps = [10.0, 30.0, 50.0]
            result = await processor._generate_smart_thumbnails(
                Path("input.mp4"), Path("/output"), recommended_timestamps, "test_id"
            )

            assert len(result) == 3
            assert all(isinstance(path, Path) for path in result)
            assert mock_to_thread.call_count == 3

    async def test_generate_smart_thumbnails_failure(self):
        """Test smart thumbnail generation with failure."""
        config = ProcessorConfig()
        processor = EnhancedVideoProcessor(config, enable_ai=True)

        # Mock thumbnail generator
        mock_thumbnail_gen = Mock()
        processor.thumbnail_generator = mock_thumbnail_gen

        with patch(
            "video_processor.core.enhanced_processor.asyncio.to_thread"
        ) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Thumbnail generation failed")

            result = await processor._generate_smart_thumbnails(
                Path("input.mp4"), Path("/output"), [10.0, 30.0], "test_id"
            )

            assert result == []  # Should return empty list on failure


class TestEnhancedVideoProcessingResult:
    """Test enhanced video processing result class."""

    def test_initialization(self):
        """Test enhanced result initialization."""
        mock_analysis = Mock(spec=ContentAnalysis)
        smart_thumbnails = [Path("smart1.jpg"), Path("smart2.jpg")]

        result = EnhancedVideoProcessingResult(
            video_id="test_id",
            input_path=Path("input.mp4"),
            output_path=Path("/output"),
            encoded_files={"mp4": Path("output.mp4")},
            thumbnails=[Path("thumb.jpg")],
            content_analysis=mock_analysis,
            smart_thumbnails=smart_thumbnails,
        )

        assert result.video_id == "test_id"
        assert result.content_analysis == mock_analysis
        assert result.smart_thumbnails == smart_thumbnails

    def test_initialization_with_defaults(self):
        """Test enhanced result with default values."""
        result = EnhancedVideoProcessingResult(
            video_id="test_id",
            input_path=Path("input.mp4"),
            output_path=Path("/output"),
            encoded_files={"mp4": Path("output.mp4")},
            thumbnails=[Path("thumb.jpg")],
        )

        assert result.content_analysis is None
        assert result.smart_thumbnails == []
