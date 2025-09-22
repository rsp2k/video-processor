#!/usr/bin/env python3
"""
360° Video Processing Integration Tests

This module provides comprehensive integration tests that verify the entire
360° video processing pipeline from analysis to streaming delivery.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_processor.config import ProcessorConfig
from video_processor.video_360 import (
    ProjectionConverter,
    ProjectionType,
    SpatialAudioProcessor,
    SphericalMetadata,
    StereoMode,
    Video360Analysis,
    Video360ProcessingResult,
    Video360Processor,
    Video360StreamProcessor,
    ViewportConfig,
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for integration tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_360_video(temp_workspace):
    """Mock 360° video file."""
    video_file = temp_workspace / "sample_360.mp4"
    video_file.touch()
    return video_file


@pytest.fixture
def processor_config():
    """Standard processor configuration for tests."""
    return ProcessorConfig()


@pytest.fixture
def mock_metadata():
    """Standard spherical metadata for tests."""
    return SphericalMetadata(
        is_spherical=True,
        projection=ProjectionType.EQUIRECTANGULAR,
        stereo_mode=StereoMode.MONO,
        width=3840,
        height=1920,
        has_spatial_audio=True,
    )


class TestEnd2EndWorkflow:
    """Test complete 360° video processing workflows."""

    @pytest.mark.asyncio
    async def test_complete_360_processing_pipeline(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test complete pipeline: analysis → conversion → streaming."""

        with (
            patch(
                "video_processor.video_360.processor.Video360Processor.analyze_360_content"
            ) as mock_analyze,
            patch(
                "video_processor.video_360.conversions.ProjectionConverter.convert_projection"
            ) as mock_convert,
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor.create_360_adaptive_stream"
            ) as mock_stream,
        ):
            # Setup mocks
            mock_analyze.return_value = Video360Analysis(
                metadata=mock_metadata,
                quality=MagicMock(overall_quality=8.5),
                recommended_viewports=[
                    ViewportConfig(0, 0, 90, 60, 1920, 1080),
                    ViewportConfig(180, 0, 90, 60, 1920, 1080),
                ],
            )

            mock_convert.return_value = Video360ProcessingResult(
                success=True,
                output_path=temp_workspace / "converted.mp4",
                processing_time=15.0,
            )

            mock_stream.return_value = MagicMock(
                video_id="test_360",
                bitrate_levels=[],
                hls_playlist=temp_workspace / "playlist.m3u8",
            )

            # Step 1: Analysis
            processor = Video360Processor(processor_config)
            analysis = await processor.analyze_360_content(sample_360_video)

            assert analysis.metadata.is_spherical
            assert analysis.metadata.projection == ProjectionType.EQUIRECTANGULAR
            assert len(analysis.recommended_viewports) == 2

            # Step 2: Projection Conversion
            converter = ProjectionConverter()
            cubemap_result = await converter.convert_projection(
                sample_360_video,
                temp_workspace / "cubemap.mp4",
                ProjectionType.EQUIRECTANGULAR,
                ProjectionType.CUBEMAP,
            )

            assert cubemap_result.success
            assert cubemap_result.processing_time > 0

            # Step 3: Streaming Package
            stream_processor = Video360StreamProcessor(processor_config)
            streaming_package = await stream_processor.create_360_adaptive_stream(
                sample_360_video,
                temp_workspace / "streaming",
                enable_viewport_adaptive=True,
                enable_tiled_streaming=True,
            )

            assert streaming_package.video_id == "test_360"
            assert streaming_package.hls_playlist is not None

            # Verify all mocks were called
            mock_analyze.assert_called_once()
            mock_convert.assert_called_once()
            mock_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_360_quality_optimization_workflow(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test quality analysis and optimization recommendations."""

        with patch(
            "video_processor.video_360.processor.Video360Processor.analyze_360_content"
        ) as mock_analyze:
            # Mock analysis with quality recommendations
            mock_analysis = Video360Analysis(
                metadata=mock_metadata,
                quality=MagicMock(
                    overall_quality=7.5,
                    projection_quality=0.85,
                    pole_distortion=0.38,
                    recommended_bitrate_multiplier=2.5,
                    recommended_projections=[ProjectionType.EAC],
                ),
            )
            mock_analyze.return_value = mock_analysis

            # Analyze video quality
            processor = Video360Processor(processor_config)
            analysis = await processor.analyze_360_content(sample_360_video)

            # Verify quality metrics
            assert analysis.quality.overall_quality > 7.0
            assert analysis.quality.projection_quality > 0.8
            assert len(analysis.quality.recommended_projections) > 0

            # Verify recommendations include projection optimization
            assert ProjectionType.EAC in analysis.quality.recommended_projections

    @pytest.mark.asyncio
    async def test_multi_format_export_workflow(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test exporting 360° video to multiple formats and projections."""

        with patch(
            "video_processor.video_360.conversions.ProjectionConverter.batch_convert_projections"
        ) as mock_batch:
            # Mock batch conversion results
            mock_results = [
                Video360ProcessingResult(
                    success=True,
                    output_path=temp_workspace / f"output_{proj.value}.mp4",
                    processing_time=10.0,
                    output_metadata=SphericalMetadata(projection=proj, is_spherical=True),
                )
                for proj in [
                    ProjectionType.CUBEMAP,
                    ProjectionType.EAC,
                    ProjectionType.STEREOGRAPHIC,
                ]
            ]
            mock_batch.return_value = mock_results

            # Execute batch conversion
            converter = ProjectionConverter()
            results = await converter.batch_convert_projections(
                sample_360_video,
                temp_workspace,
                [
                    ProjectionType.CUBEMAP,
                    ProjectionType.EAC,
                    ProjectionType.STEREOGRAPHIC,
                ],
                parallel=True,
            )

            # Verify all conversions succeeded
            assert len(results) == 3
            assert all(result.success for result in results)
            assert all(result.processing_time > 0 for result in results)

            # Verify different projections were created
            projections = [result.output_metadata.projection for result in results if result.output_metadata]
            assert ProjectionType.CUBEMAP in projections
            assert ProjectionType.EAC in projections
            assert ProjectionType.STEREOGRAPHIC in projections


class TestSpatialAudioIntegration:
    """Test spatial audio processing integration."""

    @pytest.mark.asyncio
    async def test_spatial_audio_pipeline(
        self, temp_workspace, sample_360_video, processor_config
    ):
        """Test complete spatial audio processing pipeline."""

        with (
            patch(
                "video_processor.video_360.spatial_audio.SpatialAudioProcessor.convert_to_binaural"
            ) as mock_binaural,
            patch(
                "video_processor.video_360.spatial_audio.SpatialAudioProcessor.rotate_spatial_audio"
            ) as mock_rotate,
        ):
            # Setup mocks
            mock_binaural.return_value = Video360ProcessingResult(
                success=True,
                output_path=temp_workspace / "binaural.mp4",
                processing_time=8.0,
            )

            mock_rotate.return_value = Video360ProcessingResult(
                success=True,
                output_path=temp_workspace / "rotated.mp4",
                processing_time=5.0,
            )

            # Process spatial audio
            spatial_processor = SpatialAudioProcessor()

            # Convert to binaural
            binaural_result = await spatial_processor.convert_to_binaural(
                sample_360_video, temp_workspace / "binaural.mp4"
            )

            assert binaural_result.success
            assert "binaural" in str(binaural_result.output_path)

            # Rotate spatial audio
            rotated_result = await spatial_processor.rotate_spatial_audio(
                sample_360_video,
                temp_workspace / "rotated.mp4",
                yaw_rotation=45.0,
                pitch_rotation=15.0,
            )

            assert rotated_result.success
            assert "rotated" in str(rotated_result.output_path)


class TestStreamingIntegration:
    """Test 360° streaming integration."""

    @pytest.mark.asyncio
    async def test_adaptive_streaming_creation(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test creation of adaptive streaming packages."""

        with (
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._generate_360_bitrate_ladder"
            ) as mock_ladder,
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._generate_360_renditions"
            ) as mock_renditions,
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._generate_360_hls_playlist"
            ) as mock_hls,
        ):
            # Setup mocks
            mock_ladder.return_value = [
                MagicMock(name="720p", width=2560, height=1280),
                MagicMock(name="1080p", width=3840, height=1920),
            ]

            mock_renditions.return_value = {
                "720p": temp_workspace / "720p.mp4",
                "1080p": temp_workspace / "1080p.mp4",
            }

            mock_hls.return_value = temp_workspace / "playlist.m3u8"

            # Mock the analyze_360_content method
            with patch(
                "video_processor.video_360.processor.Video360Processor.analyze_360_content"
            ) as mock_analyze:
                mock_analyze.return_value = Video360Analysis(
                    metadata=mock_metadata,
                    quality=MagicMock(overall_quality=8.0),
                    supports_tiled_encoding=True
                )

                # Create streaming package
                stream_processor = Video360StreamProcessor(processor_config)
                streaming_package = await stream_processor.create_360_adaptive_stream(
                    sample_360_video,
                    temp_workspace,
                    enable_tiled_streaming=True,
                    streaming_formats=["hls"],
                )

                # Verify package creation
                assert streaming_package.video_id == sample_360_video.stem
                assert streaming_package.metadata.is_spherical
                assert len(streaming_package.bitrate_levels) == 2

    @pytest.mark.asyncio
    async def test_viewport_adaptive_streaming(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test viewport-adaptive streaming features."""

        with (
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._generate_viewport_streams"
            ) as mock_viewports,
            patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._create_viewport_adaptive_manifest"
            ) as mock_manifest,
        ):
            # Setup mocks
            mock_viewports.return_value = {
                "viewport_0": temp_workspace / "viewport_0.mp4",
                "viewport_1": temp_workspace / "viewport_1.mp4",
            }

            mock_manifest.return_value = temp_workspace / "viewport_manifest.json"

            # Mock analysis
            with patch(
                "video_processor.video_360.processor.Video360Processor.analyze_360_content"
            ) as mock_analyze:
                mock_analyze.return_value = Video360Analysis(
                    metadata=mock_metadata,
                    quality=MagicMock(overall_quality=8.0),
                    recommended_viewports=[
                        ViewportConfig(0, 0, 90, 60, 1920, 1080),
                        ViewportConfig(180, 0, 90, 60, 1920, 1080),
                    ],
                )

                # Create viewport-adaptive stream
                stream_processor = Video360StreamProcessor(processor_config)
                streaming_package = await stream_processor.create_360_adaptive_stream(
                    sample_360_video, temp_workspace, enable_viewport_adaptive=True
                )

                # Verify viewport features
                assert streaming_package.viewport_extractions is not None
                assert len(streaming_package.viewport_extractions) == 2
                assert streaming_package.viewport_adaptive_manifest is not None


