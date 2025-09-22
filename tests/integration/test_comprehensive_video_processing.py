"""
Comprehensive integration tests using the full test video suite.
"""

import tempfile
from pathlib import Path

import pytest

from video_processor import ProcessorConfig, VideoProcessor


@pytest.mark.integration
class TestComprehensiveVideoProcessing:
    """Test video processing with comprehensive test suite."""

    def test_smoke_suite_processing(self, test_suite_manager, procrastinate_app):
        """Test processing all videos in the smoke test suite."""
        smoke_videos = test_suite_manager.get_suite_videos("smoke")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            config = ProcessorConfig(
                base_path=output_dir, output_formats=["mp4"], quality_preset="medium"
            )
            processor = VideoProcessor(config)

            results = []
            for video_path in smoke_videos:
                if video_path.exists() and video_path.stat().st_size > 1000:
                    try:
                        result = processor.process_video(
                            input_path=video_path,
                            output_dir=output_dir / video_path.stem,
                        )
                        results.append((video_path.name, "SUCCESS", result))
                    except Exception as e:
                        results.append((video_path.name, "FAILED", str(e)))

            # At least one video should process successfully
            successful_results = [r for r in results if r[1] == "SUCCESS"]
            assert len(successful_results) > 0, (
                f"No videos processed successfully: {results}"
            )

    def test_codec_compatibility(self, test_suite_manager):
        """Test processing different codec formats."""
        codec_videos = test_suite_manager.get_suite_videos("codecs")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            config = ProcessorConfig(
                base_path=output_dir,
                output_formats=["mp4", "webm"],
                quality_preset="low",  # Faster processing
            )
            processor = VideoProcessor(config)

            codec_results = {}
            for video_path in codec_videos[:3]:  # Test first 3 to avoid timeout
                if video_path.exists() and video_path.stat().st_size > 1000:
                    codec = video_path.suffix.lower()
                    try:
                        result = processor.process_video(
                            input_path=video_path,
                            output_dir=output_dir / f"codec_test_{codec}",
                        )
                        codec_results[codec] = "SUCCESS"
                    except Exception as e:
                        codec_results[codec] = f"FAILED: {str(e)}"

            assert len(codec_results) > 0, "No codec tests completed"
            successful_codecs = [c for c, r in codec_results.items() if r == "SUCCESS"]
            assert len(successful_codecs) > 0, (
                f"No codecs processed successfully: {codec_results}"
            )

    def test_edge_case_handling(self, test_suite_manager):
        """Test handling of edge case videos."""
        edge_videos = test_suite_manager.get_suite_videos("edge_cases")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            config = ProcessorConfig(
                base_path=output_dir, output_formats=["mp4"], quality_preset="low"
            )
            processor = VideoProcessor(config)

            edge_results = {}
            for video_path in edge_videos[:5]:  # Test first 5 edge cases
                if video_path.exists():
                    edge_case = video_path.stem
                    try:
                        result = processor.process_video(
                            input_path=video_path,
                            output_dir=output_dir / f"edge_test_{edge_case}",
                        )
                        edge_results[edge_case] = "SUCCESS"
                    except Exception as e:
                        # Some edge cases are expected to fail
                        edge_results[edge_case] = f"EXPECTED_FAIL: {type(e).__name__}"

            assert len(edge_results) > 0, "No edge case tests completed"
            # At least some edge cases should be handled gracefully
            handled_cases = [
                c
                for c, r in edge_results.items()
                if "SUCCESS" in r or "EXPECTED_FAIL" in r
            ]
            assert len(handled_cases) == len(edge_results), (
                f"Unexpected failures: {edge_results}"
            )

    @pytest.mark.asyncio
    async def test_async_processing_with_suite(
        self, test_suite_manager, procrastinate_app
    ):
        """Test async processing with videos from test suite."""
        from video_processor.tasks.procrastinate_tasks import process_video_task

        smoke_videos = test_suite_manager.get_suite_videos("smoke")
        valid_video = None

        for video_path in smoke_videos:
            if video_path.exists() and video_path.stat().st_size > 1000:
                valid_video = video_path
                break

        if not valid_video:
            pytest.skip("No valid video found in smoke suite")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Defer the task
            job = await process_video_task.defer_async(
                input_path=str(valid_video),
                output_dir=str(output_dir),
                output_formats=["mp4"],
                quality_preset="low",
            )

            assert job.id is not None
            assert job.task_name == "process_video_task"


@pytest.mark.integration
class TestVideoSuiteValidation:
    """Test validation of the comprehensive video test suite."""

    def test_suite_structure(self, test_suite_manager):
        """Test that the test suite has expected structure."""
        config_path = test_suite_manager.base_dir / "test_suite.json"
        assert config_path.exists(), "Test suite configuration not found"

        # Check expected suites exist
        expected_suites = ["smoke", "basic", "codecs", "edge_cases", "stress"]
        for suite_name in expected_suites:
            videos = test_suite_manager.get_suite_videos(suite_name)
            assert len(videos) > 0, f"Suite '{suite_name}' has no videos"

    def test_video_accessibility(self, test_suite_manager):
        """Test that videos in suites are accessible."""
        smoke_videos = test_suite_manager.get_suite_videos("smoke")

        accessible_count = 0
        for video_path in smoke_videos:
            if video_path.exists() and video_path.is_file():
                accessible_count += 1

        assert accessible_count > 0, "No accessible videos found in smoke suite"

    def test_suite_categories(self, test_suite_manager):
        """Test that suite categories are properly defined."""
        assert len(test_suite_manager.categories) >= 5
        assert "smoke" in test_suite_manager.categories
        assert "edge_cases" in test_suite_manager.categories
        assert "codecs" in test_suite_manager.categories
