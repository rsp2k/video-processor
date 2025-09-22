#!/usr/bin/env python3
"""
Comprehensive tests for 360° video processing.

This test suite implements the detailed testing scenarios from the 360° video
testing specification, covering projection conversions, viewport extraction,
stereoscopic processing, and spatial audio functionality.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from video_processor import ProcessorConfig, VideoProcessor
from video_processor.exceptions import VideoProcessorError
from video_processor.video_360 import (
    ProjectionConverter,
    ProjectionType,
    SpatialAudioProcessor,
    SphericalMetadata,
    StereoMode,
    Video360Processor,
    Video360StreamProcessor,
    ViewportConfig,
)
from video_processor.video_360.models import SpatialAudioType


class Test360VideoDetection:
    """Test 360° video detection capabilities."""

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

        from video_processor.utils.video_360 import Video360Detection

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

        from video_processor.utils.video_360 import Video360Detection

        result = Video360Detection.detect_360_video(metadata)

        assert result["is_360_video"] is True
        assert "filename" in result["detection_methods"]
        assert result["projection_type"] == "equirectangular"

    def test_spherical_metadata_detection(self):
        """Test 360° detection based on spherical metadata."""
        metadata = {
            "video": {"width": 1920, "height": 1080},
            "filename": "test.mp4",
            "format": {"tags": {"Spherical": "1", "ProjectionType": "equirectangular"}},
        }

        from video_processor.utils.video_360 import Video360Detection

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

        from video_processor.utils.video_360 import Video360Detection

        result = Video360Detection.detect_360_video(metadata)

        assert result["is_360_video"] is False
        assert result["confidence"] == 0.0
        assert len(result["detection_methods"]) == 0


class TestProjectionConversions:
    """Test projection conversion capabilities."""

    @pytest.fixture
    def projection_converter(self):
        """Create projection converter instance."""
        return ProjectionConverter()

    @pytest.fixture
    def mock_360_video(self, tmp_path):
        """Create mock 360° video file."""
        video_file = tmp_path / "test_360.mp4"
        video_file.touch()  # Create empty file for testing
        return video_file

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "target_projection",
        [
            ProjectionType.CUBEMAP,
            ProjectionType.EAC,
            ProjectionType.STEREOGRAPHIC,
            ProjectionType.FISHEYE,
            ProjectionType.FLAT,
        ],
    )
    async def test_projection_conversion(
        self, projection_converter, mock_360_video, tmp_path, target_projection
    ):
        """Test converting between different projections."""
        output_video = tmp_path / f"converted_{target_projection.value}.mp4"

        with patch("asyncio.to_thread") as mock_thread:
            # Mock successful FFmpeg execution
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_thread.return_value = mock_result

            # Mock file size
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1000000  # 1MB

                result = await projection_converter.convert_projection(
                    mock_360_video,
                    output_video,
                    ProjectionType.EQUIRECTANGULAR,
                    target_projection,
                    output_resolution=(2048, 1024),
                )

        assert result.success
        assert result.output_path == output_video

    @pytest.mark.asyncio
    async def test_cubemap_layout_conversion(
        self, projection_converter, mock_360_video, tmp_path
    ):
        """Test converting between different cubemap layouts."""
        layouts = ["3x2", "6x1", "1x6", "2x3"]

        with patch("asyncio.to_thread") as mock_thread:
            # Mock successful FFmpeg execution
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_thread.return_value = mock_result

            results = await projection_converter.create_cubemap_layouts(
                mock_360_video, tmp_path, ProjectionType.EQUIRECTANGULAR
            )

        assert len(results) == 4
        for layout in layouts:
            assert layout in results
            assert results[layout].success

    @pytest.mark.asyncio
    async def test_batch_projection_conversion(
        self, projection_converter, mock_360_video, tmp_path
    ):
        """Test batch conversion to multiple projections."""
        target_projections = [
            ProjectionType.CUBEMAP,
            ProjectionType.STEREOGRAPHIC,
            ProjectionType.FISHEYE,
        ]

        with patch("asyncio.to_thread") as mock_thread:
            # Mock successful FFmpeg execution
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_thread.return_value = mock_result

            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1000000

                results = await projection_converter.batch_convert_projections(
                    mock_360_video,
                    tmp_path,
                    ProjectionType.EQUIRECTANGULAR,
                    target_projections,
                )

        assert len(results) == len(target_projections)
        for projection in target_projections:
            assert projection in results
            assert results[projection].success


class TestViewportExtraction:
    """Test viewport extraction from 360° videos."""

    @pytest.fixture
    def video360_processor(self):
        """Create 360° video processor."""
        config = ProcessorConfig()
        return Video360Processor(config)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "yaw,pitch,roll,fov",
        [
            (0, 0, 0, 90),  # Front view
            (90, 0, 0, 90),  # Right view
            (180, 0, 0, 90),  # Back view
            (270, 0, 0, 90),  # Left view
            (0, 90, 0, 90),  # Top view
            (0, -90, 0, 90),  # Bottom view
            (45, 30, 0, 120),  # Wide FOV diagonal view
            (0, 0, 0, 60),  # Narrow FOV
        ],
    )
    async def test_viewport_extraction(
        self, video360_processor, tmp_path, yaw, pitch, roll, fov
    ):
        """Test extracting fixed viewports from 360° video."""
        input_video = tmp_path / "input_360.mp4"
        output_video = tmp_path / f"viewport_y{yaw}_p{pitch}_r{roll}_fov{fov}.mp4"
        input_video.touch()

        viewport_config = ViewportConfig(
            yaw=yaw, pitch=pitch, roll=roll, fov=fov, width=1920, height=1080
        )

        with patch.object(
            video360_processor, "extract_spherical_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = SphericalMetadata(
                is_spherical=True,
                projection=ProjectionType.EQUIRECTANGULAR,
                width=3840,
                height=1920,
            )

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await video360_processor.extract_viewport(
                        input_video, output_video, viewport_config
                    )

        assert result.success
        assert result.output_path == output_video
        assert result.output_metadata.projection == ProjectionType.FLAT

    @pytest.mark.asyncio
    async def test_animated_viewport_extraction(self, video360_processor, tmp_path):
        """Test extracting animated/moving viewport."""
        input_video = tmp_path / "input_360.mp4"
        output_video = tmp_path / "animated_viewport.mp4"
        input_video.touch()

        # Define viewport animation (pan from left to right)
        def viewport_animation(t: float) -> tuple:
            """Return yaw, pitch, roll, fov for time t."""
            yaw = -180 + (360 * t / 5.0)  # Full rotation in 5 seconds
            pitch = 20 * np.sin(2 * np.pi * t / 3)  # Oscillate pitch
            roll = 0
            fov = 90 + 30 * np.sin(2 * np.pi * t / 4)  # Zoom in/out
            return yaw, pitch, roll, fov

        with patch.object(video360_processor, "_get_video_duration") as mock_duration:
            mock_duration.return_value = 5.0

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await video360_processor.extract_animated_viewport(
                        input_video, output_video, viewport_animation
                    )

        assert result.success
        assert result.output_path == output_video


class TestStereoscopicProcessing:
    """Test stereoscopic 360° video processing."""

    @pytest.fixture
    def video360_processor(self):
        config = ProcessorConfig()
        return Video360Processor(config)

    @pytest.mark.asyncio
    async def test_stereo_to_mono_conversion(self, video360_processor, tmp_path):
        """Test converting stereoscopic to monoscopic."""
        input_video = tmp_path / "stereo_tb.mp4"
        output_video = tmp_path / "mono_from_stereo.mp4"
        input_video.touch()

        with patch.object(
            video360_processor, "extract_spherical_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = SphericalMetadata(
                is_spherical=True,
                projection=ProjectionType.EQUIRECTANGULAR,
                stereo_mode=StereoMode.TOP_BOTTOM,
                width=3840,
                height=3840,
            )

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await video360_processor.stereo_to_mono(
                        input_video, output_video, eye="left"
                    )

        assert result.success
        assert result.output_metadata.stereo_mode == StereoMode.MONO

    @pytest.mark.asyncio
    async def test_stereo_mode_conversion(self, video360_processor, tmp_path):
        """Test converting between stereo modes (TB to SBS)."""
        input_video = tmp_path / "stereo_tb.mp4"
        output_video = tmp_path / "stereo_sbs_from_tb.mp4"
        input_video.touch()

        with patch.object(
            video360_processor, "extract_spherical_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = SphericalMetadata(
                is_spherical=True,
                projection=ProjectionType.EQUIRECTANGULAR,
                stereo_mode=StereoMode.TOP_BOTTOM,
                width=3840,
                height=3840,
            )

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await video360_processor.convert_stereo_mode(
                        input_video, output_video, StereoMode.LEFT_RIGHT
                    )

        assert result.success
        assert result.output_metadata.stereo_mode == StereoMode.LEFT_RIGHT


class TestSpatialAudioProcessing:
    """Test spatial audio processing capabilities."""

    @pytest.fixture
    def spatial_audio_processor(self):
        return SpatialAudioProcessor()

    @pytest.mark.asyncio
    async def test_ambisonic_audio_detection(self, spatial_audio_processor, tmp_path):
        """Test detection of ambisonic spatial audio."""
        video_path = tmp_path / "ambisonic_bformat.mp4"
        video_path.touch()

        with patch("asyncio.to_thread") as mock_thread:
            # Mock ffprobe output with ambisonic metadata
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps(
                {
                    "streams": [
                        {
                            "codec_type": "audio",
                            "channels": 4,
                            "tags": {"ambisonic": "1", "channel_layout": "quad"},
                        }
                    ]
                }
            )
            mock_thread.return_value = mock_result

            audio_type = await spatial_audio_processor.detect_spatial_audio(video_path)

        assert audio_type == SpatialAudioType.AMBISONIC_BFORMAT

    @pytest.mark.asyncio
    async def test_spatial_audio_rotation(self, spatial_audio_processor, tmp_path):
        """Test rotating spatial audio with video."""
        input_video = tmp_path / "ambisonic_bformat.mp4"
        output_video = tmp_path / "rotated_spatial_audio.mp4"
        input_video.touch()

        with patch.object(
            spatial_audio_processor, "detect_spatial_audio"
        ) as mock_detect:
            mock_detect.return_value = SpatialAudioType.AMBISONIC_BFORMAT

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await spatial_audio_processor.rotate_spatial_audio(
                        input_video, output_video, yaw_rotation=90
                    )

        assert result.success

    @pytest.mark.asyncio
    async def test_binaural_conversion(self, spatial_audio_processor, tmp_path):
        """Test converting spatial audio to binaural."""
        input_video = tmp_path / "ambisonic.mp4"
        output_video = tmp_path / "binaural.mp4"
        input_video.touch()

        with patch.object(
            spatial_audio_processor, "detect_spatial_audio"
        ) as mock_detect:
            mock_detect.return_value = SpatialAudioType.AMBISONIC_BFORMAT

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 1000000

                    result = await spatial_audio_processor.convert_to_binaural(
                        input_video, output_video
                    )

        assert result.success

    @pytest.mark.asyncio
    async def test_ambisonic_channel_extraction(
        self, spatial_audio_processor, tmp_path
    ):
        """Test extracting individual ambisonic channels."""
        input_video = tmp_path / "ambisonic.mp4"
        output_dir = tmp_path / "channels"
        output_dir.mkdir()
        input_video.touch()

        with patch.object(
            spatial_audio_processor, "detect_spatial_audio"
        ) as mock_detect:
            mock_detect.return_value = SpatialAudioType.AMBISONIC_BFORMAT

            with patch("asyncio.to_thread") as mock_thread:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_thread.return_value = mock_result

                # Mock channel files creation
                for channel in ["W", "X", "Y", "Z"]:
                    (output_dir / f"channel_{channel}.wav").touch()

                channels = await spatial_audio_processor.extract_ambisonic_channels(
                    input_video, output_dir
                )

        assert len(channels) == 4
        assert "W" in channels
        assert "X" in channels
        assert "Y" in channels
        assert "Z" in channels


class Test360Streaming:
    """Test 360° adaptive streaming capabilities."""

    @pytest.fixture
    def stream_processor(self):
        config = ProcessorConfig()
        return Video360StreamProcessor(config)

    @pytest.mark.asyncio
    async def test_360_adaptive_streaming(self, stream_processor, tmp_path):
        """Test creating 360° adaptive streaming package."""
        input_video = tmp_path / "test_360.mp4"
        output_dir = tmp_path / "streaming_output"
        input_video.touch()

        # Mock the analysis
        with patch.object(
            stream_processor.video360_processor, "analyze_360_content"
        ) as mock_analyze:
            from video_processor.video_360.models import (
                Video360Analysis,
                Video360Quality,
            )

            mock_analysis = Video360Analysis(
                metadata=SphericalMetadata(
                    is_spherical=True,
                    projection=ProjectionType.EQUIRECTANGULAR,
                    width=3840,
                    height=1920,
                ),
                quality=Video360Quality(motion_intensity=0.5),
                supports_tiled_encoding=True,
                supports_viewport_adaptive=True,
            )
            mock_analyze.return_value = mock_analysis

            # Mock rendition generation
            with patch.object(
                stream_processor, "_generate_360_renditions"
            ) as mock_renditions:
                mock_renditions.return_value = {
                    "720p": tmp_path / "720p.mp4",
                    "1080p": tmp_path / "1080p.mp4",
                }

                # Mock manifest generation
                with patch.object(
                    stream_processor, "_generate_360_hls_playlist"
                ) as mock_hls:
                    mock_hls.return_value = tmp_path / "playlist.m3u8"

                    with patch.object(
                        stream_processor, "_generate_360_dash_manifest"
                    ) as mock_dash:
                        mock_dash.return_value = tmp_path / "manifest.mpd"

                        # Mock other components
                        with patch.object(
                            stream_processor, "_generate_viewport_streams"
                        ) as mock_viewports:
                            mock_viewports.return_value = {}

                            with patch.object(
                                stream_processor, "_generate_projection_thumbnails"
                            ) as mock_thumbs:
                                mock_thumbs.return_value = {}

                                with patch.object(
                                    stream_processor, "_generate_spatial_audio_tracks"
                                ) as mock_audio:
                                    mock_audio.return_value = {}

                                    streaming_package = await stream_processor.create_360_adaptive_stream(
                                        input_video,
                                        output_dir,
                                        "test_360",
                                        streaming_formats=["hls", "dash"],
                                    )

        assert streaming_package.video_id == "test_360"
        assert streaming_package.metadata.is_spherical
        assert streaming_package.hls_playlist is not None
        assert streaming_package.dash_manifest is not None

    @pytest.mark.asyncio
    async def test_viewport_adaptive_streaming(self, stream_processor, tmp_path):
        """Test viewport-adaptive streaming generation."""
        input_video = tmp_path / "test_360.mp4"
        output_dir = tmp_path / "streaming_output"
        input_video.touch()

        # Custom viewport configurations
        custom_viewports = [
            ViewportConfig(yaw=0, pitch=0, fov=90),  # Front
            ViewportConfig(yaw=90, pitch=0, fov=90),  # Right
            ViewportConfig(yaw=180, pitch=0, fov=90),  # Back
        ]

        # Mock analysis and processing similar to above
        with patch.object(
            stream_processor.video360_processor, "analyze_360_content"
        ) as mock_analyze:
            from video_processor.video_360.models import (
                Video360Analysis,
                Video360Quality,
            )

            mock_analysis = Video360Analysis(
                metadata=SphericalMetadata(
                    is_spherical=True,
                    projection=ProjectionType.EQUIRECTANGULAR,
                    width=3840,
                    height=1920,
                ),
                quality=Video360Quality(motion_intensity=0.5),
                supports_viewport_adaptive=True,
            )
            mock_analyze.return_value = mock_analysis

            with patch.object(
                stream_processor, "_generate_360_renditions"
            ) as mock_renditions:
                mock_renditions.return_value = {"720p": tmp_path / "720p.mp4"}

                with patch.object(
                    stream_processor, "_generate_viewport_streams"
                ) as mock_viewports:
                    mock_viewports.return_value = {
                        "viewport_0": tmp_path / "viewport_0.mp4",
                        "viewport_1": tmp_path / "viewport_1.mp4",
                        "viewport_2": tmp_path / "viewport_2.mp4",
                    }

                    with patch.object(
                        stream_processor, "_create_viewport_adaptive_manifest"
                    ) as mock_manifest:
                        mock_manifest.return_value = tmp_path / "viewport_adaptive.json"

                        # Mock other methods
                        with patch.object(
                            stream_processor, "_generate_360_hls_playlist"
                        ):
                            with patch.object(
                                stream_processor, "_generate_projection_thumbnails"
                            ):
                                with patch.object(
                                    stream_processor, "_generate_spatial_audio_tracks"
                                ):
                                    streaming_package = await stream_processor.create_360_adaptive_stream(
                                        input_video,
                                        output_dir,
                                        "test_360",
                                        enable_viewport_adaptive=True,
                                        custom_viewports=custom_viewports,
                                    )

        assert streaming_package.supports_viewport_adaptive
        assert len(streaming_package.viewport_extractions) == 3


class TestAIIntegration:
    """Test AI-enhanced 360° content analysis."""

    @pytest.mark.asyncio
    async def test_360_content_analysis(self, tmp_path):
        """Test AI analysis of 360° video content."""
        from video_processor.ai.content_analyzer import VideoContentAnalyzer

        video_path = tmp_path / "test_360.mp4"
        video_path.touch()

        analyzer = VideoContentAnalyzer()

        # Mock the video metadata
        with patch("ffmpeg.probe") as mock_probe:
            mock_probe.return_value = {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 3840,
                        "height": 1920,
                    }
                ],
                "format": {
                    "duration": "10.0",
                    "tags": {"Spherical": "1", "ProjectionType": "equirectangular"},
                },
            }

            # Mock FFmpeg processes
            with patch("ffmpeg.input") as mock_input:
                mock_process = Mock()
                mock_process.communicate = Mock(return_value=(b"", b"scene boundaries"))

                mock_filter_chain = Mock()
                mock_filter_chain.run_async.return_value = mock_process
                mock_filter_chain.output.return_value = mock_filter_chain
                mock_filter_chain.filter.return_value = mock_filter_chain

                mock_input.return_value = mock_filter_chain

                with patch("asyncio.to_thread") as mock_thread:
                    mock_thread.return_value = (b"", b"scene info")

                    analysis = await analyzer.analyze_content(video_path)

        assert analysis.is_360_video is True
        assert analysis.video_360 is not None
        assert analysis.video_360.projection_type == "equirectangular"
        assert len(analysis.video_360.optimal_viewport_points) > 0
        assert len(analysis.video_360.recommended_projections) > 0


class TestIntegration:
    """Integration tests for complete 360° video processing pipeline."""

    @pytest.mark.asyncio
    async def test_full_360_pipeline(self, tmp_path):
        """Test complete 360° video processing pipeline."""
        input_video = tmp_path / "test_360.mp4"
        input_video.touch()

        config = ProcessorConfig(
            base_path=tmp_path,
            output_formats=["mp4"],
            quality_preset="medium",
            enable_360_processing=True,
            enable_ai_analysis=True,
        )

        # Mock the processor components
        with patch(
            "video_processor.core.processor.VideoProcessor.process_video"
        ) as mock_process:
            from video_processor.core.processor import ProcessingResult

            mock_result = ProcessingResult(
                video_id="test_360",
                encoded_files={"mp4": tmp_path / "output.mp4"},
                metadata={
                    "video_360": {
                        "is_360_video": True,
                        "projection_type": "equirectangular",
                        "confidence": 0.9,
                    }
                },
            )
            mock_process.return_value = mock_result

            processor = VideoProcessor(config)
            result = processor.process_video(input_video, "test_360")

        assert result.video_id == "test_360"
        assert "mp4" in result.encoded_files
        assert result.metadata["video_360"]["is_360_video"] is True

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_360_processing_performance(self, tmp_path, benchmark):
        """Benchmark 360° video processing performance."""
        input_video = tmp_path / "benchmark_360.mp4"
        input_video.touch()

        config = ProcessorConfig(enable_360_processing=True)
        processor = Video360Processor(config)

        async def process_viewport():
            viewport_config = ViewportConfig(yaw=0, pitch=0, roll=0, fov=90)

            with patch.object(processor, "extract_spherical_metadata") as mock_metadata:
                mock_metadata.return_value = SphericalMetadata(
                    is_spherical=True, projection=ProjectionType.EQUIRECTANGULAR
                )

                with patch("asyncio.to_thread") as mock_thread:
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_thread.return_value = mock_result

                    with patch.object(Path, "stat") as mock_stat:
                        mock_stat.return_value.st_size = 1000000

                        output = tmp_path / "benchmark_output.mp4"
                        await processor.extract_viewport(
                            input_video, output, viewport_config
                        )

        # Run benchmark
        result = benchmark(asyncio.run, process_viewport())

        # Performance assertions (these would need to be calibrated based on actual performance)
        # assert result.stats['mean'] < 10.0  # Should complete in < 10 seconds


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def video360_processor(self):
        config = ProcessorConfig()
        return Video360Processor(config)

    @pytest.mark.asyncio
    async def test_missing_metadata_handling(self, video360_processor, tmp_path):
        """Test handling of 360° video without metadata."""
        video_path = tmp_path / "no_metadata_360.mp4"
        video_path.touch()

        with patch("asyncio.to_thread") as mock_thread:
            # Mock ffprobe output without spherical metadata
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps(
                {
                    "streams": [{"codec_type": "video", "width": 3840, "height": 1920}],
                    "format": {"tags": {}},
                }
            )
            mock_thread.return_value = mock_result

            metadata = await video360_processor.extract_spherical_metadata(video_path)

        # Should infer 360° from aspect ratio
        assert metadata.width == 3840
        assert metadata.height == 1920
        aspect_ratio = metadata.width / metadata.height
        if abs(aspect_ratio - 2.0) < 0.1:
            assert metadata.is_spherical

    @pytest.mark.asyncio
    async def test_invalid_viewport_config(self, video360_processor, tmp_path):
        """Test handling of invalid viewport configuration."""
        input_video = tmp_path / "test.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        # Invalid viewport (FOV too high)
        invalid_viewport = ViewportConfig(yaw=0, pitch=0, roll=0, fov=200)

        with pytest.raises(VideoProcessorError):
            await video360_processor.extract_viewport(
                input_video, output_video, invalid_viewport
            )

    @pytest.mark.asyncio
    async def test_unsupported_projection_fallback(self):
        """Test fallback for unsupported projections."""
        converter = ProjectionConverter()

        # Test that all projections in the enum are supported
        supported = converter.get_supported_projections()
        assert ProjectionType.EQUIRECTANGULAR in supported
        assert ProjectionType.CUBEMAP in supported
        assert ProjectionType.FLAT in supported


# Utility functions for test data generation
def create_mock_spherical_metadata(
    projection=ProjectionType.EQUIRECTANGULAR,
    stereo_mode=StereoMode.MONO,
    width=3840,
    height=1920,
) -> SphericalMetadata:
    """Create mock spherical metadata for testing."""
    return SphericalMetadata(
        is_spherical=True,
        projection=projection,
        stereo_mode=stereo_mode,
        width=width,
        height=height,
        aspect_ratio=width / height,
        confidence=0.9,
        detection_methods=["metadata"],
    )


def create_mock_viewport_config(yaw=0, pitch=0, fov=90) -> ViewportConfig:
    """Create mock viewport configuration for testing."""
    return ViewportConfig(
        yaw=yaw, pitch=pitch, roll=0, fov=fov, width=1920, height=1080
    )


# Test configuration for different test suites
test_suites = {
    "quick": [
        "Test360VideoDetection::test_aspect_ratio_detection",
        "TestProjectionConversions::test_projection_conversion",
        "TestViewportExtraction::test_viewport_extraction",
    ],
    "projections": [
        "TestProjectionConversions",
    ],
    "stereoscopic": [
        "TestStereoscopicProcessing",
    ],
    "spatial_audio": [
        "TestSpatialAudioProcessing",
    ],
    "streaming": [
        "Test360Streaming",
    ],
    "performance": [
        "TestIntegration::test_360_processing_performance",
    ],
    "edge_cases": [
        "TestEdgeCases",
    ],
}


if __name__ == "__main__":
    # Allow running specific test suites
    import sys

    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        if suite_name in test_suites:
            # Run specific suite
            test_args = ["-v"] + [f"-k {test}" for test in test_suites[suite_name]]
            pytest.main(test_args)
        else:
            print(f"Unknown test suite: {suite_name}")
            print(f"Available suites: {list(test_suites.keys())}")
    else:
        # Run all tests
        pytest.main(["-v", __file__])
