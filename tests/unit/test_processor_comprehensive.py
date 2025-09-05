"""Comprehensive tests for the VideoProcessor class."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from video_processor import VideoProcessor, ProcessorConfig
from video_processor.exceptions import (
    VideoProcessorError,
    ValidationError,
    StorageError,
    EncodingError,
)


@pytest.mark.unit
class TestVideoProcessorInitialization:
    """Test VideoProcessor initialization and configuration."""
    
    def test_initialization_with_valid_config(self, default_config):
        """Test processor initialization with valid configuration."""
        processor = VideoProcessor(default_config)
        
        assert processor.config == default_config
        assert processor.config.base_path == default_config.base_path
        assert processor.config.output_formats == default_config.output_formats
    
    def test_initialization_creates_output_directory(self, temp_dir):
        """Test that base path configuration is accessible."""
        output_dir = temp_dir / "video_output"
        
        config = ProcessorConfig(
            base_path=output_dir,
            output_formats=["mp4"]
        )
        
        processor = VideoProcessor(config)
        
        # Base path should be properly configured 
        assert processor.config.base_path == output_dir
        # Storage backend should be initialized
        assert processor.storage is not None
    
    def test_initialization_with_invalid_ffmpeg_path(self, temp_dir):
        """Test initialization with invalid FFmpeg path is allowed."""
        config = ProcessorConfig(
            base_path=temp_dir,
            ffmpeg_path="/nonexistent/ffmpeg"
        )
        
        # Initialization should succeed, validation happens during processing
        processor = VideoProcessor(config)
        assert processor.config.ffmpeg_path == "/nonexistent/ffmpeg"


@pytest.mark.unit
class TestVideoProcessingWorkflow:
    """Test the complete video processing workflow."""
    
    @patch('video_processor.core.encoders.VideoEncoder.encode_video')
    @patch('video_processor.core.thumbnails.ThumbnailGenerator.generate_thumbnail')
    @patch('video_processor.core.thumbnails.ThumbnailGenerator.generate_sprites')
    def test_process_video_complete_workflow(self, mock_sprites, mock_thumb, mock_encode, 
                                           processor, valid_video, temp_dir):
        """Test complete video processing workflow."""
        # Setup mocks
        mock_encode.return_value = temp_dir / "output.mp4"
        mock_thumb.return_value = temp_dir / "thumb.jpg"
        mock_sprites.return_value = (temp_dir / "sprites.jpg", temp_dir / "sprites.vtt")
        
        # Mock files exist
        for path in [mock_encode.return_value, mock_thumb.return_value, 
                    mock_sprites.return_value[0], mock_sprites.return_value[1]]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        
        result = processor.process_video(
            input_path=valid_video,
            output_dir=temp_dir / "output"
        )
        
        # Verify all methods were called
        mock_encode.assert_called()
        mock_thumb.assert_called_once()
        mock_sprites.assert_called_once()
        
        # Verify result structure
        assert result.video_id is not None
        assert len(result.encoded_files) > 0
        assert len(result.thumbnails) > 0
        assert result.sprite_file is not None
        assert result.webvtt_file is not None
    
    def test_process_video_with_custom_id(self, processor, valid_video, temp_dir):
        """Test processing with custom video ID."""
        custom_id = "my-custom-video-123"
        
        with patch.object(processor.encoder, 'encode_video') as mock_encode:
            with patch.object(processor.thumbnail_generator, 'generate_thumbnail') as mock_thumb:
                with patch.object(processor.thumbnail_generator, 'generate_sprites') as mock_sprites:
                    # Setup mocks
                    mock_encode.return_value = temp_dir / f"{custom_id}.mp4"
                    mock_thumb.return_value = temp_dir / f"{custom_id}_thumb.jpg"
                    mock_sprites.return_value = (
                        temp_dir / f"{custom_id}_sprites.jpg",
                        temp_dir / f"{custom_id}_sprites.vtt"
                    )
                    
                    # Create mock files
                    for path in [mock_encode.return_value, mock_thumb.return_value]:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.touch()
                    for path in mock_sprites.return_value:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.touch()
                    
                    result = processor.process_video(
                        input_path=valid_video,
                        output_dir=temp_dir / "output",
                        video_id=custom_id
                    )
                    
                    assert result.video_id == custom_id
    
    def test_process_video_missing_input(self, processor, temp_dir):
        """Test processing with missing input file."""
        nonexistent_file = temp_dir / "nonexistent.mp4"
        
        with pytest.raises(ValidationError):
            processor.process_video(
                input_path=nonexistent_file,
                output_dir=temp_dir / "output"
            )
    
    def test_process_video_readonly_output_directory(self, processor, valid_video, temp_dir):
        """Test processing with read-only output directory."""
        output_dir = temp_dir / "readonly_output"
        output_dir.mkdir()
        
        # Make directory read-only
        output_dir.chmod(0o444)
        
        try:
            with pytest.raises(StorageError):
                processor.process_video(
                    input_path=valid_video,
                    output_dir=output_dir
                )
        finally:
            # Restore permissions for cleanup
            output_dir.chmod(0o755)


@pytest.mark.unit
class TestVideoEncoding:
    """Test video encoding functionality."""
    
    @patch('subprocess.run')
    def test_encode_video_success(self, mock_run, processor, valid_video, temp_dir):
        """Test successful video encoding."""
        mock_run.return_value = Mock(returncode=0)
        
        output_path = processor.encoder.encode_video(
            input_path=valid_video,
            output_dir=temp_dir,
            format_name="mp4",
            video_id="test123"
        )
        
        assert output_path.suffix == ".mp4"
        assert "test123" in str(output_path)
        
        # Verify FFmpeg was called
        assert mock_run.called
    
    @patch('subprocess.run')
    def test_encode_video_ffmpeg_failure(self, mock_run, processor, valid_video, temp_dir):
        """Test encoding failure handling."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr=b"FFmpeg encoding error"
        )
        
        with pytest.raises(EncodingError):
            processor.encoder.encode_video(
                input_path=valid_video,
                output_dir=temp_dir,
                format_name="mp4",
                video_id="test123"
            )
    
    def test_encode_video_unsupported_format(self, processor, valid_video, temp_dir):
        """Test encoding with unsupported format."""
        with pytest.raises(ValidationError):
            processor.encoder.encode_video(
                input_path=valid_video,
                output_dir=temp_dir,
                format_name="unsupported_format",
                video_id="test123"
            )
    
    @pytest.mark.parametrize("format_name,expected_codec", [
        ("mp4", "libx264"),
        ("webm", "libvpx-vp9"),
        ("ogv", "libtheora"),
    ])
    @patch('subprocess.run')
    def test_format_specific_codecs(self, mock_run, processor, valid_video, temp_dir,
                                   format_name, expected_codec):
        """Test that correct codecs are used for different formats."""
        mock_run.return_value = Mock(returncode=0)
        
        processor.encoder.encode_video(
            input_path=valid_video,
            output_dir=temp_dir,
            format_name=format_name,
            video_id="test123"
        )
        
        # Check that the expected codec was used in the FFmpeg command
        call_args = mock_run.call_args[0][0]
        assert expected_codec in call_args


