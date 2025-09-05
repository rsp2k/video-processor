"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, AsyncMock

from video_processor import VideoProcessor, ProcessorConfig


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
        generate_sprites=True
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
        pytest.skip(f"Test video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py")
    return video_path


@pytest.fixture
def corrupt_video(video_fixtures_dir: Path) -> Path:
    """Path to a corrupted test video."""
    video_path = video_fixtures_dir / "corrupt" / "bad_header.mp4"
    if not video_path.exists():
        pytest.skip(f"Corrupt video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py")
    return video_path


@pytest.fixture
def edge_case_video(video_fixtures_dir: Path) -> Path:
    """Path to an edge case test video."""
    video_path = video_fixtures_dir / "edge_cases" / "one_frame.mp4" 
    if not video_path.exists():
        pytest.skip(f"Edge case video not found: {video_path}. Run: python tests/fixtures/generate_fixtures.py")
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
        return Mock(
            returncode=1,
            stdout=b"",
            stderr=b"Error: Invalid input file"
        )
    
    monkeypatch.setattr("subprocess.run", mock_run)


# Async event loop fixture for async tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"  
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_ffmpeg: marks tests that require FFmpeg"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )