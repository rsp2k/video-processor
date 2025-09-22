"""Tests for AI content analyzer."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from video_processor.ai.content_analyzer import (
    ContentAnalysis,
    QualityMetrics,
    SceneAnalysis,
    VideoContentAnalyzer,
)


class TestVideoContentAnalyzer:
    """Test AI content analysis functionality."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = VideoContentAnalyzer()
        assert analyzer is not None

    def test_analyzer_without_opencv(self):
        """Test analyzer behavior when OpenCV is not available."""
        analyzer = VideoContentAnalyzer(enable_opencv=False)
        assert not analyzer.enable_opencv

    def test_is_analysis_available_method(self):
        """Test analysis availability check."""
        # This will depend on whether OpenCV is actually installed
        result = VideoContentAnalyzer.is_analysis_available()
        assert isinstance(result, bool)

    def test_get_missing_dependencies(self):
        """Test missing dependencies reporting."""
        missing = VideoContentAnalyzer.get_missing_dependencies()
        assert isinstance(missing, list)

    @patch("video_processor.ai.content_analyzer.ffmpeg.probe")
    async def test_get_video_metadata(self, mock_probe):
        """Test video metadata extraction."""
        # Mock FFmpeg probe response
        mock_probe.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "30.0",
                }
            ],
            "format": {"duration": "30.0"},
        }

        analyzer = VideoContentAnalyzer()
        metadata = await analyzer._get_video_metadata(Path("test.mp4"))

        assert metadata["streams"][0]["width"] == 1920
        assert metadata["streams"][0]["height"] == 1080
        mock_probe.assert_called_once()

    @patch("video_processor.ai.content_analyzer.ffmpeg.probe")
    @patch("video_processor.ai.content_analyzer.ffmpeg.input")
    async def test_analyze_scenes_fallback(self, mock_input, mock_probe):
        """Test scene analysis with fallback when FFmpeg scene detection fails."""
        # Mock FFmpeg probe
        mock_probe.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "60.0",
                }
            ],
            "format": {"duration": "60.0"},
        }

        # Mock FFmpeg process that fails
        mock_process = Mock()
        mock_process.communicate.return_value = (b"", b"error output")
        mock_input.return_value.filter.return_value.filter.return_value.output.return_value.run_async.return_value = mock_process

        analyzer = VideoContentAnalyzer()
        scenes = await analyzer._analyze_scenes(Path("test.mp4"), 60.0)

        assert isinstance(scenes, SceneAnalysis)
        assert scenes.scene_count > 0
        assert len(scenes.scene_boundaries) >= 0
        assert len(scenes.key_moments) > 0

    def test_parse_scene_boundaries(self):
        """Test parsing scene boundaries from FFmpeg output."""
        analyzer = VideoContentAnalyzer()

        # Mock FFmpeg showinfo output
        ffmpeg_output = """
        [Parsed_showinfo_1 @ 0x123] n:0 pts:0 pts_time:0.000000 pos:123 fmt:yuv420p
        [Parsed_showinfo_1 @ 0x123] n:1 pts:1024 pts_time:10.240000 pos:456 fmt:yuv420p
        [Parsed_showinfo_1 @ 0x123] n:2 pts:2048 pts_time:20.480000 pos:789 fmt:yuv420p
        """

        boundaries = analyzer._parse_scene_boundaries(ffmpeg_output)

        assert len(boundaries) == 3
        assert 0.0 in boundaries
        assert 10.24 in boundaries
        assert 20.48 in boundaries

    def test_generate_fallback_scenes(self):
        """Test fallback scene generation."""
        analyzer = VideoContentAnalyzer()

        # Short video
        boundaries = analyzer._generate_fallback_scenes(20.0)
        assert len(boundaries) == 0

        # Medium video
        boundaries = analyzer._generate_fallback_scenes(90.0)
        assert len(boundaries) == 1

        # Long video
        boundaries = analyzer._generate_fallback_scenes(300.0)
        assert len(boundaries) > 1
        assert len(boundaries) <= 10  # Max 10 scenes

    def test_fallback_quality_assessment(self):
        """Test fallback quality assessment."""
        analyzer = VideoContentAnalyzer()
        quality = analyzer._fallback_quality_assessment()

        assert isinstance(quality, QualityMetrics)
        assert 0 <= quality.sharpness_score <= 1
        assert 0 <= quality.brightness_score <= 1
        assert 0 <= quality.contrast_score <= 1
        assert 0 <= quality.noise_level <= 1
        assert 0 <= quality.overall_quality <= 1

    def test_detect_360_video_by_metadata(self):
        """Test 360° video detection by metadata."""
        analyzer = VideoContentAnalyzer()

        # Mock probe info with spherical metadata
        probe_info_360 = {
            "format": {"tags": {"spherical": "1", "ProjectionType": "equirectangular"}},
            "streams": [{"codec_type": "video", "width": 3840, "height": 1920}],
        }

        is_360 = analyzer._detect_360_video(probe_info_360)
        assert is_360

    def test_detect_360_video_by_aspect_ratio(self):
        """Test 360° video detection by aspect ratio."""
        analyzer = VideoContentAnalyzer()

        # Mock probe info with 2:1 aspect ratio
        probe_info_2to1 = {
            "format": {"tags": {}},
            "streams": [{"codec_type": "video", "width": 3840, "height": 1920}],
        }

        is_360 = analyzer._detect_360_video(probe_info_2to1)
        assert is_360

        # Mock probe info with normal aspect ratio
        probe_info_normal = {
            "format": {"tags": {}},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
        }

        is_360 = analyzer._detect_360_video(probe_info_normal)
        assert not is_360

    def test_recommend_thumbnails(self):
        """Test thumbnail recommendation logic."""
        analyzer = VideoContentAnalyzer()

        # Create mock scene analysis
        scenes = SceneAnalysis(
            scene_boundaries=[10.0, 20.0, 30.0],
            scene_count=4,
            average_scene_length=10.0,
            key_moments=[5.0, 15.0, 25.0],
            confidence_scores=[0.8, 0.9, 0.7],
        )

        # Create mock quality metrics
        quality = QualityMetrics(
            sharpness_score=0.8,
            brightness_score=0.5,
            contrast_score=0.7,
            noise_level=0.2,
            overall_quality=0.7,
        )

        recommendations = analyzer._recommend_thumbnails(scenes, quality, 60.0)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert len(recommendations) <= 5  # Max 5 recommendations
        assert all(isinstance(t, (int, float)) for t in recommendations)

    def test_parse_motion_data(self):
        """Test motion data parsing."""
        analyzer = VideoContentAnalyzer()

        # Mock FFmpeg motion output with multiple frames
        motion_output = """
        [Parsed_showinfo_1 @ 0x123] n:0 pts:0 pts_time:0.000000 pos:123 fmt:yuv420p
        [Parsed_showinfo_1 @ 0x123] n:1 pts:1024 pts_time:1.024000 pos:456 fmt:yuv420p
        [Parsed_showinfo_1 @ 0x123] n:2 pts:2048 pts_time:2.048000 pos:789 fmt:yuv420p
        """

        motion_data = analyzer._parse_motion_data(motion_output)

        assert "intensity" in motion_data
        assert 0 <= motion_data["intensity"] <= 1


