"""Advanced video encoders for next-generation codecs (AV1, HDR)."""

import subprocess
from pathlib import Path
from typing import Literal

from ..config import ProcessorConfig
from ..exceptions import EncodingError, FFmpegError


class AdvancedVideoEncoder:
    """Handles advanced video encoding operations using next-generation codecs."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config
        self._quality_presets = self._get_advanced_quality_presets()

    def _get_advanced_quality_presets(self) -> dict[str, dict[str, str]]:
        """Get quality presets optimized for advanced codecs."""
        return {
            "low": {
                "av1_crf": "35",
                "av1_cpu_used": "8",  # Fastest encoding
                "hevc_crf": "30",
                "bitrate_multiplier": "0.7",  # AV1 needs less bitrate
            },
            "medium": {
                "av1_crf": "28",
                "av1_cpu_used": "6",  # Balanced speed/quality
                "hevc_crf": "25",
                "bitrate_multiplier": "0.8",
            },
            "high": {
                "av1_crf": "22",
                "av1_cpu_used": "4",  # Better quality
                "hevc_crf": "20",
                "bitrate_multiplier": "0.9",
            },
            "ultra": {
                "av1_crf": "18",
                "av1_cpu_used": "2",  # Highest quality, slower encoding
                "hevc_crf": "16",
                "bitrate_multiplier": "1.0",
            },
        }

    def encode_av1(
        self,
        input_path: Path,
        output_dir: Path,
        video_id: str,
        container: Literal["mp4", "webm"] = "mp4",
        use_two_pass: bool = True,
    ) -> Path:
        """
        Encode video to AV1 using libaom-av1 encoder.

        AV1 provides ~30% better compression than H.264 with same quality.
        Uses CRF (Constant Rate Factor) for quality-based encoding.

        Args:
            input_path: Input video file
            output_dir: Output directory
            video_id: Unique video identifier
            container: Output container (mp4 or webm)
            use_two_pass: Whether to use two-pass encoding for better quality

        Returns:
            Path to encoded file
        """
        extension = "mp4" if container == "mp4" else "webm"
        output_file = output_dir / f"{video_id}_av1.{extension}"
        passlog_file = output_dir / f"{video_id}.av1-pass"
        quality = self._quality_presets[self.config.quality_preset]

        # Check if libaom-av1 is available
        if not self._check_av1_support():
            raise EncodingError("AV1 encoding requires libaom-av1 encoder in FFmpeg")

        def clean_av1_passlogs() -> None:
            """Clean up AV1 pass log files."""
            for suffix in ["-0.log"]:
                log_file = Path(f"{passlog_file}{suffix}")
                if log_file.exists():
                    try:
                        log_file.unlink()
                    except FileNotFoundError:
                        pass  # Already removed

        clean_av1_passlogs()

        try:
            if use_two_pass:
                # Two-pass encoding for optimal quality/size ratio
                self._encode_av1_two_pass(
                    input_path, output_file, passlog_file, quality, container
                )
            else:
                # Single-pass CRF encoding for faster processing
                self._encode_av1_single_pass(
                    input_path, output_file, quality, container
                )

        finally:
            clean_av1_passlogs()

        if not output_file.exists():
            raise EncodingError("AV1 encoding failed - output file not created")

        return output_file

    def _encode_av1_two_pass(
        self,
        input_path: Path,
        output_file: Path,
        passlog_file: Path,
        quality: dict[str, str],
        container: str,
    ) -> None:
        """Encode AV1 using two-pass method."""
        # Pass 1 - Analysis pass
        pass1_cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libaom-av1",
            "-crf",
            quality["av1_crf"],
            "-cpu-used",
            quality["av1_cpu_used"],
            "-row-mt",
            "1",  # Enable row-based multithreading
            "-tiles",
            "2x2",  # Tile-based encoding for parallelization
            "-pass",
            "1",
            "-passlogfile",
            str(passlog_file),
            "-an",  # No audio in pass 1
            "-f",
            container,
            "/dev/null"
            if container == "webm"
            else "NUL"
            if container == "mp4"
            else "/dev/null",
        ]

        result = subprocess.run(pass1_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"AV1 Pass 1 failed: {result.stderr}")

        # Pass 2 - Final encoding
        pass2_cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libaom-av1",
            "-crf",
            quality["av1_crf"],
            "-cpu-used",
            quality["av1_cpu_used"],
            "-row-mt",
            "1",
            "-tiles",
            "2x2",
            "-pass",
            "2",
            "-passlogfile",
            str(passlog_file),
        ]

        # Audio encoding based on container
        if container == "webm":
            pass2_cmd.extend(["-c:a", "libopus", "-b:a", "128k"])
        else:  # mp4
            pass2_cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        pass2_cmd.append(str(output_file))

        result = subprocess.run(pass2_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"AV1 Pass 2 failed: {result.stderr}")

    def _encode_av1_single_pass(
        self,
        input_path: Path,
        output_file: Path,
        quality: dict[str, str],
        container: str,
    ) -> None:
        """Encode AV1 using single-pass CRF method."""
        cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libaom-av1",
            "-crf",
            quality["av1_crf"],
            "-cpu-used",
            quality["av1_cpu_used"],
            "-row-mt",
            "1",
            "-tiles",
            "2x2",
        ]

        # Audio encoding based on container
        if container == "webm":
            cmd.extend(["-c:a", "libopus", "-b:a", "128k"])
        else:  # mp4
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        cmd.append(str(output_file))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"AV1 single-pass encoding failed: {result.stderr}")

    def encode_hevc(
        self,
        input_path: Path,
        output_dir: Path,
        video_id: str,
        use_hardware: bool = False,
    ) -> Path:
        """
        Encode video to HEVC/H.265 for better compression than H.264.

        HEVC provides ~25% better compression than H.264 with same quality.

        Args:
            input_path: Input video file
            output_dir: Output directory
            video_id: Unique video identifier
            use_hardware: Whether to attempt hardware acceleration

        Returns:
            Path to encoded file
        """
        output_file = output_dir / f"{video_id}_hevc.mp4"
        quality = self._quality_presets[self.config.quality_preset]

        # Choose encoder based on hardware availability
        encoder = "libx265"
        if use_hardware and self._check_hardware_hevc_support():
            encoder = "hevc_nvenc"  # NVIDIA hardware encoder

        cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            encoder,
        ]

        if encoder == "libx265":
            # Software encoding with x265
            cmd.extend(
                [
                    "-crf",
                    quality["hevc_crf"],
                    "-preset",
                    "medium",
                    "-x265-params",
                    "log-level=error",
                ]
            )
        else:
            # Hardware encoding
            cmd.extend(
                [
                    "-crf",
                    quality["hevc_crf"],
                    "-preset",
                    "medium",
                ]
            )

        cmd.extend(
            [
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(output_file),
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback to software encoding if hardware fails
            if use_hardware and encoder == "hevc_nvenc":
                return self.encode_hevc(
                    input_path, output_dir, video_id, use_hardware=False
                )
            raise FFmpegError(f"HEVC encoding failed: {result.stderr}")

        if not output_file.exists():
            raise EncodingError("HEVC encoding failed - output file not created")

        return output_file

    def get_av1_bitrate_multiplier(self) -> float:
        """
        Get bitrate multiplier for AV1 encoding.

        AV1 needs significantly less bitrate than H.264 for same quality.
        """
        multiplier = float(
            self._quality_presets[self.config.quality_preset]["bitrate_multiplier"]
        )
        return multiplier

    def _check_av1_support(self) -> bool:
        """Check if FFmpeg has AV1 encoding support."""
        try:
            result = subprocess.run(
                [self.config.ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "libaom-av1" in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_hardware_hevc_support(self) -> bool:
        """Check if hardware HEVC encoding is available."""
        try:
            result = subprocess.run(
                [self.config.ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "hevc_nvenc" in result.stdout or "hevc_qsv" in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def get_supported_advanced_codecs() -> dict[str, bool]:
        """Get information about supported advanced codecs."""
        # This would be populated by actual FFmpeg capability detection
        return {
            "av1": False,  # Will be detected at runtime
            "hevc": False,
            "vp9": True,  # Usually available
            "hardware_hevc": False,
            "hardware_av1": False,
        }


class HDRProcessor:
    """HDR (High Dynamic Range) video processing capabilities."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

    def encode_hdr_hevc(
        self,
        input_path: Path,
        output_dir: Path,
        video_id: str,
        hdr_standard: Literal["hdr10", "hdr10plus", "dolby_vision"] = "hdr10",
    ) -> Path:
        """
        Encode HDR video using HEVC with HDR metadata preservation.

        Args:
            input_path: Input HDR video file
            output_dir: Output directory
            video_id: Unique video identifier
            hdr_standard: HDR standard to use

        Returns:
            Path to encoded HDR file
        """
        output_file = output_dir / f"{video_id}_hdr_{hdr_standard}.mp4"

        cmd = [
            self.config.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libx265",
            "-crf",
            "18",  # High quality for HDR content
            "-preset",
            "slow",  # Better compression for HDR
            "-pix_fmt",
            "yuv420p10le",  # 10-bit encoding for HDR
        ]

        # Add HDR-specific parameters
        if hdr_standard == "hdr10":
            cmd.extend(
                [
                    "-color_primaries",
                    "bt2020",
                    "-color_trc",
                    "smpte2084",
                    "-colorspace",
                    "bt2020nc",
                    "-master-display",
                    "G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)",
                    "-max-cll",
                    "1000,400",
                ]
            )

        cmd.extend(
            [
                "-c:a",
                "aac",
                "-b:a",
                "256k",  # Higher audio quality for HDR content
                str(output_file),
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"HDR encoding failed: {result.stderr}")

        if not output_file.exists():
            raise EncodingError("HDR encoding failed - output file not created")

        return output_file

    def analyze_hdr_content(self, video_path: Path) -> dict[str, any]:
        """
        Analyze video for HDR characteristics.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with HDR analysis results
        """
        try:
            # Use ffprobe to analyze HDR metadata
            result = subprocess.run(
                [
                    self.config.ffmpeg_path.replace("ffmpeg", "ffprobe"),
                    "-v",
                    "quiet",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=color_primaries,color_trc,color_space",
                    "-of",
                    "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                return {
                    "is_hdr": any(
                        part in ["bt2020", "smpte2084", "arib-std-b67"]
                        for part in parts
                    ),
                    "color_primaries": parts[0] if parts else "unknown",
                    "color_transfer": parts[1] if len(parts) > 1 else "unknown",
                    "color_space": parts[2] if len(parts) > 2 else "unknown",
                }

            return {"is_hdr": False, "error": result.stderr}

        except Exception as e:
            return {"is_hdr": False, "error": str(e)}

    @staticmethod
    def get_hdr_support() -> dict[str, bool]:
        """Check what HDR capabilities are available."""
        return {
            "hdr10": True,  # Basic HDR10 support
            "hdr10plus": False,  # Requires special build
            "dolby_vision": False,  # Requires licensed encoder
        }
