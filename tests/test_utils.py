"""Tests for utility modules."""

from pathlib import Path

from video_processor.utils.ffmpeg import FFmpegUtils
from video_processor.utils.paths import PathUtils


class TestPathUtils:
    """Tests for PathUtils."""

    def test_generate_video_id(self):
        """Test video ID generation."""
        video_id = PathUtils.generate_video_id()
        assert len(video_id) == 8
        assert video_id.isalnum() or "-" in video_id  # UUID format

        # Test uniqueness
        video_id2 = PathUtils.generate_video_id()
        assert video_id != video_id2

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert PathUtils.sanitize_filename("normal_file.mp4") == "normal_file.mp4"
        assert (
            PathUtils.sanitize_filename("file<with>bad:chars") == "file_with_bad_chars"
        )
        assert PathUtils.sanitize_filename("  .file  ") == "file"
        assert PathUtils.sanitize_filename("") == "untitled"

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert PathUtils.get_file_extension(Path("file.mp4")) == "mp4"
        assert PathUtils.get_file_extension(Path("file.MP4")) == "mp4"
        assert PathUtils.get_file_extension(Path("file")) == ""

    def test_change_extension(self):
        """Test extension changing."""
        original = Path("/path/to/file.mov")
        changed = PathUtils.change_extension(original, "mp4")
        assert changed == Path("/path/to/file.mp4")

        changed_with_dot = PathUtils.change_extension(original, ".webm")
        assert changed_with_dot == Path("/path/to/file.webm")

    def test_is_video_file(self):
        """Test video file detection."""
        assert PathUtils.is_video_file(Path("movie.mp4")) is True
        assert PathUtils.is_video_file(Path("movie.avi")) is True
        assert PathUtils.is_video_file(Path("movie.txt")) is False
        assert PathUtils.is_video_file(Path("image.jpg")) is False

    def test_get_safe_output_path(self, tmp_path):
        """Test safe output path generation."""
        # Test basic path
        path = PathUtils.get_safe_output_path(tmp_path, "video", "mp4", "abc123")
        assert path == tmp_path / "abc123_video.mp4"

        # Test conflict resolution
        (tmp_path / "abc123_video.mp4").touch()
        path = PathUtils.get_safe_output_path(tmp_path, "video", "mp4", "abc123")
        assert path == tmp_path / "abc123_video_1.mp4"


class TestFFmpegUtils:
    """Tests for FFmpegUtils."""

    def test_check_ffmpeg_available(self):
        """Test FFmpeg availability check."""
        # This test might fail in CI/CD without FFmpeg installed
        result = FFmpegUtils.check_ffmpeg_available("/usr/bin/ffmpeg")
        assert isinstance(result, bool)

        # Test with invalid path
        assert FFmpegUtils.check_ffmpeg_available("/invalid/path") is False

    def test_estimate_processing_time(self, tmp_path):
        """Test processing time estimation."""
        # Create a dummy file (this is just testing the calculation logic)
        dummy_file = tmp_path / "dummy.mp4"
        dummy_file.touch()

        # Test with default parameters (will use fallback since file isn't valid)
        time_estimate = FFmpegUtils.estimate_processing_time(
            dummy_file, ["mp4"], "medium"
        )
        assert time_estimate >= 60  # Should return minimum 60 seconds
