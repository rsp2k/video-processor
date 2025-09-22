"""Tests for adaptive streaming functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from video_processor.config import ProcessorConfig
from video_processor.streaming.adaptive import (
    AdaptiveStreamProcessor,
    BitrateLevel,
    StreamingPackage,
)


class TestBitrateLevel:
    """Test BitrateLevel dataclass."""

    def test_bitrate_level_creation(self):
        """Test BitrateLevel creation."""
        level = BitrateLevel(
            name="720p",
            width=1280,
            height=720,
            bitrate=3000,
            max_bitrate=4500,
            codec="h264",
            container="mp4",
        )

        assert level.name == "720p"
        assert level.width == 1280
        assert level.height == 720
        assert level.bitrate == 3000
        assert level.max_bitrate == 4500
        assert level.codec == "h264"
        assert level.container == "mp4"


class TestStreamingPackage:
    """Test StreamingPackage dataclass."""

    def test_streaming_package_creation(self):
        """Test StreamingPackage creation."""
        package = StreamingPackage(
            video_id="test_video",
            source_path=Path("input.mp4"),
            output_dir=Path("/output"),
            segment_duration=6,
        )

        assert package.video_id == "test_video"
        assert package.source_path == Path("input.mp4")
        assert package.output_dir == Path("/output")
        assert package.segment_duration == 6
        assert package.hls_playlist is None
        assert package.dash_manifest is None


class TestAdaptiveStreamProcessor:
    """Test adaptive stream processor functionality."""

    def test_initialization(self):
        """Test processor initialization."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        assert processor.config == config
        assert processor.enable_ai_optimization in [
            True,
            False,
        ]  # Depends on AI availability

    def test_initialization_with_ai_disabled(self):
        """Test processor initialization with AI disabled."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config, enable_ai_optimization=False)

        assert processor.enable_ai_optimization is False
        assert processor.content_analyzer is None

    def test_get_streaming_capabilities(self):
        """Test streaming capabilities reporting."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        capabilities = processor.get_streaming_capabilities()

        assert isinstance(capabilities, dict)
        assert "hls_streaming" in capabilities
        assert "dash_streaming" in capabilities
        assert "ai_optimization" in capabilities
        assert "advanced_codecs" in capabilities
        assert "thumbnail_tracks" in capabilities
        assert "multi_bitrate" in capabilities

    def test_get_output_format_mapping(self):
        """Test codec to output format mapping."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        assert processor._get_output_format("h264") == "mp4"
        assert processor._get_output_format("hevc") == "hevc"
        assert processor._get_output_format("av1") == "av1_mp4"
        assert processor._get_output_format("unknown") == "mp4"

    def test_get_quality_preset_for_bitrate(self):
        """Test quality preset selection based on bitrate."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        assert processor._get_quality_preset_for_bitrate(500) == "low"
        assert processor._get_quality_preset_for_bitrate(2000) == "medium"
        assert processor._get_quality_preset_for_bitrate(5000) == "high"
        assert processor._get_quality_preset_for_bitrate(10000) == "ultra"

    def test_get_ffmpeg_options_for_level(self):
        """Test FFmpeg options generation for bitrate levels."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        level = BitrateLevel(
            name="720p",
            width=1280,
            height=720,
            bitrate=3000,
            max_bitrate=4500,
            codec="h264",
            container="mp4",
        )

        options = processor._get_ffmpeg_options_for_level(level)

        assert options["b:v"] == "3000k"
        assert options["maxrate"] == "4500k"
        assert options["bufsize"] == "9000k"
        assert options["s"] == "1280x720"

    @pytest.mark.asyncio
    async def test_generate_optimal_bitrate_ladder_without_ai(self):
        """Test bitrate ladder generation without AI analysis."""
        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config, enable_ai_optimization=False)

        levels = await processor._generate_optimal_bitrate_ladder(Path("test.mp4"))

        assert isinstance(levels, list)
        assert len(levels) >= 1
        assert all(isinstance(level, BitrateLevel) for level in levels)

    @pytest.mark.asyncio
    @patch("video_processor.streaming.adaptive.VideoContentAnalyzer")
    async def test_generate_optimal_bitrate_ladder_with_ai(self, mock_analyzer_class):
        """Test bitrate ladder generation with AI analysis."""
        # Mock AI analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analysis.resolution = (1920, 1080)
        mock_analysis.motion_intensity = 0.8
        mock_analyzer.analyze_content = AsyncMock(return_value=mock_analysis)
        mock_analyzer_class.return_value = mock_analyzer

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config, enable_ai_optimization=True)
        processor.content_analyzer = mock_analyzer

        levels = await processor._generate_optimal_bitrate_ladder(Path("test.mp4"))

        assert isinstance(levels, list)
        assert len(levels) >= 1

        # Check that bitrates were adjusted for high motion
        for level in levels:
            assert level.bitrate > 0
            assert level.max_bitrate > level.bitrate

    @pytest.mark.asyncio
    @patch("video_processor.streaming.adaptive.VideoProcessor")
    @patch("video_processor.streaming.adaptive.asyncio.to_thread")
    async def test_generate_bitrate_renditions(
        self, mock_to_thread, mock_processor_class
    ):
        """Test bitrate rendition generation."""
        # Mock VideoProcessor
        mock_result = Mock()
        mock_result.encoded_files = {"mp4": Path("/output/test.mp4")}
        mock_processor_instance = Mock()
        mock_processor_instance.process_video.return_value = mock_result
        mock_processor_class.return_value = mock_processor_instance
        mock_to_thread.return_value = mock_result

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        bitrate_levels = [
            BitrateLevel("480p", 854, 480, 1500, 2250, "h264", "mp4"),
            BitrateLevel("720p", 1280, 720, 3000, 4500, "h264", "mp4"),
        ]

        with patch("pathlib.Path.mkdir"):
            rendition_files = await processor._generate_bitrate_renditions(
                Path("input.mp4"), Path("/output"), "test_video", bitrate_levels
            )

        assert isinstance(rendition_files, dict)
        assert len(rendition_files) == 2
        assert "480p" in rendition_files
        assert "720p" in rendition_files

    @pytest.mark.asyncio
    @patch("video_processor.streaming.adaptive.asyncio.to_thread")
    async def test_generate_thumbnail_track(self, mock_to_thread):
        """Test thumbnail track generation."""
        # Mock VideoProcessor result
        mock_result = Mock()
        mock_result.sprite_file = Path("/output/sprite.jpg")
        mock_to_thread.return_value = mock_result

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        with patch("video_processor.streaming.adaptive.VideoProcessor"):
            thumbnail_track = await processor._generate_thumbnail_track(
                Path("input.mp4"), Path("/output"), "test_video"
            )

        assert thumbnail_track == Path("/output/sprite.jpg")

    @pytest.mark.asyncio
    @patch("video_processor.streaming.adaptive.asyncio.to_thread")
    async def test_generate_thumbnail_track_failure(self, mock_to_thread):
        """Test thumbnail track generation failure."""
        mock_to_thread.side_effect = Exception("Thumbnail generation failed")

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        with patch("video_processor.streaming.adaptive.VideoProcessor"):
            thumbnail_track = await processor._generate_thumbnail_track(
                Path("input.mp4"), Path("/output"), "test_video"
            )

        assert thumbnail_track is None

    @pytest.mark.asyncio
    @patch(
        "video_processor.streaming.adaptive.AdaptiveStreamProcessor._generate_hls_playlist"
    )
    @patch(
        "video_processor.streaming.adaptive.AdaptiveStreamProcessor._generate_dash_manifest"
    )
    @patch(
        "video_processor.streaming.adaptive.AdaptiveStreamProcessor._generate_thumbnail_track"
    )
    @patch(
        "video_processor.streaming.adaptive.AdaptiveStreamProcessor._generate_bitrate_renditions"
    )
    @patch(
        "video_processor.streaming.adaptive.AdaptiveStreamProcessor._generate_optimal_bitrate_ladder"
    )
    async def test_create_adaptive_stream(
        self, mock_ladder, mock_renditions, mock_thumbnail, mock_dash, mock_hls
    ):
        """Test complete adaptive stream creation."""
        # Setup mocks
        mock_bitrate_levels = [
            BitrateLevel("720p", 1280, 720, 3000, 4500, "h264", "mp4")
        ]
        mock_rendition_files = {"720p": Path("/output/720p.mp4")}

        mock_ladder.return_value = mock_bitrate_levels
        mock_renditions.return_value = mock_rendition_files
        mock_thumbnail.return_value = Path("/output/sprite.jpg")
        mock_hls.return_value = Path("/output/playlist.m3u8")
        mock_dash.return_value = Path("/output/manifest.mpd")

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        with patch("pathlib.Path.mkdir"):
            result = await processor.create_adaptive_stream(
                Path("input.mp4"), Path("/output"), "test_video", ["hls", "dash"]
            )

        assert isinstance(result, StreamingPackage)
        assert result.video_id == "test_video"
        assert result.hls_playlist == Path("/output/playlist.m3u8")
        assert result.dash_manifest == Path("/output/manifest.mpd")
        assert result.thumbnail_track == Path("/output/sprite.jpg")
        assert result.bitrate_levels == mock_bitrate_levels

    @pytest.mark.asyncio
    async def test_create_adaptive_stream_with_custom_ladder(self):
        """Test adaptive stream creation with custom bitrate ladder."""
        custom_levels = [
            BitrateLevel("480p", 854, 480, 1500, 2250, "h264", "mp4"),
        ]

        config = ProcessorConfig()
        processor = AdaptiveStreamProcessor(config)

        with (
            patch.multiple(
                processor,
                _generate_bitrate_renditions=AsyncMock(
                    return_value={"480p": Path("test.mp4")}
                ),
                _generate_hls_playlist=AsyncMock(return_value=Path("playlist.m3u8")),
                _generate_dash_manifest=AsyncMock(return_value=Path("manifest.mpd")),
                _generate_thumbnail_track=AsyncMock(return_value=Path("sprite.jpg")),
            ),
            patch("pathlib.Path.mkdir"),
        ):
            result = await processor.create_adaptive_stream(
                Path("input.mp4"),
                Path("/output"),
                "test_video",
                custom_bitrate_ladder=custom_levels,
            )

        assert result.bitrate_levels == custom_levels
