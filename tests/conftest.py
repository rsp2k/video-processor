"""Pytest configuration and shared fixtures."""

import asyncio
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from video_processor import ProcessorConfig, VideoProcessor

# Import our testing framework components
from tests.framework.fixtures import VideoTestFixtures
from tests.framework.config import TestingConfig
from tests.framework.quality import QualityMetricsCalculator


# Legacy fixtures (maintained for backward compatibility)
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def default_config(temp_dir: Path) -> ProcessorConfig:
    """Create a default test configuration."""
    return ProcessorConfig(
        base_path=temp_dir,
        output_formats=["mp4", "webm"],
        quality_preset="medium",
        thumbnail_timestamp=1,
        sprite_interval=2.0,
        generate_thumbnails=True,
        generate_sprites=True,
    )


@pytest.fixture
def processor(default_config: ProcessorConfig) -> VideoProcessor:
    """Create a VideoProcessor instance."""
    return VideoProcessor(default_config)


@pytest.fixture
def video_fixtures_dir() -> Path:
    """Path to video fixtures directory."""
    return Path(__file__).parent / "fixtures" / "videos"


@pytest.fixture
def valid_video(video_fixtures_dir: Path) -> Path:
    """Path to a valid test video."""
    video_path = video_fixtures_dir / "valid" / "standard_h264.mp4"
    if not video_path.exists():
        pytest.skip(
            f"Test video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py"
        )
    return video_path


@pytest.fixture
def corrupt_video(video_fixtures_dir: Path) -> Path:
    """Path to a corrupted test video."""
    video_path = video_fixtures_dir / "corrupt" / "bad_header.mp4"
    if not video_path.exists():
        pytest.skip(
            f"Corrupt video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py"
        )
    return video_path


@pytest.fixture
def edge_case_video(video_fixtures_dir: Path) -> Path:
    """Path to an edge case test video."""
    video_path = video_fixtures_dir / "edge_cases" / "one_frame.mp4"
    if not video_path.exists():
        pytest.skip(
            f"Edge case video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py"
        )
    return video_path


@pytest.fixture
async def mock_procrastinate_app():
    """Mock Procrastinate application for testing."""
    app = Mock()
    app.tasks = Mock()
    app.tasks.process_video_async = AsyncMock()
    app.tasks.process_video_async.defer_async = AsyncMock(
        return_value=Mock(id="test-job-123")
    )
    app.tasks.generate_thumbnail_async = AsyncMock()
    app.tasks.generate_thumbnail_async.defer_async = AsyncMock(
        return_value=Mock(id="test-thumbnail-job-456")
    )
    return app


@pytest.fixture
def mock_ffmpeg_success(monkeypatch):
    """Mock successful FFmpeg execution."""

    def mock_run(*args, **kwargs):
        return Mock(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr("subprocess.run", mock_run)


@pytest.fixture
def mock_ffmpeg_failure(monkeypatch):
    """Mock failed FFmpeg execution."""

    def mock_run(*args, **kwargs):
        return Mock(returncode=1, stdout=b"", stderr=b"Error: Invalid input file")

    monkeypatch.setattr("subprocess.run", mock_run)


# Async event loop fixture for async tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Enhanced fixtures from our testing framework
@pytest.fixture
def enhanced_temp_dir() -> Generator[Path, None, None]:
    """Enhanced temporary directory with proper cleanup and structure."""
    return VideoTestFixtures.enhanced_temp_dir()


@pytest.fixture
def video_config(enhanced_temp_dir: Path) -> ProcessorConfig:
    """Enhanced video processor configuration for testing."""
    return VideoTestFixtures.video_config(enhanced_temp_dir)


@pytest.fixture
def enhanced_processor(video_config: ProcessorConfig) -> VideoProcessor:
    """Enhanced video processor with test-specific configurations."""
    return VideoTestFixtures.enhanced_processor(video_config)


@pytest.fixture
def mock_ffmpeg_environment(monkeypatch):
    """Comprehensive FFmpeg mocking environment."""
    return VideoTestFixtures.mock_ffmpeg_environment(monkeypatch)


@pytest.fixture
def test_video_scenarios():
    """Predefined test video scenarios for comprehensive testing."""
    return VideoTestFixtures.test_video_scenarios()


@pytest.fixture
def performance_benchmarks():
    """Performance benchmarks for different video processing operations."""
    return VideoTestFixtures.performance_benchmarks()


@pytest.fixture
def video_360_fixtures():
    """Specialized fixtures for 360° video testing."""
    return VideoTestFixtures.video_360_fixtures()


@pytest.fixture
def ai_analysis_fixtures():
    """Fixtures for AI-powered video analysis testing."""
    return VideoTestFixtures.ai_analysis_fixtures()


@pytest.fixture
def streaming_fixtures():
    """Fixtures for streaming and adaptive bitrate testing."""
    return VideoTestFixtures.streaming_fixtures()


@pytest.fixture
async def async_test_environment():
    """Async environment setup for testing async video processing."""
    return VideoTestFixtures.async_test_environment()


@pytest.fixture
def mock_procrastinate_advanced():
    """Advanced Procrastinate mocking with realistic behavior."""
    return VideoTestFixtures.mock_procrastinate_advanced()


# Framework fixtures (quality_tracker, test_artifacts_dir, video_test_config, video_assert)
# are defined in pytest_plugin.py
# This conftest.py contains legacy fixtures for backward compatibility
