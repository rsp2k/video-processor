"""HLS (HTTP Live Streaming) manifest generation and segmentation."""

import asyncio
import logging
import subprocess
from pathlib import Path

from ..exceptions import FFmpegError
from .adaptive import BitrateLevel

logger = logging.getLogger(__name__)


class HLSGenerator:
    """Generates HLS playlists and segments from video renditions."""

    def __init__(self, segment_duration: int = 6) -> None:
        self.segment_duration = segment_duration

    async def create_master_playlist(
        self,
        output_dir: Path,
        video_id: str,
        bitrate_levels: list[BitrateLevel],
        rendition_files: dict[str, Path],
    ) -> Path:
        """
        Create HLS master playlist and segment all renditions.

        Args:
            output_dir: Output directory
            video_id: Video identifier
            bitrate_levels: List of bitrate levels
            rendition_files: Dictionary of rendition name to file path

        Returns:
            Path to master playlist file
        """
        logger.info(f"Creating HLS master playlist for {video_id}")

        # Create HLS directory
        hls_dir = output_dir / "hls"
        hls_dir.mkdir(exist_ok=True)

        # Generate segments for each rendition
        playlist_info = []
        for level in bitrate_levels:
            if level.name in rendition_files:
                playlist_path = await self._create_rendition_playlist(
                    hls_dir, level, rendition_files[level.name]
                )
                playlist_info.append((level, playlist_path))

        # Create master playlist
        master_playlist_path = hls_dir / f"{video_id}.m3u8"
        await self._write_master_playlist(master_playlist_path, playlist_info)

        logger.info(f"HLS master playlist created: {master_playlist_path}")
        return master_playlist_path

    async def _create_rendition_playlist(
        self, hls_dir: Path, level: BitrateLevel, video_file: Path
    ) -> Path:
        """Create individual rendition playlist with segments."""
        rendition_dir = hls_dir / level.name
        rendition_dir.mkdir(exist_ok=True)

        playlist_path = rendition_dir / f"{level.name}.m3u8"
        segment_pattern = rendition_dir / f"{level.name}_%03d.ts"

        # Use FFmpeg to create HLS segments
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-c",
            "copy",  # Copy without re-encoding
            "-hls_time",
            str(self.segment_duration),
            "-hls_playlist_type",
            "vod",
            "-hls_segment_filename",
            str(segment_pattern),
            str(playlist_path),
        ]

        try:
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, check=True
            )
            logger.info(f"HLS segments created for {level.name}")
            return playlist_path

        except subprocess.CalledProcessError as e:
            error_msg = f"HLS segmentation failed for {level.name}: {e.stderr}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)

    async def _write_master_playlist(
        self, master_path: Path, playlist_info: list[tuple]
    ) -> None:
        """Write HLS master playlist file."""
        lines = ["#EXTM3U", "#EXT-X-VERSION:6"]

        for level, playlist_path in playlist_info:
            # Calculate relative path from master playlist to rendition playlist
            rel_path = playlist_path.relative_to(master_path.parent)

            lines.extend(
                [
                    f"#EXT-X-STREAM-INF:BANDWIDTH={level.bitrate * 1000},"
                    f"RESOLUTION={level.width}x{level.height},"
                    f'CODECS="{self._get_hls_codec_string(level.codec)}"',
                    str(rel_path),
                ]
            )

        content = "\n".join(lines) + "\n"

        await asyncio.to_thread(master_path.write_text, content)
        logger.info(f"Master playlist written with {len(playlist_info)} renditions")

    def _get_hls_codec_string(self, codec: str) -> str:
        """Get HLS codec string for manifest."""
        codec_strings = {
            "h264": "avc1.42E01E",
            "hevc": "hev1.1.6.L93.B0",
            "av1": "av01.0.05M.08",
        }
        return codec_strings.get(codec, "avc1.42E01E")


