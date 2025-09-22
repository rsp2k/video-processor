"""DASH (Dynamic Adaptive Streaming over HTTP) manifest generation."""

import asyncio
import logging
import subprocess
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from ..exceptions import FFmpegError
from .adaptive import BitrateLevel

logger = logging.getLogger(__name__)


class DASHGenerator:
    """Generates DASH MPD manifests and segments from video renditions."""

    def __init__(self, segment_duration: int = 4) -> None:
        self.segment_duration = segment_duration

    async def create_manifest(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel],
        rendition_files: dict[str, Path],
    ) -> Path:
        """
        Create DASH MPD manifest and segment all renditions.

        Args:
            output_dir: Output directory
            video_id: Video identifier
            bitrate_levels: List of bitrate levels
            rendition_files: Dictionary of rendition name to file path

        Returns:
            Path to MPD manifest file
        """
        logger.info(f"Creating DASH manifest for {video_id}")

        # Create DASH directory
        dash_dir = output_dir / "dash"
        dash_dir.mkdir(exist_ok=True)

        # Generate DASH segments for each rendition
        adaptation_sets = []
        for level in bitrate_levels:
            if level.name in rendition_files:
                segments_info = await self._create_dash_segments(
                    dash_dir, level, rendition_files[level.name]
                )
                adaptation_sets.append((level, segments_info))

        # Create MPD manifest
        manifest_path = dash_dir / f"{video_id}.mpd"
        await self._create_mpd_manifest(manifest_path, video_id, adaptation_sets)

        logger.info(f"DASH manifest created: {manifest_path}")
        return manifest_path

    async def _create_dash_segments(
        self, dash_dir: Path, level: BitrateLevel, video_file: Path
    ) -> dict:
        """Create DASH segments for a single bitrate level."""
        rendition_dir = dash_dir / level.name
        rendition_dir.mkdir(exist_ok=True)

        # DASH segment pattern
        init_segment = rendition_dir / f"{level.name}_init.mp4"
        segment_pattern = rendition_dir / f"{level.name}_$Number$.m4s"

        # Use FFmpeg to create DASH segments
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-c",
            "copy",  # Copy without re-encoding
            "-f",
            "dash",
            "-seg_duration",
            str(self.segment_duration),
            "-init_seg_name",
            str(init_segment.name),
            "-media_seg_name",
            f"{level.name}_$Number$.m4s",
            "-single_file",
            "0",  # Create separate segment files
            str(rendition_dir / f"{level.name}.mpd"),
        ]

        try:
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, check=True
            )

            # Get duration and segment count from the created files
            segments_info = await self._analyze_dash_segments(rendition_dir, level.name)
            logger.info(f"DASH segments created for {level.name}")
            return segments_info

        except subprocess.CalledProcessError as e:
            error_msg = f"DASH segmentation failed for {level.name}: {e.stderr}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)

    async def _analyze_dash_segments(
        self, rendition_dir: Path, rendition_name: str
    ) -> dict:
        """Analyze created DASH segments to get metadata."""
        # Count segment files
        segment_files = list(rendition_dir.glob(f"{rendition_name}_*.m4s"))
        segment_count = len(segment_files)

        # Get duration from FFprobe
        try:
            # Find the first video file in the directory (should be the source)
            video_files = list(rendition_dir.glob("*.mp4"))
            if video_files:
                duration = await self._get_video_duration(video_files[0])
            else:
                duration = segment_count * self.segment_duration  # Estimate

        except Exception as e:
            logger.warning(f"Could not get exact duration: {e}")
            duration = segment_count * self.segment_duration

        return {
            "segment_count": segment_count,
            "duration": duration,
            "init_segment": f"{rendition_name}_init.mp4",
            "media_template": f"{rendition_name}_$Number$.m4s",
        }

    async def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video_path),
        ]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        return float(result.stdout.strip())

    async def _create_mpd_manifest(
        self, manifest_path: Path, video_id: str, adaptation_sets: list[tuple]
    ) -> None:
        """Create DASH MPD manifest XML."""
        # Calculate total duration (use first adaptation set)
        if adaptation_sets:
            total_duration = adaptation_sets[0][1]["duration"]
        else:
            total_duration = 0

        # Create MPD root element
        mpd = ET.Element("MPD")
        mpd.set("xmlns", "urn:mpeg:dash:schema:mpd:2011")
        mpd.set("type", "static")
        mpd.set("mediaPresentationDuration", self._format_duration(total_duration))
        mpd.set("profiles", "urn:mpeg:dash:profile:isoff-on-demand:2011")
        mpd.set("minBufferTime", f"PT{self.segment_duration}S")

        # Add publishing time
        now = datetime.now(UTC)
        mpd.set("publishTime", now.isoformat().replace("+00:00", "Z"))

        # Create Period element
        period = ET.SubElement(mpd, "Period")
        period.set("id", "0")
        period.set("duration", self._format_duration(total_duration))

        # Group by codec for adaptation sets
        codec_groups = {}
        for level, segments_info in adaptation_sets:
            if level.codec not in codec_groups:
                codec_groups[level.codec] = []
            codec_groups[level.codec].append((level, segments_info))

        # Create adaptation sets
        adaptation_set_id = 0
        for codec, levels in codec_groups.items():
            adaptation_set = ET.SubElement(period, "AdaptationSet")
            adaptation_set.set("id", str(adaptation_set_id))
            adaptation_set.set("contentType", "video")
            adaptation_set.set("mimeType", "video/mp4")
            adaptation_set.set("codecs", self._get_dash_codec_string(codec))
            adaptation_set.set("startWithSAP", "1")
            adaptation_set.set("segmentAlignment", "true")

            # Add representations for each bitrate level
            representation_id = 0
            for level, segments_info in levels:
                representation = ET.SubElement(adaptation_set, "Representation")
                representation.set("id", f"{adaptation_set_id}_{representation_id}")
                representation.set("bandwidth", str(level.bitrate * 1000))
                representation.set("width", str(level.width))
                representation.set("height", str(level.height))
                representation.set("frameRate", "25")  # Default frame rate

                # Add segment template
                segment_template = ET.SubElement(representation, "SegmentTemplate")
                segment_template.set("timescale", "1000")
                segment_template.set("duration", str(self.segment_duration * 1000))
                segment_template.set(
                    "initialization", f"{level.name}/{segments_info['init_segment']}"
                )
                segment_template.set(
                    "media", f"{level.name}/{segments_info['media_template']}"
                )
                segment_template.set("startNumber", "1")

                representation_id += 1

            adaptation_set_id += 1

        # Write XML to file
        tree = ET.ElementTree(mpd)
        ET.indent(tree, space="  ", level=0)  # Pretty print

        await asyncio.to_thread(
            tree.write, manifest_path, encoding="utf-8", xml_declaration=True
        )

        logger.info(f"MPD manifest written with {len(adaptation_sets)} representations")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in ISO 8601 format for DASH."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"PT{hours}H{minutes}M{secs:.3f}S"

    def _get_dash_codec_string(self, codec: str) -> str:
        """Get DASH codec string for manifest."""
        codec_strings = {
            "h264": "avc1.42E01E",
            "hevc": "hev1.1.6.L93.B0",
            "av1": "av01.0.05M.08",
        }
        return codec_strings.get(codec, "avc1.42E01E")


