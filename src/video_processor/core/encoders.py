"""Video encoding using FFmpeg."""

import subprocess
from pathlib import Path

from ..config import ProcessorConfig
from ..exceptions import EncodingError, FFmpegError


class VideoEncoder:
    """Handles video encoding operations using FFmpeg."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config
        self._quality_presets = self._get_quality_presets()

    def _get_quality_presets(self) -> dict[str, dict[str, str]]:
        """Get quality presets for different output formats."""
        return {
            "low": {
                "video_bitrate": "1000k",
                "min_bitrate": "500k",
                "max_bitrate": "1500k",
                "audio_bitrate": "128k",
                "crf": "28",
            },
            "medium": {
                "video_bitrate": "2500k",
                "min_bitrate": "1000k",
                "max_bitrate": "4000k",
                "audio_bitrate": "192k",
                "crf": "23",
            },
            "high": {
                "video_bitrate": "5000k",
                "min_bitrate": "2000k",
                "max_bitrate": "8000k",
                "audio_bitrate": "256k",
                "crf": "18",
            },
            "ultra": {
                "video_bitrate": "10000k",
                "min_bitrate": "5000k",
                "max_bitrate": "15000k",
                "audio_bitrate": "320k",
                "crf": "15",
            },
        }

    def encode_video(
        self,
        input_path: Path,
        output_dir: Path,
        format_name: str,
        video_id: str,
    ) -> Path:
        """
        Encode video to specified format.

        Args:
            input_path: Input video file
            output_dir: Output directory
            format_name: Output format (mp4, webm, ogv)
            video_id: Unique video identifier

        Returns:
            Path to encoded file
        """
        if format_name == "mp4":
            return self._encode_mp4(input_path, output_dir, video_id)
        elif format_name == "webm":
            return self._encode_webm(input_path, output_dir, video_id)
        elif format_name == "ogv":
            return self._encode_ogv(input_path, output_dir, video_id)
        elif format_name == "av1_mp4":
            return self._encode_av1_mp4(input_path, output_dir, video_id)
        elif format_name == "av1_webm":
            return self._encode_av1_webm(input_path, output_dir, video_id)
        elif format_name == "hevc":
            return self._encode_hevc_mp4(input_path, output_dir, video_id)
        else:
            raise EncodingError(f"Unsupported format: {format_name}")

    def _encode_mp4(self, input_path: Path, output_dir: Path, video_id: str) -> Path:
        """Encode video to MP4 using two-pass encoding."""
        output_file = output_dir / f"{video_id}.mp4"
        passlog_file = output_dir / f"{video_id}.ffmpeg2pass"
        quality = self._quality_presets[self.config.quality_preset]

        def clean_passlogs() -> None:
            """Clean up FFmpeg pass log files."""
            for suffix in ["-0.log", "-0.log.mbtree"]:
                log_file = Path(f"{passlog_file}{suffix}")
                if log_file.exists():
                    log_file.unlink()

        clean_passlogs()

        try:
            # Pass 1 - Analysis pass
            pass1_cmd = [
                self.config.ffmpeg_path,
                "-y",
                "-i",
                str(input_path),
                "-passlogfile",
                str(passlog_file),
                "-c:v",
                "libx264",
                "-b:v",
                quality["video_bitrate"],
                "-minrate",
                quality["min_bitrate"],
                "-maxrate",
                quality["max_bitrate"],
                "-pass",
                "1",
                "-an",  # No audio in pass 1
                "-f",
                "mp4",
                "/dev/null",
            ]

            result = subprocess.run(pass1_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise FFmpegError(f"Pass 1 failed: {result.stderr}")

            # Pass 2 - Final encoding
            pass2_cmd = [
                self.config.ffmpeg_path,
                "-y",
                "-i",
                str(input_path),
                "-passlogfile",
                str(passlog_file),
                "-c:v",
                "libx264",
                "-b:v",
                quality["video_bitrate"],
                "-minrate",
                quality["min_bitrate"],
                "-maxrate",
                quality["max_bitrate"],
                "-pass",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                quality["audio_bitrate"],
                "-movflags",
                "faststart",
                str(output_file),
            ]

            result = subprocess.run(pass2_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise FFmpegError(f"Pass 2 failed: {result.stderr}")

        finally:
            clean_passlogs()

        if not output_file.exists():
            raise EncodingError("MP4 encoding failed - output file not created")

        return output_file

    def _encode_webm(self, input_path: Path, output_dir: Path, video_id: str) -> Path:
        """Encode video to WebM using VP9."""
        # Use MP4 as input if it exists for better quality
        mp4_file = output_dir / f"{video_id}.mp4"
        source_file = mp4_file if mp4_file.exists() else input_path

        output_file = output_dir / f"{video_id}.webm"
        passlog_file = output_dir / f"{video_id}.webm-pass"
        quality = self._quality_presets[self.config.quality_preset]

        try:
            # Pass 1
            pass1_cmd = [
                self.config.ffmpeg_path,
                "-y",
                "-i",
                str(source_file),
                "-passlogfile",
                str(passlog_file),
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                quality["crf"],
                "-pass",
                "1",
                "-an",
                "-f",
                "null",
                "/dev/null",
            ]

            result = subprocess.run(pass1_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise FFmpegError(f"WebM Pass 1 failed: {result.stderr}")

            # Pass 2
            pass2_cmd = [
                self.config.ffmpeg_path,
                "-y",
                "-i",
                str(source_file),
                "-passlogfile",
                str(passlog_file),
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                quality["crf"],
                "-pass",
                "2",
                "-c:a",
                "libopus",
                str(output_file),
            ]

            result = subprocess.run(pass2_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise FFmpegError(f"WebM Pass 2 failed: {result.stderr}")

        finally:
            # Clean up pass log
            pass_log = Path(f"{passlog_file}-0.log")
            if pass_log.exists():
                pass_log.unlink()

        if not output_file.exists():
            raise EncodingError("WebM encoding failed - output file not created")

        return output_file

    def _encode_ogv(self, input_path: Path, output_dir: Path, video_id: str) -> Path:
        """Encode video to OGV using Theora."""
        # Use MP4 as input if it exists for better quality
        mp4_file = output_dir / f"{video_id}.mp4"
        source_file = mp4_file if mp4_file.exists() else input_path

        output_file = output_dir / f"{video_id}.ogv"

        cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(source_file),
            "-codec:v",
            "libtheora",
            "-qscale:v",
            "6",
            "-codec:a",
            "libvorbis",
            "-qscale:a",
            "6",
            str(output_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"OGV encoding failed: {result.stderr}")

        if not output_file.exists():
            raise EncodingError("OGV encoding failed - output file not created")

        return output_file

    def _encode_av1_mp4(
        self, input_path: Path, output_dir: Path, video_id: str
    ) -> Path:
        """Encode video to AV1 in MP4 container."""
        from .advanced_encoders import AdvancedVideoEncoder

        advanced_encoder = AdvancedVideoEncoder(self.config)
        return advanced_encoder.encode_av1(
            input_path, output_dir, video_id, container="mp4"
        )

    def _encode_av1_webm(
        self, input_path: Path, output_dir: Path, video_id: str
    ) -> Path:
        """Encode video to AV1 in WebM container."""
        from .advanced_encoders import AdvancedVideoEncoder

        advanced_encoder = AdvancedVideoEncoder(self.config)
        return advanced_encoder.encode_av1(
            input_path, output_dir, video_id, container="webm"
        )

    def _encode_hevc_mp4(
        self, input_path: Path, output_dir: Path, video_id: str
    ) -> Path:
        """Encode video to HEVC/H.265 in MP4 container."""
        from .advanced_encoders import AdvancedVideoEncoder

        advanced_encoder = AdvancedVideoEncoder(self.config)
        return advanced_encoder.encode_hevc(input_path, output_dir, video_id)