@pytest.mark.asyncio
class TestVideoContentAnalyzerIntegration:
    """Integration tests for video content analyzer."""

    @patch("video_processor.ai.content_analyzer.ffmpeg.probe")
    @patch("video_processor.ai.content_analyzer.ffmpeg.input")
    async def test_analyze_content_full_pipeline(self, mock_input, mock_probe):
        """Test full content analysis pipeline."""
        # Mock FFmpeg probe response
        mock_probe.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "30.0",
                }
            ],
            "format": {"duration": "30.0", "tags": {}},
        }

        # Mock FFmpeg scene detection process
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"scene output"))
        mock_input.return_value.filter.return_value.filter.return_value.output.return_value.run_async.return_value = mock_process

        # Mock motion detection process
        mock_motion_process = Mock()
        mock_motion_process.communicate = AsyncMock(
            return_value=(b"", b"motion output")
        )

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_process.communicate.return_value

            analyzer = VideoContentAnalyzer()
            result = await analyzer.analyze_content(Path("test.mp4"))

            assert isinstance(result, ContentAnalysis)
            assert result.duration == 30.0
            assert result.resolution == (1920, 1080)
            assert isinstance(result.scenes, SceneAnalysis)
            assert isinstance(result.quality_metrics, QualityMetrics)
            assert isinstance(result.has_motion, bool)
            assert isinstance(result.is_360_video, bool)
            assert isinstance(result.recommended_thumbnails, list)