class DASHLiveGenerator:
    """Generates live DASH streams."""

    def __init__(self, segment_duration: int = 4, time_shift_buffer: int = 300) -> None:
        self.segment_duration = segment_duration
        self.time_shift_buffer = time_shift_buffer  # DVR window in seconds

    async def start_live_stream(
        self,
        input_source: str,
        output_dir: Path,
        stream_name: str,
        bitrate_levels: list[BitrateLevel],
    ) -> None:
        """
        Start live DASH streaming.

        Args:
            input_source: Input source (RTMP, file, device)
            output_dir: Output directory
            stream_name: Name of the stream
            bitrate_levels: Bitrate levels for ABR streaming
        """
        logger.info(f"Starting live DASH stream: {stream_name}")

        # Create output directory
        dash_dir = output_dir / "dash_live" / stream_name
        dash_dir.mkdir(parents=True, exist_ok=True)

        # Use FFmpeg to generate live DASH stream with multiple bitrates
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_source,
            "-f",
            "dash",
            "-seg_duration",
            str(self.segment_duration),
            "-window_size",
            str(self.time_shift_buffer // self.segment_duration),
            "-extra_window_size",
            "5",
            "-remove_at_exit",
            "1",
        ]

        # Add video streams for each bitrate level
        for i, level in enumerate(bitrate_levels):
            cmd.extend(
                [
                    "-map",
                    "0:v:0",
                    f"-c:v:{i}",
                    self._get_encoder_for_codec(level.codec),
                    f"-b:v:{i}",
                    f"{level.bitrate}k",
                    f"-maxrate:v:{i}",
                    f"{level.max_bitrate}k",
                    f"-s:v:{i}",
                    f"{level.width}x{level.height}",
                ]
            )

        # Add audio stream
        cmd.extend(
            [
                "-map",
                "0:a:0",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
            ]
        )

        # Output
        manifest_path = dash_dir / f"{stream_name}.mpd"
        cmd.append(str(manifest_path))

        logger.info("Starting live DASH encoding")

        try:
            # Start FFmpeg process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Monitor process
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = f"Live DASH streaming failed: {stderr.decode()}"
                logger.error(error_msg)
                raise FFmpegError(error_msg)

        except Exception as e:
            logger.error(f"Live DASH stream error: {e}")
            raise

    def _get_encoder_for_codec(self, codec: str) -> str:
        """Get FFmpeg encoder for codec."""
        encoders = {
            "h264": "libx264",
            "hevc": "libx265",
            "av1": "libaom-av1",
        }
        return encoders.get(codec, "libx264")