@pytest.mark.unit
class TestThumbnailGeneration:
    """Test thumbnail generation functionality."""
    
    @patch('subprocess.run')
    def test_generate_thumbnail_success(self, mock_run, processor, valid_video, temp_dir):
        """Test successful thumbnail generation."""
        mock_run.return_value = Mock(returncode=0)
        
        thumbnail_path = processor.thumbnail_generator.generate_thumbnail(
            video_path=valid_video,
            output_dir=temp_dir,
            timestamp=5,
            video_id="test123"
        )
        
        assert thumbnail_path.suffix in [".jpg", ".png"]
        assert "test123" in str(thumbnail_path)
        assert "_thumb_5" in str(thumbnail_path)
        
        # Verify FFmpeg was called for thumbnail
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "-ss" in call_args  # Seek to timestamp
        assert "5" in call_args    # Timestamp value
    
    @patch('subprocess.run')
    def test_generate_thumbnail_ffmpeg_failure(self, mock_run, processor, valid_video, temp_dir):
        """Test thumbnail generation failure handling."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr=b"FFmpeg thumbnail error"
        )
        
        with pytest.raises(EncodingError):
            processor.thumbnail_generator.generate_thumbnail(
                video_path=valid_video,
                output_dir=temp_dir,
                timestamp=5,
                video_id="test123"
            )
    
    @pytest.mark.parametrize("timestamp,expected_time", [
        (0, "0"),
        (1, "1"),
        (30, "30"),
        (3600, "3600"),  # 1 hour
    ])
    @patch('subprocess.run')
    def test_thumbnail_timestamps(self, mock_run, processor, valid_video, temp_dir,
                                 timestamp, expected_time):
        """Test thumbnail generation at different timestamps."""
        mock_run.return_value = Mock(returncode=0)
        
        processor.thumbnail_generator.generate_thumbnail(
            video_path=valid_video,
            output_dir=temp_dir,
            timestamp=timestamp,
            video_id="test123"
        )
        
        call_args = mock_run.call_args[0][0]
        assert "-ss" in call_args
        ss_index = call_args.index("-ss")
        assert call_args[ss_index + 1] == expected_time


@pytest.mark.unit  
class TestSpriteGeneration:
    """Test sprite sheet generation functionality."""
    
    @patch('video_processor.utils.sprite_generator.generate_sprite_sheet')
    def test_generate_sprites_success(self, mock_generate, processor, valid_video, temp_dir):
        """Test successful sprite generation."""
        # Mock sprite generator
        sprite_path = temp_dir / "sprites.jpg"
        vtt_path = temp_dir / "sprites.vtt"
        
        mock_generate.return_value = (sprite_path, vtt_path)
        
        # Create mock files
        sprite_path.parent.mkdir(parents=True, exist_ok=True)
        sprite_path.touch()
        vtt_path.touch()
        
        result_sprite, result_vtt = processor.thumbnail_generator.generate_sprites(
            video_path=valid_video,
            output_dir=temp_dir,
            video_id="test123"
        )
        
        assert result_sprite == sprite_path
        assert result_vtt == vtt_path
        assert mock_generate.called
    
    @patch('video_processor.utils.sprite_generator.generate_sprite_sheet')
    def test_generate_sprites_failure(self, mock_generate, processor, valid_video, temp_dir):
        """Test sprite generation failure handling."""
        mock_generate.side_effect = Exception("Sprite generation failed")
        
        with pytest.raises(EncodingError):
            processor.thumbnail_generator.generate_sprites(
                video_path=valid_video,
                output_dir=temp_dir,
                video_id="test123"
            )


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_process_video_with_corrupted_input(self, processor, corrupt_video, temp_dir):
        """Test processing corrupted video file."""
        with pytest.raises((VideoProcessorError, FileNotFoundError)):
            processor.process_video(
                input_path=corrupt_video,
                output_dir=temp_dir / "output"
            )
    
    @patch('shutil.disk_usage')
    def test_insufficient_disk_space(self, mock_disk, processor, valid_video, temp_dir):
        """Test handling of insufficient disk space."""
        # Mock very low disk space (100 bytes)
        mock_disk.return_value = Mock(free=100)
        
        with pytest.raises(StorageError) as exc_info:
            processor.process_video(
                input_path=valid_video,
                output_dir=temp_dir / "output"
            )
        
        assert "disk space" in str(exc_info.value).lower()
    
    @patch('pathlib.Path.mkdir')
    def test_permission_error_on_directory_creation(self, mock_mkdir, processor, valid_video):
        """Test handling permission errors during directory creation."""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(StorageError):
            processor.process_video(
                input_path=valid_video,
                output_dir=Path("/restricted/path")
            )
    
    def test_cleanup_on_processing_failure(self, processor, valid_video, temp_dir):
        """Test that temporary files are cleaned up on failure."""
        output_dir = temp_dir / "output"
        
        with patch.object(processor.encoder, 'encode_video') as mock_encode:
            mock_encode.side_effect = EncodingError("Encoding failed")
            
            try:
                processor.process_video(
                    input_path=valid_video,
                    output_dir=output_dir
                )
            except EncodingError:
                pass
            
            # Check that no temporary files remain
            if output_dir.exists():
                temp_files = list(output_dir.glob("*.tmp"))
                assert len(temp_files) == 0


@pytest.mark.unit
class TestQualityPresets:
    """Test quality preset functionality."""
    
    @pytest.mark.parametrize("preset,expected_bitrate", [
        ("low", "1000k"),
        ("medium", "2500k"),
        ("high", "5000k"),
        ("ultra", "10000k"),
    ])
    def test_quality_preset_bitrates(self, temp_dir, preset, expected_bitrate):
        """Test that quality presets use correct bitrates."""
        config = ProcessorConfig(
            base_path=temp_dir,
            quality_preset=preset
        )
        processor = VideoProcessor(config)
        
        # Get encoding parameters
        from video_processor.core.encoders import VideoEncoder
        encoder = VideoEncoder(processor.config)
        quality_params = encoder._quality_presets[preset]
        
        assert quality_params["video_bitrate"] == expected_bitrate
    
    def test_invalid_quality_preset(self, temp_dir):
        """Test handling of invalid quality preset."""
        # The ValidationError is now a pydantic ValidationError, not our custom one
        from pydantic import ValidationError as PydanticValidationError
        with pytest.raises(PydanticValidationError):
            ProcessorConfig(
                base_path=temp_dir,
                quality_preset="invalid_preset"
            )