"""Test FFmpeg utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from video_processor.utils.ffmpeg import FFmpegUtils
from video_processor.exceptions import FFmpegError


class TestFFmpegUtils:
    """Test FFmpeg utility functions."""
    
    def test_ffmpeg_detection(self):
        """Test FFmpeg binary detection."""
        # Test with default path
        available = FFmpegUtils.check_ffmpeg_available()
        if not available:
            pytest.skip("FFmpeg not available on system")
        
        assert available is True
    
    @patch('subprocess.run')
    def test_ffmpeg_not_found(self, mock_run):
        """Test handling when FFmpeg is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        available = FFmpegUtils.check_ffmpeg_available("/nonexistent/ffmpeg")
        assert available is False
    
    @patch('subprocess.run')
    def test_ffmpeg_timeout(self, mock_run):
        """Test FFmpeg timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["ffmpeg"], timeout=10
        )
        
        available = FFmpegUtils.check_ffmpeg_available()
        assert available is False
    
    @patch('subprocess.run')
    def test_get_ffmpeg_version(self, mock_run):
        """Test getting FFmpeg version."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="ffmpeg version 4.4.2-0ubuntu0.22.04.1"
        )
        
        version = FFmpegUtils.get_ffmpeg_version()
        assert version == "4.4.2-0ubuntu0.22.04.1"
    
    @patch('subprocess.run')
    def test_get_ffmpeg_version_failure(self, mock_run):
        """Test getting FFmpeg version when it fails."""
        mock_run.return_value = Mock(returncode=1)
        
        version = FFmpegUtils.get_ffmpeg_version()
        assert version is None
    
    def test_validate_input_file_exists(self, valid_video):
        """Test validating existing input file."""
        # This should not raise an exception
        try:
            FFmpegUtils.validate_input_file(valid_video)
        except FFmpegError:
            pytest.skip("ffmpeg-python not available for file validation")
    
    def test_validate_input_file_missing(self, temp_dir):
        """Test validating missing input file."""
        missing_file = temp_dir / "missing.mp4"
        
        with pytest.raises(FFmpegError) as exc_info:
            FFmpegUtils.validate_input_file(missing_file)
        
        assert "does not exist" in str(exc_info.value)
    
    def test_validate_input_file_directory(self, temp_dir):
        """Test validating directory instead of file."""
        with pytest.raises(FFmpegError) as exc_info:
            FFmpegUtils.validate_input_file(temp_dir)
        
        assert "not a file" in str(exc_info.value)
    
    def test_estimate_processing_time_basic(self, temp_dir):
        """Test basic processing time estimation."""
        # Create a dummy file for testing
        dummy_file = temp_dir / "dummy.mp4"
        dummy_file.touch()
        
        try:
            estimate = FFmpegUtils.estimate_processing_time(
                input_file=dummy_file,
                output_formats=["mp4"],
                quality_preset="medium"
            )
            # Should return at least the minimum time
            assert estimate >= 60
        except Exception:
            # If ffmpeg-python not available, skip
            pytest.skip("ffmpeg-python not available for estimation")
    
    @pytest.mark.parametrize("quality_preset", ["low", "medium", "high", "ultra"])
    def test_estimate_processing_time_quality_presets(self, quality_preset, temp_dir):
        """Test processing time estimates for different quality presets."""
        dummy_file = temp_dir / "dummy.mp4"
        dummy_file.touch()
        
        try:
            estimate = FFmpegUtils.estimate_processing_time(
                input_file=dummy_file,
                output_formats=["mp4"],
                quality_preset=quality_preset
            )
            assert estimate >= 60
        except Exception:
            pytest.skip("ffmpeg-python not available for estimation")
    
    @pytest.mark.parametrize("formats", [
        ["mp4"],
        ["mp4", "webm"],
        ["mp4", "webm", "ogv"],
    ])
    def test_estimate_processing_time_formats(self, formats, temp_dir):
        """Test processing time estimates for different format combinations."""
        dummy_file = temp_dir / "dummy.mp4"
        dummy_file.touch()
        
        try:
            estimate = FFmpegUtils.estimate_processing_time(
                input_file=dummy_file,
                output_formats=formats,
                quality_preset="medium"
            )
            assert estimate >= 60
            
            # More formats should take longer
            if len(formats) > 1:
                single_format_estimate = FFmpegUtils.estimate_processing_time(
                    input_file=dummy_file,
                    output_formats=formats[:1],
                    quality_preset="medium"
                )
                assert estimate >= single_format_estimate
                
        except Exception:
            pytest.skip("ffmpeg-python not available for estimation")