class TestErrorHandlingIntegration:
    """Test error handling across the 360° processing pipeline."""

    @pytest.mark.asyncio
    async def test_missing_video_handling(self, temp_workspace, processor_config):
        """Test graceful handling of missing video files."""

        missing_video = temp_workspace / "nonexistent.mp4"
        processor = Video360Processor(processor_config)

        # Should handle missing file gracefully
        with pytest.raises(FileNotFoundError):
            await processor.analyze_360_content(missing_video)

    @pytest.mark.asyncio
    async def test_invalid_projection_handling(
        self, temp_workspace, sample_360_video, processor_config
    ):
        """Test handling of invalid projection conversions."""

        converter = ProjectionConverter()

        with patch("subprocess.run") as mock_run:
            # Mock FFmpeg failure
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Invalid projection conversion"
            )

            result = await converter.convert_projection(
                sample_360_video,
                temp_workspace / "output.mp4",
                ProjectionType.EQUIRECTANGULAR,
                ProjectionType.CUBEMAP,
            )

            # Should handle conversion failure gracefully
            assert not result.success
            assert "Invalid projection" in str(result.error_message)

    @pytest.mark.asyncio
    async def test_streaming_fallback_handling(
        self, temp_workspace, sample_360_video, processor_config, mock_metadata
    ):
        """Test streaming fallback when 360° features are unavailable."""

        with patch(
            "video_processor.video_360.processor.Video360Processor.analyze_360_content"
        ) as mock_analyze:
            # Mock non-360° video
            non_360_metadata = SphericalMetadata(
                is_spherical=False, projection=ProjectionType.UNKNOWN
            )
            mock_analyze.return_value = Video360Analysis(
                metadata=non_360_metadata,
                quality=MagicMock(overall_quality=5.0)
            )

            # Should still create streaming package with warning
            stream_processor = Video360StreamProcessor(processor_config)

            with patch(
                "video_processor.video_360.streaming.Video360StreamProcessor._generate_360_bitrate_ladder"
            ) as mock_ladder:
                mock_ladder.return_value = []  # No levels for non-360° content

                streaming_package = await stream_processor.create_360_adaptive_stream(
                    sample_360_video, temp_workspace
                )

                # Should still create package but with fallback behavior
                assert streaming_package.video_id == sample_360_video.stem
                assert not streaming_package.metadata.is_spherical


