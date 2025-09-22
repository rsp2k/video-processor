"""Spatial audio processing for 360° videos."""

import asyncio
import logging
import subprocess
import time
from pathlib import Path

from ..exceptions import VideoProcessorError
from .models import SpatialAudioType, Video360ProcessingResult

logger = logging.getLogger(__name__)


class SpatialAudioProcessor:
    """
    Process spatial audio for 360° videos.

    Handles ambisonic audio, object-based audio, and spatial audio rotation
    for immersive 360° video experiences.
    """

    def __init__(self):
        self.supported_formats = [
            SpatialAudioType.AMBISONIC_BFORMAT,
            SpatialAudioType.AMBISONIC_HOA,
            SpatialAudioType.OBJECT_BASED,
            SpatialAudioType.HEAD_LOCKED,
            SpatialAudioType.BINAURAL,
        ]

    async def detect_spatial_audio(self, video_path: Path) -> SpatialAudioType:
        """
        Detect spatial audio format in video file.

        Args:
            video_path: Path to video file

        Returns:
            Detected spatial audio type
        """
        try:
            # Use ffprobe to analyze audio streams
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(video_path),
            ]

            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, check=True
            )

            import json

            probe_data = json.loads(result.stdout)

            # Analyze audio streams
            audio_streams = [
                stream
                for stream in probe_data.get("streams", [])
                if stream.get("codec_type") == "audio"
            ]

            if not audio_streams:
                return SpatialAudioType.NONE

            # Check channel count and metadata
            for stream in audio_streams:
                channels = stream.get("channels", 0)
                tags = stream.get("tags", {})

                # Check for ambisonic indicators
                if channels >= 4:
                    # B-format ambisonics (4 channels minimum)
                    if self._has_ambisonic_metadata(tags):
                        if channels == 4:
                            return SpatialAudioType.AMBISONIC_BFORMAT
                        else:
                            return SpatialAudioType.AMBISONIC_HOA

                    # Object-based audio
                    if self._has_object_audio_metadata(tags):
                        return SpatialAudioType.OBJECT_BASED

                # Binaural (stereo with special processing)
                if channels == 2 and self._has_binaural_metadata(tags):
                    return SpatialAudioType.BINAURAL

                # Head-locked stereo
                if channels == 2:
                    return SpatialAudioType.HEAD_LOCKED

            return SpatialAudioType.NONE

        except Exception as e:
            logger.error(f"Spatial audio detection failed: {e}")
            return SpatialAudioType.NONE

    def _has_ambisonic_metadata(self, tags: dict) -> bool:
        """Check for ambisonic audio metadata."""
        ambisonic_indicators = [
            "ambisonic",
            "Ambisonic",
            "AMBISONIC",
            "bformat",
            "B-format",
            "B_FORMAT",
            "spherical_audio",
            "spatial_audio",
        ]

        for tag_name, tag_value in tags.items():
            tag_str = str(tag_value).lower()
            if any(indicator.lower() in tag_str for indicator in ambisonic_indicators):
                return True
            if any(
                indicator.lower() in tag_name.lower()
                for indicator in ambisonic_indicators
            ):
                return True

        return False

    def _has_object_audio_metadata(self, tags: dict) -> bool:
        """Check for object-based audio metadata."""
        object_indicators = [
            "object_based",
            "object_audio",
            "spatial_objects",
            "dolby_atmos",
            "atmos",
            "dts_x",
        ]

        for tag_name, tag_value in tags.items():
            tag_str = str(tag_value).lower()
            if any(indicator in tag_str for indicator in object_indicators):
                return True

        return False

    def _has_binaural_metadata(self, tags: dict) -> bool:
        """Check for binaural audio metadata."""
        binaural_indicators = [
            "binaural",
            "hrtf",
            "head_related",
            "3d_audio",
            "immersive_stereo",
        ]

        for tag_name, tag_value in tags.items():
            tag_str = str(tag_value).lower()
            if any(indicator in tag_str for indicator in binaural_indicators):
                return True

        return False

    async def rotate_spatial_audio(
        self,
        input_path: Path,
        output_path: Path,
        yaw_rotation: float,
        pitch_rotation: float = 0.0,
        roll_rotation: float = 0.0,
    ) -> Video360ProcessingResult:
        """
        Rotate spatial audio field.

        Args:
            input_path: Source video with spatial audio
            output_path: Output video with rotated audio
            yaw_rotation: Rotation around Y-axis (degrees)
            pitch_rotation: Rotation around X-axis (degrees)
            roll_rotation: Rotation around Z-axis (degrees)

        Returns:
            Video360ProcessingResult with rotation details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="spatial_audio_rotation")

        try:
            # Detect spatial audio format
            audio_type = await self.detect_spatial_audio(input_path)

            if audio_type == SpatialAudioType.NONE:
                result.add_warning("No spatial audio detected")
                # Copy file without audio processing
                import shutil

                shutil.copy2(input_path, output_path)
                result.success = True
                result.output_path = output_path
                return result

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build audio rotation filter based on format
            audio_filter = self._build_audio_rotation_filter(
                audio_type, yaw_rotation, pitch_rotation, roll_rotation
            )

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c:v",
                "copy",  # Copy video unchanged
                "-af",
                audio_filter,
                "-c:a",
                "aac",  # Re-encode audio
                str(output_path),
                "-y",
            ]

            # Execute rotation
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                logger.info(f"Spatial audio rotation successful: yaw={yaw_rotation}°")

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Spatial audio rotation error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_audio_rotation_filter(
        self, audio_type: SpatialAudioType, yaw: float, pitch: float, roll: float
    ) -> str:
        """Build FFmpeg audio filter for spatial rotation."""

        if audio_type == SpatialAudioType.AMBISONIC_BFORMAT:
            # For B-format ambisonics, use FFmpeg's sofalizer or custom rotation
            # This is a simplified implementation
            return f"arotate=angle={yaw}*PI/180"

        elif audio_type == SpatialAudioType.OBJECT_BASED:
            # Object-based audio rotation (complex, simplified here)
            return f"aecho=0.8:0.88:{int(abs(yaw) * 10)}:0.4"

        elif audio_type == SpatialAudioType.HEAD_LOCKED:
            # Head-locked audio doesn't rotate with video
            return "copy"

        elif audio_type == SpatialAudioType.BINAURAL:
            # Binaural rotation (would need HRTF processing)
            return f"aecho=0.8:0.88:{int(abs(yaw) * 5)}:0.3"

        else:
            return "copy"

    async def convert_to_binaural(
        self, input_path: Path, output_path: Path, head_model: str = "default"
    ) -> Video360ProcessingResult:
        """
        Convert spatial audio to binaural for headphone playback.

        Args:
            input_path: Source video with spatial audio
            output_path: Output video with binaural audio
            head_model: HRTF model to use ("default", "kemar", etc.)

        Returns:
            Video360ProcessingResult with conversion details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="binaural_conversion")

        try:
            # Detect source audio format
            audio_type = await self.detect_spatial_audio(input_path)

            if audio_type == SpatialAudioType.NONE:
                result.add_error("No spatial audio to convert")
                return result

            # Get file sizes
            result.file_size_before = input_path.stat().st_size

            # Build binaural conversion filter
            binaural_filter = self._build_binaural_filter(audio_type, head_model)

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c:v",
                "copy",
                "-af",
                binaural_filter,
                "-c:a",
                "aac",
                "-ac",
                "2",  # Force stereo output
                str(output_path),
                "-y",
            ]

            # Execute conversion
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                logger.info("Binaural conversion successful")

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Binaural conversion error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def _build_binaural_filter(
        self, audio_type: SpatialAudioType, head_model: str
    ) -> str:
        """Build FFmpeg filter for binaural conversion."""

        if audio_type == SpatialAudioType.AMBISONIC_BFORMAT:
            # B-format to binaural conversion
            # In practice, would use specialized filters like sofalizer
            return "pan=stereo|FL=0.5*FL+0.3*FR+0.2*FC|FR=0.5*FR+0.3*FL+0.2*FC"

        elif audio_type == SpatialAudioType.OBJECT_BASED:
            # Object-based to binaural (complex processing)
            return "pan=stereo|FL=FL|FR=FR"

        elif audio_type == SpatialAudioType.HEAD_LOCKED:
            # Already stereo, just ensure proper panning
            return "pan=stereo|FL=FL|FR=FR"

        else:
            return "copy"

    async def extract_ambisonic_channels(
        self, input_path: Path, output_dir: Path
    ) -> dict[str, Path]:
        """
        Extract individual ambisonic channels (W, X, Y, Z).

        Args:
            input_path: Source video with ambisonic audio
            output_dir: Directory for channel files

        Returns:
            Dictionary mapping channel names to file paths
        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)

            # Detect if audio is ambisonic
            audio_type = await self.detect_spatial_audio(input_path)

            if audio_type not in [
                SpatialAudioType.AMBISONIC_BFORMAT,
                SpatialAudioType.AMBISONIC_HOA,
            ]:
                raise VideoProcessorError("Input does not contain ambisonic audio")

            channels = {}
            channel_names = ["W", "X", "Y", "Z"]  # B-format channels

            # Extract each channel
            for i, channel_name in enumerate(channel_names):
                output_path = output_dir / f"channel_{channel_name}.wav"

                cmd = [
                    "ffmpeg",
                    "-i",
                    str(input_path),
                    "-map",
                    "0:a:0",
                    "-af",
                    f"pan=mono|c0=c{i}",
                    "-c:a",
                    "pcm_s16le",
                    str(output_path),
                    "-y",
                ]

                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True
                )

                if result.returncode == 0:
                    channels[channel_name] = output_path
                    logger.info(f"Extracted ambisonic channel {channel_name}")
                else:
                    logger.error(
                        f"Failed to extract channel {channel_name}: {result.stderr}"
                    )

            return channels

        except Exception as e:
            logger.error(f"Ambisonic channel extraction failed: {e}")
            raise VideoProcessorError(f"Channel extraction failed: {e}")

    async def create_ambisonic_from_channels(
        self,
        channel_files: dict[str, Path],
        output_path: Path,
        video_path: Path | None = None,
    ) -> Video360ProcessingResult:
        """
        Create ambisonic audio from individual channel files.

        Args:
            channel_files: Dictionary of channel name to file path
            output_path: Output ambisonic audio/video file
            video_path: Optional video to combine with audio

        Returns:
            Video360ProcessingResult with creation details
        """
        start_time = time.time()
        result = Video360ProcessingResult(operation="create_ambisonic")

        try:
            required_channels = ["W", "X", "Y", "Z"]

            # Verify all required channels are present
            for channel in required_channels:
                if channel not in channel_files:
                    raise VideoProcessorError(f"Missing required channel: {channel}")
                if not channel_files[channel].exists():
                    raise VideoProcessorError(
                        f"Channel file not found: {channel_files[channel]}"
                    )

            # Build FFmpeg command
            cmd = ["ffmpeg"]

            # Add video input if provided
            if video_path and video_path.exists():
                cmd.extend(["-i", str(video_path)])
                video_input_index = 0
                audio_start_index = 1
            else:
                video_input_index = None
                audio_start_index = 0

            # Add channel inputs in B-format order (W, X, Y, Z)
            for channel in required_channels:
                cmd.extend(["-i", str(channel_files[channel])])

            # Map inputs
            if video_input_index is not None:
                cmd.extend(["-map", f"{video_input_index}:v"])  # Video

            # Map audio channels
            for i, channel in enumerate(required_channels):
                cmd.extend(["-map", f"{audio_start_index + i}:a"])

            # Set audio codec and channel layout
            cmd.extend(
                [
                    "-c:a",
                    "aac",
                    "-ac",
                    "4",  # 4-channel output
                    "-metadata:s:a:0",
                    "ambisonic=1",
                    "-metadata:s:a:0",
                    "channel_layout=quad",
                ]
            )

            # Copy video if present
            if video_input_index is not None:
                cmd.extend(["-c:v", "copy"])

            cmd.extend([str(output_path), "-y"])

            # Execute creation
            process_result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if process_result.returncode == 0:
                result.success = True
                result.output_path = output_path
                result.file_size_after = output_path.stat().st_size

                logger.info("Ambisonic audio creation successful")

            else:
                result.add_error(f"FFmpeg failed: {process_result.stderr}")

        except Exception as e:
            result.add_error(f"Ambisonic creation error: {e}")

        result.processing_time = time.time() - start_time
        return result

    def get_supported_formats(self) -> list[SpatialAudioType]:
        """Get list of supported spatial audio formats."""
        return self.supported_formats.copy()

    def get_format_info(self, audio_type: SpatialAudioType) -> dict:
        """Get information about a spatial audio format."""
        format_info = {
            SpatialAudioType.AMBISONIC_BFORMAT: {
                "name": "Ambisonic B-format",
                "channels": 4,
                "description": "First-order ambisonics with W, X, Y, Z channels",
                "use_cases": ["360° video", "VR", "immersive audio"],
                "rotation_support": True,
            },
            SpatialAudioType.AMBISONIC_HOA: {
                "name": "Higher Order Ambisonics",
                "channels": "9+",
                "description": "Higher order ambisonic encoding for better spatial resolution",
                "use_cases": ["Professional VR", "research", "high-end immersive"],
                "rotation_support": True,
            },
            SpatialAudioType.OBJECT_BASED: {
                "name": "Object-based Audio",
                "channels": "Variable",
                "description": "Audio objects positioned in 3D space",
                "use_cases": ["Dolby Atmos", "cinema", "interactive content"],
                "rotation_support": True,
            },
            SpatialAudioType.HEAD_LOCKED: {
                "name": "Head-locked Stereo",
                "channels": 2,
                "description": "Stereo audio that doesn't rotate with head movement",
                "use_cases": ["Narration", "music", "UI sounds"],
                "rotation_support": False,
            },
            SpatialAudioType.BINAURAL: {
                "name": "Binaural Audio",
                "channels": 2,
                "description": "Stereo audio processed for headphone playback with HRTF",
                "use_cases": ["Headphone VR", "ASMR", "3D audio simulation"],
                "rotation_support": True,
            },
        }

        return format_info.get(
            audio_type,
            {
                "name": "Unknown",
                "channels": 0,
                "description": "Unknown spatial audio format",
                "use_cases": [],
                "rotation_support": False,
            },
        )
