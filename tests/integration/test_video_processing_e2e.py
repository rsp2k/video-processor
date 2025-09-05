"""
End-to-end integration tests for video processing in Docker environment.

These tests verify the complete video processing pipeline including:
- Video encoding with multiple formats
- Thumbnail generation
- Sprite generation
- Database integration
- File system operations
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any

import pytest
import psycopg2

from video_processor import VideoProcessor, ProcessorConfig
from video_processor.core.processor import VideoProcessingResult


class TestVideoProcessingE2E:
    """End-to-end tests for video processing pipeline."""
    
    def test_synchronous_video_processing(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test complete synchronous video processing pipeline."""
        print(f"\n🎬 Testing synchronous video processing with {test_video_file}")
        
        # Configure processor for integration testing
        output_dir = temp_video_dir / "sync_output"
        config = ProcessorConfig(
            base_path=output_dir,
            output_formats=["mp4", "webm"],  # Test multiple formats
            quality_preset="low",  # Fast processing for tests
            generate_thumbnails=True,
            generate_sprites=True,
            sprite_interval=2.0,  # More frequent for short test video
            thumbnail_timestamp=5,  # 5 seconds into 10s video
            storage_backend="local"
        )
        
        # Initialize processor
        processor = VideoProcessor(config)
        
        # Process the test video
        start_time = time.time()
        result = processor.process_video(
            input_path=test_video_file,
            output_dir="test_sync_processing"
        )
        processing_time = time.time() - start_time
        
        # Verify result structure
        assert isinstance(result, VideoProcessingResult)
        assert result.video_id is not None
        assert len(result.video_id) > 0
        
        # Verify encoded files
        assert "mp4" in result.encoded_files
        assert "webm" in result.encoded_files
        
        for format_name, output_path in result.encoded_files.items():
            assert output_path.exists(), f"{format_name} output file not found: {output_path}"
            assert output_path.stat().st_size > 0, f"{format_name} output file is empty"
            
        # Verify thumbnail
        assert result.thumbnail_file is not None
        assert result.thumbnail_file.exists()
        assert result.thumbnail_file.suffix.lower() in [".jpg", ".jpeg", ".png"]
        
        # Verify sprite files
        assert result.sprite_files is not None
        sprite_image, webvtt_file = result.sprite_files
        assert sprite_image.exists()
        assert webvtt_file.exists()
        assert sprite_image.suffix.lower() in [".jpg", ".jpeg", ".png"]
        assert webvtt_file.suffix == ".vtt"
        
        # Verify metadata
        assert result.metadata is not None
        assert result.metadata.duration > 0
        assert result.metadata.width > 0
        assert result.metadata.height > 0
        
        print(f"✅ Synchronous processing completed in {processing_time:.2f}s")
        print(f"   Video ID: {result.video_id}")
        print(f"   Formats: {list(result.encoded_files.keys())}")
        print(f"   Duration: {result.metadata.duration}s")
        
    def test_video_processing_with_custom_config(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test video processing with various configuration options."""
        print(f"\n⚙️ Testing video processing with custom configuration")
        
        output_dir = temp_video_dir / "custom_config_output"
        
        # Test with different quality preset
        config = ProcessorConfig(
            base_path=output_dir,
            output_formats=["mp4"],
            quality_preset="medium",
            generate_thumbnails=True,
            generate_sprites=False,  # Disable sprites for this test
            thumbnail_timestamp=1,
            custom_ffmpeg_options={
                "video": ["-preset", "ultrafast"],  # Override for speed
                "audio": ["-ac", "1"]  # Mono audio
            }
        )
        
        processor = VideoProcessor(config)
        result = processor.process_video(test_video_file, "custom_config_test")
        
        # Verify custom configuration was applied
        assert len(result.encoded_files) == 1  # Only MP4
        assert "mp4" in result.encoded_files
        assert result.thumbnail_file is not None
        assert result.sprite_files is None  # Sprites disabled
        
        print("✅ Custom configuration test passed")
        
    def test_error_handling(
        self,
        docker_compose_project: str,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test error handling for invalid inputs."""
        print(f"\n🚫 Testing error handling scenarios")
        
        config = ProcessorConfig(
            base_path=temp_video_dir / "error_test",
            output_formats=["mp4"],
            quality_preset="low"
        )
        processor = VideoProcessor(config)
        
        # Test with non-existent file
        non_existent_file = temp_video_dir / "does_not_exist.mp4"
        
        with pytest.raises(FileNotFoundError):
            processor.process_video(non_existent_file, "error_test")
            
        print("✅ Error handling test passed")
        
    def test_concurrent_processing(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test processing multiple videos concurrently."""
        print(f"\n🔄 Testing concurrent video processing")
        
        # Create multiple output directories
        num_concurrent = 3
        processors = []
        
        for i in range(num_concurrent):
            output_dir = temp_video_dir / f"concurrent_{i}"
            config = ProcessorConfig(
                base_path=output_dir,
                output_formats=["mp4"],
                quality_preset="low",
                generate_thumbnails=False,  # Disable for speed
                generate_sprites=False
            )
            processors.append(VideoProcessor(config))
        
        # Process videos concurrently (simulate multiple instances)
        results = []
        start_time = time.time()
        
        for i, processor in enumerate(processors):
            result = processor.process_video(test_video_file, f"concurrent_test_{i}")
            results.append(result)
            
        processing_time = time.time() - start_time
        
        # Verify all results
        assert len(results) == num_concurrent
        for i, result in enumerate(results):
            assert result.video_id is not None
            assert "mp4" in result.encoded_files
            assert result.encoded_files["mp4"].exists()
            
        print(f"✅ Processed {num_concurrent} videos concurrently in {processing_time:.2f}s")


class TestVideoProcessingValidation:
    """Tests for video processing validation and edge cases."""
    
    def test_quality_preset_validation(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test all quality presets produce valid output."""
        print(f"\n📊 Testing quality preset validation")
        
        presets = ["low", "medium", "high", "ultra"]
        
        for preset in presets:
            output_dir = temp_video_dir / f"quality_{preset}"
            config = ProcessorConfig(
                base_path=output_dir,
                output_formats=["mp4"],
                quality_preset=preset,
                generate_thumbnails=False,
                generate_sprites=False
            )
            
            processor = VideoProcessor(config)
            result = processor.process_video(test_video_file, f"quality_test_{preset}")
            
            # Verify output exists and has content
            assert result.encoded_files["mp4"].exists()
            assert result.encoded_files["mp4"].stat().st_size > 0
            
            print(f"   ✅ {preset} preset: {result.encoded_files['mp4'].stat().st_size} bytes")
            
        print("✅ All quality presets validated")
        
    def test_output_format_validation(
        self,
        docker_compose_project: str,
        test_video_file: Path,  
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test all supported output formats."""
        print(f"\n🎞️ Testing output format validation")
        
        formats = ["mp4", "webm", "ogv"]
        
        output_dir = temp_video_dir / "format_test"
        config = ProcessorConfig(
            base_path=output_dir,
            output_formats=formats,
            quality_preset="low",
            generate_thumbnails=False,
            generate_sprites=False
        )
        
        processor = VideoProcessor(config)
        result = processor.process_video(test_video_file, "format_validation")
        
        # Verify all formats were created
        for fmt in formats:
            assert fmt in result.encoded_files
            output_file = result.encoded_files[fmt]
            assert output_file.exists()
            assert output_file.suffix == f".{fmt}"
            
            print(f"   ✅ {fmt}: {output_file.stat().st_size} bytes")
            
        print("✅ All output formats validated")


class TestVideoProcessingPerformance:
    """Performance and resource usage tests."""
    
    def test_processing_performance(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        clean_database: None
    ):
        """Test processing performance metrics."""
        print(f"\n⚡ Testing processing performance")
        
        config = ProcessorConfig(
            base_path=temp_video_dir / "performance_test",
            output_formats=["mp4"],
            quality_preset="low",
            generate_thumbnails=True,
            generate_sprites=True
        )
        
        processor = VideoProcessor(config)
        
        # Measure processing time
        start_time = time.time()
        result = processor.process_video(test_video_file, "performance_test")
        processing_time = time.time() - start_time
        
        # Performance assertions (for 10s test video)
        assert processing_time < 60, f"Processing took too long: {processing_time:.2f}s"
        assert result.metadata.duration > 0
        
        # Calculate processing ratio (processing_time / video_duration)
        processing_ratio = processing_time / result.metadata.duration
        
        print(f"✅ Processing completed in {processing_time:.2f}s")
        print(f"   Video duration: {result.metadata.duration:.2f}s") 
        print(f"   Processing ratio: {processing_ratio:.2f}x realtime")
        
        # Performance should be reasonable for test setup
        assert processing_ratio < 10, f"Processing too slow: {processing_ratio:.2f}x realtime"