"""Tests for advanced video encoders (AV1, HEVC, HDR)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from video_processor.config import ProcessorConfig
from video_processor.core.advanced_encoders import AdvancedVideoEncoder, HDRProcessor
from video_processor.exceptions import EncodingError, FFmpegError


class TestAdvancedVideoEncoder:
    """Test advanced video encoder functionality."""

    def test_initialization(self):
        """Test advanced encoder initialization."""
        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        assert encoder.config == config
        assert encoder._quality_presets is not None

    def test_get_advanced_quality_presets(self):
        """Test advanced quality presets configuration."""
        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        presets = encoder._get_advanced_quality_presets()

        assert "low" in presets
        assert "medium" in presets
        assert "high" in presets
        assert "ultra" in presets

        # Check AV1-specific parameters
        assert "av1_crf" in presets["medium"]
        assert "av1_cpu_used" in presets["medium"]
        assert "bitrate_multiplier" in presets["medium"]

    @patch("subprocess.run")
    def test_check_av1_support_available(self, mock_run):
        """Test AV1 support detection when available."""
        # Mock ffmpeg -encoders output with AV1 support
        mock_run.return_value = Mock(
            returncode=0, stdout="... libaom-av1 ... AV1 encoder ...", stderr=""
        )

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        result = encoder._check_av1_support()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_av1_support_unavailable(self, mock_run):
        """Test AV1 support detection when unavailable."""
        # Mock ffmpeg -encoders output without AV1 support
        mock_run.return_value = Mock(
            returncode=0, stdout="libx264 libx265 libvpx-vp9", stderr=""
        )

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        result = encoder._check_av1_support()

        assert result is False

    @patch("subprocess.run")
    def test_check_hardware_hevc_support(self, mock_run):
        """Test hardware HEVC support detection."""
        # Mock ffmpeg -encoders output with hardware HEVC support
        mock_run.return_value = Mock(
            returncode=0, stdout="... hevc_nvenc ... NVIDIA HEVC encoder ...", stderr=""
        )

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        result = encoder._check_hardware_hevc_support()

        assert result is True

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_av1_support"
    )
    @patch("video_processor.core.advanced_encoders.subprocess.run")
    def test_encode_av1_mp4_success(self, mock_run, mock_av1_support):
        """Test successful AV1 MP4 encoding."""
        # Mock AV1 support as available
        mock_av1_support.return_value = True

        # Mock successful subprocess runs for two-pass encoding
        mock_run.side_effect = [
            Mock(returncode=0, stderr=""),  # Pass 1
            Mock(returncode=0, stderr=""),  # Pass 2
        ]

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        # Mock file operations - output file exists, log files don't
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            result = encoder.encode_av1(
                Path("input.mp4"), Path("/output"), "test_id", container="mp4"
            )

        assert result == Path("/output/test_id_av1.mp4")
        assert mock_run.call_count == 2  # Two-pass encoding

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_av1_support"
    )
    def test_encode_av1_no_support(self, mock_av1_support):
        """Test AV1 encoding when support is unavailable."""
        # Mock AV1 support as unavailable
        mock_av1_support.return_value = False

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with pytest.raises(EncodingError, match="AV1 encoding requires libaom-av1"):
            encoder.encode_av1(Path("input.mp4"), Path("/output"), "test_id")

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_av1_support"
    )
    @patch("video_processor.core.advanced_encoders.subprocess.run")
    def test_encode_av1_single_pass(self, mock_run, mock_av1_support):
        """Test AV1 single-pass encoding."""
        mock_av1_support.return_value = True
        mock_run.return_value = Mock(returncode=0, stderr="")

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink"),
        ):
            result = encoder.encode_av1(
                Path("input.mp4"), Path("/output"), "test_id", use_two_pass=False
            )

        assert result == Path("/output/test_id_av1.mp4")
        assert mock_run.call_count == 1  # Single-pass encoding

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_av1_support"
    )
    @patch("video_processor.core.advanced_encoders.subprocess.run")
    def test_encode_av1_webm_container(self, mock_run, mock_av1_support):
        """Test AV1 encoding with WebM container."""
        mock_av1_support.return_value = True
        mock_run.side_effect = [
            Mock(returncode=0, stderr=""),  # Pass 1
            Mock(returncode=0, stderr=""),  # Pass 2
        ]

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink"),
        ):
            result = encoder.encode_av1(
                Path("input.mp4"), Path("/output"), "test_id", container="webm"
            )

        assert result == Path("/output/test_id_av1.webm")

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_av1_support"
    )
    @patch("video_processor.core.advanced_encoders.subprocess.run")
    def test_encode_av1_encoding_failure(self, mock_run, mock_av1_support):
        """Test AV1 encoding failure handling."""
        mock_av1_support.return_value = True
        mock_run.return_value = Mock(returncode=1, stderr="Encoding failed")

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with pytest.raises(FFmpegError, match="AV1 Pass 1 failed"):
            encoder.encode_av1(Path("input.mp4"), Path("/output"), "test_id")

    @patch("subprocess.run")
    def test_encode_hevc_success(self, mock_run):
        """Test successful HEVC encoding."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with patch("pathlib.Path.exists", return_value=True):
            result = encoder.encode_hevc(Path("input.mp4"), Path("/output"), "test_id")

        assert result == Path("/output/test_id_hevc.mp4")

    @patch(
        "video_processor.core.advanced_encoders.AdvancedVideoEncoder._check_hardware_hevc_support"
    )
    @patch("subprocess.run")
    def test_encode_hevc_hardware_fallback(self, mock_run, mock_hw_support):
        """Test HEVC hardware encoding with software fallback."""
        mock_hw_support.return_value = True

        # First call (hardware) fails, second call (software) succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stderr="Hardware encoding failed"),  # Hardware fails
            Mock(returncode=0, stderr=""),  # Software succeeds
        ]

        config = ProcessorConfig()
        encoder = AdvancedVideoEncoder(config)

        with patch("pathlib.Path.exists", return_value=True):
            result = encoder.encode_hevc(
                Path("input.mp4"), Path("/output"), "test_id", use_hardware=True
            )

        assert result == Path("/output/test_id_hevc.mp4")
        assert mock_run.call_count == 2  # Hardware + fallback

    def test_get_av1_bitrate_multiplier(self):
        """Test AV1 bitrate multiplier calculation."""
        config = ProcessorConfig(quality_preset="medium")
        encoder = AdvancedVideoEncoder(config)

        multiplier = encoder.get_av1_bitrate_multiplier()

        assert isinstance(multiplier, float)
        assert 0.5 <= multiplier <= 1.0  # AV1 should use less bitrate

    def test_get_supported_advanced_codecs(self):
        """Test advanced codec support reporting."""
        codecs = AdvancedVideoEncoder.get_supported_advanced_codecs()

        assert isinstance(codecs, dict)
        assert "av1" in codecs
        assert "hevc" in codecs
        assert "hardware_hevc" in codecs


