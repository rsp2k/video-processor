"""Video processing specific test fixtures and utilities."""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Generator, Any
from unittest.mock import Mock, AsyncMock
import pytest

from video_processor import ProcessorConfig, VideoProcessor
from .quality import QualityMetricsCalculator


@pytest.fixture
def quality_tracker(request) -> QualityMetricsCalculator:
    """Fixture to track test quality metrics."""
    test_name = request.node.name
    tracker = QualityMetricsCalculator(test_name)
    yield tracker

    # Finalize and save metrics
    metrics = tracker.finalize()
    # In a real implementation, you'd save to database here
    # For now, we'll store in test metadata
    request.node.quality_metrics = metrics


@pytest.fixture
def enhanced_temp_dir() -> Generator[Path, None, None]:
    """Enhanced temporary directory with proper cleanup and structure."""
    temp_path = Path(tempfile.mkdtemp(prefix="video_test_"))

    # Create standard directory structure
    (temp_path / "input").mkdir()
    (temp_path / "output").mkdir()
    (temp_path / "thumbnails").mkdir()
    (temp_path / "sprites").mkdir()
    (temp_path / "logs").mkdir()

    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def video_config(enhanced_temp_dir: Path) -> ProcessorConfig:
    """Enhanced video processor configuration for testing."""
    return ProcessorConfig(
        base_path=enhanced_temp_dir,
        output_formats=["mp4", "webm"],
        quality_preset="medium",
        thumbnail_timestamp=1,
        sprite_interval=2.0,
        generate_thumbnails=True,
        generate_sprites=True,
    )


@pytest.fixture
def enhanced_processor(video_config: ProcessorConfig) -> VideoProcessor:
    """Enhanced video processor with test-specific configurations."""
    processor = VideoProcessor(video_config)
    # Add test-specific hooks or mocks here if needed
    return processor


@pytest.fixture
def mock_ffmpeg_environment(monkeypatch):
    """Comprehensive FFmpeg mocking environment."""

    def mock_run_success(*args, **kwargs):
        return Mock(returncode=0, stdout=b"", stderr=b"frame=100 fps=30")

    def mock_run_failure(*args, **kwargs):
        return Mock(returncode=1, stdout=b"", stderr=b"Error: Invalid codec")

    def mock_probe_success(*args, **kwargs):
        return {
            'streams': [
                {
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080,
                    'duration': '10.0',
                    'bit_rate': '5000000'
                }
            ]
        }

    # Default to success, can be overridden in specific tests
    monkeypatch.setattr("subprocess.run", mock_run_success)
    monkeypatch.setattr("ffmpeg.probe", mock_probe_success)

    return {
        "success": mock_run_success,
        "failure": mock_run_failure,
        "probe": mock_probe_success
    }


@pytest.fixture
def test_video_scenarios() -> Dict[str, Dict[str, Any]]:
    """Predefined test video scenarios for comprehensive testing."""
    return {
        "standard_hd": {
            "name": "Standard HD Video",
            "resolution": "1920x1080",
            "duration": 10.0,
            "codec": "h264",
            "expected_outputs": ["mp4", "webm"],
            "quality_threshold": 8.0
        },
        "short_clip": {
            "name": "Short Video Clip",
            "resolution": "1280x720",
            "duration": 2.0,
            "codec": "h264",
            "expected_outputs": ["mp4"],
            "quality_threshold": 7.5
        },
        "high_bitrate": {
            "name": "High Bitrate Video",
            "resolution": "3840x2160",
            "duration": 5.0,
            "codec": "h265",
            "expected_outputs": ["mp4", "webm"],
            "quality_threshold": 9.0
        },
        "edge_case_dimensions": {
            "name": "Odd Dimensions",
            "resolution": "1921x1081",
            "duration": 3.0,
            "codec": "h264",
            "expected_outputs": ["mp4"],
            "quality_threshold": 6.0
        }
    }


@pytest.fixture
def performance_benchmarks() -> Dict[str, Dict[str, float]]:
    """Performance benchmarks for different video processing operations."""
    return {
        "encoding": {
            "h264_720p": 15.0,  # fps
            "h264_1080p": 8.0,
            "h265_720p": 6.0,
            "h265_1080p": 3.0,
            "webm_720p": 12.0,
            "webm_1080p": 6.0
        },
        "thumbnails": {
            "generation_time_720p": 0.5,  # seconds
            "generation_time_1080p": 1.0,
            "generation_time_4k": 2.0
        },
        "sprites": {
            "creation_time_per_minute": 2.0,  # seconds
            "max_sprite_size_mb": 5.0
        }
    }


