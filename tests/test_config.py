"""Tests for configuration module."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from video_processor.config import ProcessorConfig


def test_default_config():
    """Test default configuration values."""
    config = ProcessorConfig()

    assert config.storage_backend == "local"
    assert config.output_formats == ["mp4"]
    assert config.quality_preset == "medium"
    assert config.thumbnail_timestamps == [1]
    assert config.generate_sprites is True


def test_config_validation():
    """Test configuration validation."""
    # Test empty output formats
    with pytest.raises(ValidationError):
        ProcessorConfig(output_formats=[])

    # Test valid formats
    config = ProcessorConfig(output_formats=["mp4", "webm", "ogv"])
    assert len(config.output_formats) == 3


def test_base_path_resolution():
    """Test base path is resolved to absolute path."""
    relative_path = Path("relative/path")
    config = ProcessorConfig(base_path=relative_path)

    assert config.base_path.is_absolute()


def test_custom_config():
    """Test custom configuration values."""
    config = ProcessorConfig(
        storage_backend="local",
        base_path=Path("/custom/path"),
        output_formats=["mp4", "webm"],
        quality_preset="high",
        thumbnail_timestamps=[1, 30, 60],
        generate_sprites=False,
    )

    assert config.storage_backend == "local"
    assert config.base_path == Path("/custom/path").resolve()
    assert config.output_formats == ["mp4", "webm"]
    assert config.quality_preset == "high"
    assert config.thumbnail_timestamps == [1, 30, 60]
    assert config.generate_sprites is False
