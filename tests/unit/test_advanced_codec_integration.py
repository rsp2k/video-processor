"""Tests for advanced codec integration with main VideoProcessor."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from video_processor.config import ProcessorConfig
from video_processor.core.encoders import VideoEncoder
from video_processor.exceptions import EncodingError


class TestAdvancedCodecIntegration:
    """Test integration of advanced codecs with main video processor."""

    def test_av1_format_recognition(self):
        """Test that VideoEncoder recognizes AV1 formats."""
        config = ProcessorConfig(output_formats=["av1_mp4", "av1_webm"])
        encoder = VideoEncoder(config)

        # Test format recognition
        with patch.object(encoder, "_encode_av1_mp4", return_value=Path("output.mp4")):
            result = encoder.encode_video(
                Path("input.mp4"), Path("/output"), "av1_mp4", "test_id"
            )
            assert result == Path("output.mp4")

    def test_hevc_format_recognition(self):
        """Test that VideoEncoder recognizes HEVC format."""
        config = ProcessorConfig(output_formats=["hevc"])
        encoder = VideoEncoder(config)

        with patch.object(encoder, "_encode_hevc_mp4", return_value=Path("output.mp4")):
            result = encoder.encode_video(
                Path("input.mp4"), Path("/output"), "hevc", "test_id"
            )
            assert result == Path("output.mp4")

    @patch("video_processor.core.advanced_encoders.AdvancedVideoEncoder")
    def test_av1_mp4_integration(self, mock_advanced_encoder_class):
        """Test AV1 MP4 encoding integration."""
        # Mock the AdvancedVideoEncoder
        mock_encoder_instance = Mock()
        mock_encoder_instance.encode_av1.return_value = Path("/output/test.mp4")
        mock_advanced_encoder_class.return_value = mock_encoder_instance

        config = ProcessorConfig()
        encoder = VideoEncoder(config)

        result = encoder._encode_av1_mp4(Path("input.mp4"), Path("/output"), "test")

        # Verify AdvancedVideoEncoder was instantiated with config
        mock_advanced_encoder_class.assert_called_once_with(config)

        # Verify encode_av1 was called with correct parameters
        mock_encoder_instance.encode_av1.assert_called_once_with(
            Path("input.mp4"), Path("/output"), "test", container="mp4"
        )

        assert result == Path("/output/test.mp4")

    @patch("video_processor.core.advanced_encoders.AdvancedVideoEncoder")
    def test_av1_webm_integration(self, mock_advanced_encoder_class):
        """Test AV1 WebM encoding integration."""
        mock_encoder_instance = Mock()
        mock_encoder_instance.encode_av1.return_value = Path("/output/test.webm")
        mock_advanced_encoder_class.return_value = mock_encoder_instance

        config = ProcessorConfig()
        encoder = VideoEncoder(config)

        result = encoder._encode_av1_webm(Path("input.mp4"), Path("/output"), "test")

        mock_encoder_instance.encode_av1.assert_called_once_with(
            Path("input.mp4"), Path("/output"), "test", container="webm"
        )

        assert result == Path("/output/test.webm")

    @patch("video_processor.core.advanced_encoders.AdvancedVideoEncoder")
    def test_hevc_integration(self, mock_advanced_encoder_class):
        """Test HEVC encoding integration."""
        mock_encoder_instance = Mock()
        mock_encoder_instance.encode_hevc.return_value = Path("/output/test.mp4")
        mock_advanced_encoder_class.return_value = mock_encoder_instance

        config = ProcessorConfig()
        encoder = VideoEncoder(config)

        result = encoder._encode_hevc_mp4(Path("input.mp4"), Path("/output"), "test")

        mock_encoder_instance.encode_hevc.assert_called_once_with(
            Path("input.mp4"), Path("/output"), "test"
        )

        assert result == Path("/output/test.mp4")

    def test_unsupported_format_error(self):
        """Test error handling for unsupported formats."""
        config = ProcessorConfig()
        encoder = VideoEncoder(config)

        with pytest.raises(EncodingError, match="Unsupported format: unsupported"):
            encoder.encode_video(
                Path("input.mp4"), Path("/output"), "unsupported", "test_id"
            )

    def test_config_validation_with_advanced_codecs(self):
        """Test configuration validation with advanced codec options."""
        # Test valid advanced codec configuration
        config = ProcessorConfig(
            output_formats=["mp4", "av1_mp4", "hevc"],
            enable_av1_encoding=True,
            enable_hevc_encoding=True,
            av1_cpu_used=6,
            prefer_two_pass_av1=True,
        )

        assert config.output_formats == ["mp4", "av1_mp4", "hevc"]
        assert config.enable_av1_encoding is True
        assert config.enable_hevc_encoding is True
        assert config.av1_cpu_used == 6

    def test_config_av1_cpu_used_validation(self):
        """Test AV1 CPU used parameter validation."""
        # Valid range
        config = ProcessorConfig(av1_cpu_used=4)
        assert config.av1_cpu_used == 4

        # Test edge cases
        config_min = ProcessorConfig(av1_cpu_used=0)
        assert config_min.av1_cpu_used == 0

        config_max = ProcessorConfig(av1_cpu_used=8)
        assert config_max.av1_cpu_used == 8

        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            ProcessorConfig(av1_cpu_used=-1)

        with pytest.raises(ValueError):
            ProcessorConfig(av1_cpu_used=9)