@pytest.fixture
def video_360_fixtures() -> Dict[str, Any]:
    """Specialized fixtures for 360° video testing."""
    return {
        "equirectangular": {
            "projection": "equirectangular",
            "fov": 360,
            "resolution": "4096x2048",
            "expected_processing_time": 30.0
        },
        "cubemap": {
            "projection": "cubemap",
            "face_size": 1024,
            "expected_faces": 6,
            "processing_complexity": "high"
        },
        "stereoscopic": {
            "stereo_mode": "top_bottom",
            "eye_separation": 65,  # mm
            "depth_maps": True
        }
    }


@pytest.fixture
def ai_analysis_fixtures() -> Dict[str, Any]:
    """Fixtures for AI-powered video analysis testing."""
    return {
        "scene_detection": {
            "min_scene_duration": 2.0,
            "confidence_threshold": 0.8,
            "expected_scenes": [
                {"start": 0.0, "end": 5.0, "type": "indoor"},
                {"start": 5.0, "end": 10.0, "type": "outdoor"}
            ]
        },
        "object_tracking": {
            "min_object_size": 50,  # pixels
            "tracking_confidence": 0.7,
            "max_objects_per_frame": 10
        },
        "quality_assessment": {
            "sharpness_threshold": 0.6,
            "noise_threshold": 0.3,
            "compression_artifacts": 0.2
        }
    }


@pytest.fixture
def streaming_fixtures() -> Dict[str, Any]:
    """Fixtures for streaming and adaptive bitrate testing."""
    return {
        "adaptive_streams": {
            "resolutions": ["360p", "720p", "1080p"],
            "bitrates": [800, 2500, 5000],  # kbps
            "segment_duration": 4.0,  # seconds
            "playlist_type": "vod"
        },
        "live_streaming": {
            "latency_target": 3.0,  # seconds
            "buffer_size": 6.0,  # seconds
            "keyframe_interval": 2.0
        }
    }


@pytest.fixture
async def async_test_environment():
    """Async environment setup for testing async video processing."""
    # Setup async environment
    tasks = []
    try:
        yield {
            "loop": asyncio.get_event_loop(),
            "tasks": tasks,
            "semaphore": asyncio.Semaphore(4)  # Limit concurrent operations
        }
    finally:
        # Cleanup any remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


@pytest.fixture
def mock_procrastinate_advanced():
    """Advanced Procrastinate mocking with realistic behavior."""

    class MockJob:
        def __init__(self, job_id: str, status: str = "todo"):
            self.id = job_id
            self.status = status
            self.result = None
            self.exception = None

    class MockApp:
        def __init__(self):
            self.jobs = {}
            self.task_counter = 0

        async def defer_async(self, task_name: str, **kwargs) -> MockJob:
            self.task_counter += 1
            job_id = f"test-job-{self.task_counter}"
            job = MockJob(job_id)
            self.jobs[job_id] = job

            # Simulate async processing
            await asyncio.sleep(0.1)
            job.status = "succeeded"
            job.result = {"processed": True, "output_path": "/test/output.mp4"}

            return job

        async def get_job_status(self, job_id: str) -> str:
            return self.jobs.get(job_id, MockJob("unknown", "failed")).status

    return MockApp()


# For backward compatibility, create a class that holds these fixtures
class VideoTestFixtures:
    """Legacy class for accessing fixtures."""

    @staticmethod
    def enhanced_temp_dir():
        return enhanced_temp_dir()

    @staticmethod
    def video_config(enhanced_temp_dir):
        return video_config(enhanced_temp_dir)

    @staticmethod
    def enhanced_processor(video_config):
        return enhanced_processor(video_config)

    @staticmethod
    def mock_ffmpeg_environment(monkeypatch):
        return mock_ffmpeg_environment(monkeypatch)

    @staticmethod
    def test_video_scenarios():
        return test_video_scenarios()

    @staticmethod
    def performance_benchmarks():
        return performance_benchmarks()

    @staticmethod
    def video_360_fixtures():
        return video_360_fixtures()

    @staticmethod
    def ai_analysis_fixtures():
        return ai_analysis_fixtures()

    @staticmethod
    def streaming_fixtures():
        return streaming_fixtures()

    @staticmethod
    def async_test_environment():
        return async_test_environment()

    @staticmethod
    def mock_procrastinate_advanced():
        return mock_procrastinate_advanced()

    @staticmethod
    def quality_tracker(request):
        return quality_tracker(request)


# Export commonly used fixtures for easy import
__all__ = [
    "VideoTestFixtures",
    "enhanced_temp_dir",
    "video_config",
    "enhanced_processor",
    "mock_ffmpeg_environment",
    "test_video_scenarios",
    "performance_benchmarks",
    "video_360_fixtures",
    "ai_analysis_fixtures",
    "streaming_fixtures",
    "async_test_environment",
    "mock_procrastinate_advanced",
    "quality_tracker"
]