class TestPerformanceIntegration:
    """Test performance aspects of 360° processing."""

    @pytest.mark.asyncio
    async def test_parallel_processing_efficiency(
        self, temp_workspace, sample_360_video, processor_config
    ):
        """Test parallel processing efficiency for batch operations."""

        with patch(
            "video_processor.video_360.conversions.ProjectionConverter.convert_projection"
        ) as mock_convert:
            # Mock conversion with realistic timing
            async def mock_conversion(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                return Video360ProcessingResult(
                    success=True,
                    output_path=temp_workspace / f"output_{id(args)}.mp4",
                    processing_time=2.0,
                )

            mock_convert.side_effect = mock_conversion

            converter = ProjectionConverter()

            # Test parallel vs sequential timing
            start_time = asyncio.get_event_loop().time()

            results = await converter.batch_convert_projections(
                sample_360_video,
                temp_workspace,
                [
                    ProjectionType.CUBEMAP,
                    ProjectionType.EAC,
                    ProjectionType.STEREOGRAPHIC,
                ],
                parallel=True,
            )

            elapsed_time = asyncio.get_event_loop().time() - start_time

            # Parallel processing should be more efficient than sequential
            assert len(results) == 3
            assert all(result.success for result in results)
            assert elapsed_time < 1.0  # Should complete in parallel, not sequentially


if __name__ == "__main__":
    """Run integration tests directly."""
    pytest.main([__file__, "-v"])
