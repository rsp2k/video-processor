"""Video metadata extraction using FFmpeg probe."""

from pathlib import Path
from typing import Any

import ffmpeg

from ..config import ProcessorConfig
from ..exceptions import FFmpegError


class VideoMetadata:
    """Handles video metadata extraction."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

    def extract_metadata(self, video_path: Path) -> dict[str, Any]:
        """
        Extract comprehensive metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing video metadata
        """
        try:
            probe_data = ffmpeg.probe(str(video_path))

            # Extract general format information
            format_info = probe_data.get("format", {})

            # Extract video stream information
            video_stream = self._get_video_stream(probe_data)
            audio_stream = self._get_audio_stream(probe_data)

            metadata = {
                # File information
                "filename": video_path.name,
                "file_size": int(format_info.get("size", 0)),
                "duration": float(format_info.get("duration", 0)),
                "bitrate": int(format_info.get("bit_rate", 0)),
                "format_name": format_info.get("format_name", ""),
                "format_long_name": format_info.get("format_long_name", ""),
                # Video stream information
                "video": self._extract_video_metadata(video_stream)
                if video_stream
                else None,
                # Audio stream information
                "audio": self._extract_audio_metadata(audio_stream)
                if audio_stream
                else None,
                # All streams count
                "stream_count": len(probe_data.get("streams", [])),
                # Raw probe data for advanced use cases
                "raw_probe_data": probe_data,
            }

            return metadata

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            raise FFmpegError(f"Metadata extraction failed: {error_msg}") from e
        except Exception as e:
            raise FFmpegError(f"Metadata extraction failed: {e}") from e

    def _get_video_stream(self, probe_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get the primary video stream from probe data."""
        streams = probe_data.get("streams", [])
        return next(
            (stream for stream in streams if stream.get("codec_type") == "video"), None
        )

    def _get_audio_stream(self, probe_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get the primary audio stream from probe data."""
        streams = probe_data.get("streams", [])
        return next(
            (stream for stream in streams if stream.get("codec_type") == "audio"), None
        )

    def _extract_video_metadata(self, video_stream: dict[str, Any]) -> dict[str, Any]:
        """Extract video-specific metadata."""
        return {
            "codec_name": video_stream.get("codec_name", ""),
            "codec_long_name": video_stream.get("codec_long_name", ""),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "aspect_ratio": video_stream.get("display_aspect_ratio", ""),
            "pixel_format": video_stream.get("pix_fmt", ""),
            "framerate": self._parse_framerate(video_stream.get("r_frame_rate", "")),
            "avg_framerate": self._parse_framerate(
                video_stream.get("avg_frame_rate", "")
            ),
            "bitrate": int(video_stream.get("bit_rate", 0))
            if video_stream.get("bit_rate")
            else None,
            "duration": float(video_stream.get("duration", 0))
            if video_stream.get("duration")
            else None,
            "frame_count": int(video_stream.get("nb_frames", 0))
            if video_stream.get("nb_frames")
            else None,
        }

    def _extract_audio_metadata(self, audio_stream: dict[str, Any]) -> dict[str, Any]:
        """Extract audio-specific metadata."""
        return {
            "codec_name": audio_stream.get("codec_name", ""),
            "codec_long_name": audio_stream.get("codec_long_name", ""),
            "sample_rate": int(audio_stream.get("sample_rate", 0))
            if audio_stream.get("sample_rate")
            else None,
            "channels": int(audio_stream.get("channels", 0)),
            "channel_layout": audio_stream.get("channel_layout", ""),
            "bitrate": int(audio_stream.get("bit_rate", 0))
            if audio_stream.get("bit_rate")
            else None,
            "duration": float(audio_stream.get("duration", 0))
            if audio_stream.get("duration")
            else None,
        }

    def _parse_framerate(self, framerate_str: str) -> float | None:
        """Parse framerate string like '30/1' to float."""
        if not framerate_str or framerate_str == "0/0":
            return None

        try:
            if "/" in framerate_str:
                numerator, denominator = framerate_str.split("/")
                return float(numerator) / float(denominator)
            else:
                return float(framerate_str)
        except (ValueError, ZeroDivisionError):
            return None