class TestHDRProcessor:
    """Test HDR video processing functionality."""

    def test_initialization(self):
        """Test HDR processor initialization."""
        config = ProcessorConfig()
        processor = HDRProcessor(config)

        assert processor.config == config

    @patch("subprocess.run")
    def test_encode_hdr_hevc_success(self, mock_run):
        """Test successful HDR HEVC encoding."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        config = ProcessorConfig()
        processor = HDRProcessor(config)

        with patch("pathlib.Path.exists", return_value=True):
            result = processor.encode_hdr_hevc(
                Path("input_hdr.mp4"), Path("/output"), "test_id"
            )

        assert result == Path("/output/test_id_hdr_hdr10.mp4")
        mock_run.assert_called_once()

        # Check that HDR parameters were included in the command
        call_args = mock_run.call_args[0][0]
        assert "-color_primaries" in call_args
        assert "bt2020" in call_args

    @patch("subprocess.run")
    def test_encode_hdr_hevc_failure(self, mock_run):
        """Test HDR HEVC encoding failure."""
        mock_run.return_value = Mock(returncode=1, stderr="HDR encoding failed")

        config = ProcessorConfig()
        processor = HDRProcessor(config)

        with pytest.raises(FFmpegError, match="HDR encoding failed"):
            processor.encode_hdr_hevc(Path("input_hdr.mp4"), Path("/output"), "test_id")

    @patch("subprocess.run")
    def test_analyze_hdr_content_hdr_video(self, mock_run):
        """Test HDR content analysis for HDR video."""
        # Mock ffprobe output indicating HDR content
        mock_run.return_value = Mock(returncode=0, stdout="bt2020,smpte2084,bt2020nc\n")

        config = ProcessorConfig()
        processor = HDRProcessor(config)

        result = processor.analyze_hdr_content(Path("hdr_video.mp4"))

        assert result["is_hdr"] is True
        assert result["color_primaries"] == "bt2020"
        assert result["color_transfer"] == "smpte2084"

    @patch("subprocess.run")
    def test_analyze_hdr_content_sdr_video(self, mock_run):
        """Test HDR content analysis for SDR video."""
        # Mock ffprobe output indicating SDR content
        mock_run.return_value = Mock(returncode=0, stdout="bt709,bt709,bt709\n")

        config = ProcessorConfig()
        processor = HDRProcessor(config)

        result = processor.analyze_hdr_content(Path("sdr_video.mp4"))

        assert result["is_hdr"] is False
        assert result["color_primaries"] == "bt709"

    @patch("subprocess.run")
    def test_analyze_hdr_content_failure(self, mock_run):
        """Test HDR content analysis failure handling."""
        mock_run.return_value = Mock(returncode=1, stderr="Analysis failed")

        config = ProcessorConfig()
        processor = HDRProcessor(config)

        result = processor.analyze_hdr_content(Path("video.mp4"))

        assert result["is_hdr"] is False
        assert "error" in result

    def test_get_hdr_support(self):
        """Test HDR support reporting."""
        support = HDRProcessor.get_hdr_support()

        assert isinstance(support, dict)
        assert "hdr10" in support
        assert "hdr10plus" in support
        assert "dolby_vision" in support