class HLSLiveGenerator:
    """Generates live HLS streams from real-time input."""

    def __init__(self, segment_duration: int = 6, playlist_size: int = 10) -> None:
        self.segment_duration = segment_duration
        self.playlist_size = playlist_size  # Number of segments to keep in playlist

    async def start_live_stream(
        self,
        input_source: str,  # RTMP URL, camera device, etc.
        output_dir: Path,
        stream_name: str,
        bitrate_levels: list[BitrateLevel],
    ) -> None:
        """
        Start live HLS streaming from input source.

        Args:
            input_source: Input source (RTMP, file, device)
            output_dir: Output directory for HLS files
            stream_name: Name of the stream
            bitrate_levels: Bitrate levels for ABR streaming
        """
        logger.info(f"Starting live HLS stream: {stream_name}")

        # Create output directory
        hls_dir = output_dir / "live" / stream_name
        hls_dir.mkdir(parents=True, exist_ok=True)

        # Start FFmpeg process for live streaming
        tasks = []
        for level in bitrate_levels:
            task = asyncio.create_task(
                self._start_live_rendition(input_source, hls_dir, level)
            )
            tasks.append(task)

        # Create master playlist
        master_playlist = hls_dir / f"{stream_name}.m3u8"
        await self._create_live_master_playlist(master_playlist, bitrate_levels)

        # Wait for all streaming processes
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Live streaming error: {e}")
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            raise

    async def _start_live_rendition(
        self, input_source: str, hls_dir: Path, level: BitrateLevel
    ) -> None:
        """Start live streaming for a single bitrate level."""
        rendition_dir = hls_dir / level.name
        rendition_dir.mkdir(exist_ok=True)

        playlist_path = rendition_dir / f"{level.name}.m3u8"
        segment_pattern = rendition_dir / f"{level.name}_%03d.ts"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_source,
            "-c:v",
            self._get_encoder_for_codec(level.codec),
            "-b:v",
            f"{level.bitrate}k",
            "-maxrate",
            f"{level.max_bitrate}k",
            "-s",
            f"{level.width}x{level.height}",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "hls",
            "-hls_time",
            str(self.segment_duration),
            "-hls_list_size",
            str(self.playlist_size),
            "-hls_flags",
            "delete_segments",
            "-hls_segment_filename",
            str(segment_pattern),
            str(playlist_path),
        ]

        logger.info(f"Starting live encoding for {level.name}")

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
                error_msg = f"Live streaming failed for {level.name}: {stderr.decode()}"
                logger.error(error_msg)
                raise FFmpegError(error_msg)

        except Exception as e:
            logger.error(f"Live rendition error for {level.name}: {e}")
            raise

    async def _create_live_master_playlist(
        self, master_path: Path, bitrate_levels: list[BitrateLevel]
    ) -> None:
        """Create master playlist for live streaming."""
        lines = ["#EXTM3U", "#EXT-X-VERSION:6"]

        for level in bitrate_levels:
            rel_path = f"{level.name}/{level.name}.m3u8"
            lines.extend(
                [
                    f"#EXT-X-STREAM-INF:BANDWIDTH={level.bitrate * 1000},"
                    f"RESOLUTION={level.width}x{level.height},"
                    f'CODECS="{self._get_hls_codec_string(level.codec)}"',
                    rel_path,
                ]
            )

        content = "\n".join(lines) + "\n"
        await asyncio.to_thread(master_path.write_text, content)
        logger.info("Live master playlist created")

    def _get_encoder_for_codec(self, codec: str) -> str:
        """Get FFmpeg encoder for codec."""
        encoders = {
            "h264": "libx264",
            "hevc": "libx265",
            "av1": "libaom-av1",
        }
        return encoders.get(codec, "libx264")

    def _get_hls_codec_string(self, codec: str) -> str:
        """Get HLS codec string for manifest."""
        codec_strings = {
            "h264": "avc1.42E01E",
            "hevc": "hev1.1.6.L93.B0",
            "av1": "av01.0.05M.08",
        }
        return codec_strings.get(codec, "avc1.42E01E")
