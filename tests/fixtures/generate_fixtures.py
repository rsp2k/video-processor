#!/usr/bin/env python3
"""
Generate test video files for comprehensive testing.
Requires: ffmpeg installed on system
"""

import os
import subprocess
from pathlib import Path


class TestVideoGenerator:
    """Generate various test videos for comprehensive testing."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.valid_dir = self.output_dir / "valid"
        self.corrupt_dir = self.output_dir / "corrupt"
        self.edge_cases_dir = self.output_dir / "edge_cases"

        # Create directories
        for dir_path in [self.valid_dir, self.corrupt_dir, self.edge_cases_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        """Generate all test fixtures."""
        print("🎬 Generating test videos...")

        # Check FFmpeg availability
        if not self._check_ffmpeg():
            print("❌ FFmpeg not found. Please install FFmpeg.")
            return False

        try:
            # Valid videos
            self.generate_standard_videos()
            self.generate_resolution_variants()
            self.generate_format_variants()
            self.generate_audio_variants()

            # Edge cases
            self.generate_edge_cases()

            # Corrupt videos
            self.generate_corrupt_videos()

            print("✅ Test fixtures generated successfully!")
            return True

        except Exception as e:
            print(f"❌ Error generating fixtures: {e}")
            return False

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def generate_standard_videos(self):
        """Generate standard test videos in common formats."""
        formats = {
            "standard_h264.mp4": {
                "codec": "libx264",
                "duration": 10,
                "resolution": "1280x720",
                "fps": 30,
                "audio": True,
            },
            "standard_short.mp4": {
                "codec": "libx264",
                "duration": 5,
                "resolution": "640x480",
                "fps": 24,
                "audio": True,
            },
            "standard_vp9.webm": {
                "codec": "libvpx-vp9",
                "duration": 5,
                "resolution": "854x480",
                "fps": 24,
                "audio": True,
            },
        }

        for filename, params in formats.items():
            output_path = self.valid_dir / filename
            if self._create_video(output_path, **params):
                print(f"  ✓ Generated: {filename}")
            else:
                print(f"  ⚠ Failed: {filename}")

    def generate_format_variants(self):
        """Generate videos in various container formats."""
        formats = ["mp4", "webm", "ogv"]

        for fmt in formats:
            output_path = self.valid_dir / f"format_{fmt}.{fmt}"

            # Choose appropriate codec for format
            codec_map = {"mp4": "libx264", "webm": "libvpx", "ogv": "libtheora"}

            if self._create_video(
                output_path,
                codec=codec_map.get(fmt, "libx264"),
                duration=3,
                resolution="640x480",
                fps=24,
                audio=True,
            ):
                print(f"  ✓ Format variant: {fmt}")
            else:
                print(f"  ⚠ Skipped {fmt}: codec not available")

    def generate_resolution_variants(self):
        """Generate videos with various resolutions."""
        resolutions = {
            "1080p.mp4": "1920x1080",
            "720p.mp4": "1280x720",
            "480p.mp4": "854x480",
            "360p.mp4": "640x360",
            "vertical.mp4": "720x1280",  # 9:16 vertical
            "square.mp4": "720x720",  # 1:1 square
            "tiny_resolution.mp4": "128x96",  # Very small
        }

        for filename, resolution in resolutions.items():
            output_path = self.valid_dir / filename
            if self._create_video(
                output_path,
                codec="libx264",
                duration=3,
                resolution=resolution,
                fps=30,
                audio=True,
            ):
                print(f"  ✓ Resolution: {filename} ({resolution})")

    def generate_audio_variants(self):
        """Generate videos with various audio configurations."""
        variants = {
            "no_audio.mp4": {"audio": False},
            "stereo.mp4": {"audio": True, "audio_channels": 2},
            "mono.mp4": {"audio": True, "audio_channels": 1},
        }

        for filename, params in variants.items():
            output_path = self.valid_dir / filename
            if self._create_video(
                output_path,
                codec="libx264",
                duration=3,
                resolution="640x480",
                fps=24,
                **params,
            ):
                print(f"  ✓ Audio variant: {filename}")

    def generate_edge_cases(self):
        """Generate edge case videos."""

        # Very short video (1 frame)
        if self._create_video(
            self.edge_cases_dir / "one_frame.mp4",
            codec="libx264",
            duration=0.033,  # ~1 frame at 30fps
            resolution="640x480",
            fps=30,
            audio=False,
        ):
            print("  ✓ Edge case: one_frame.mp4")

        # High FPS video
        if self._create_video(
            self.edge_cases_dir / "high_fps.mp4",
            codec="libx264",
            duration=2,
            resolution="640x480",
            fps=60,
            extra_args="-preset ultrafast",
        ):
            print("  ✓ Edge case: high_fps.mp4")

        # Only audio, no video
        if self._create_audio_only(self.edge_cases_dir / "audio_only.mp4", duration=3):
            print("  ✓ Edge case: audio_only.mp4")

        # Long duration but small file (low quality)
        if self._create_video(
            self.edge_cases_dir / "long_duration.mp4",
            codec="libx264",
            duration=60,  # 1 minute
            resolution="320x240",
            fps=15,
            extra_args="-b:v 50k -preset ultrafast",  # Very low bitrate
        ):
            print("  ✓ Edge case: long_duration.mp4")

    def generate_corrupt_videos(self):
        """Generate corrupted/broken video files for error testing."""

        # Empty file
        empty_file = self.corrupt_dir / "empty.mp4"
        empty_file.touch()
        print("  ✓ Corrupt: empty.mp4")

        # Text file with video extension
        text_as_video = self.corrupt_dir / "text_file.mp4"
        with open(text_as_video, "w") as f:
            f.write("This is not a video file!\n" * 100)
        print("  ✓ Corrupt: text_file.mp4")

        # Random bytes file with .mp4 extension
        random_bytes = self.corrupt_dir / "random_bytes.mp4"
        with open(random_bytes, "wb") as f:
            f.write(os.urandom(1024 * 5))  # 5KB of random data
        print("  ✓ Corrupt: random_bytes.mp4")

        # Create and then truncate a video
        truncated = self.corrupt_dir / "truncated.mp4"
        if self._create_video(
            truncated, codec="libx264", duration=5, resolution="640x480", fps=24
        ):
            # Truncate to 1KB
            with open(truncated, "r+b") as f:
                f.truncate(1024)
            print("  ✓ Corrupt: truncated.mp4")

        # Create a file with bad header
        bad_header = self.corrupt_dir / "bad_header.mp4"
        if self._create_video(
            bad_header, codec="libx264", duration=3, resolution="640x480", fps=24
        ):
            # Corrupt the header
            with open(bad_header, "r+b") as f:
                f.seek(4)  # Skip 'ftyp' marker
                f.write(b"XXXX")  # Corrupt the brand
            print("  ✓ Corrupt: bad_header.mp4")

    def _create_video(
        self,
        output_path: Path,
        codec: str,
        duration: float,
        resolution: str,
        fps: int = 24,
        audio: bool = True,
        audio_channels: int = 2,
        audio_rate: int = 44100,
        extra_args: str = "",
    ) -> bool:
        """Create a test video using FFmpeg."""

        width, height = map(int, resolution.split("x"))

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={width}x{height}:rate={fps}:duration={duration}",
        ]

        # Add audio input if needed
        if audio:
            cmd.extend(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency=440:sample_rate={audio_rate}:duration={duration}",
                ]
            )

        # Video encoding
        cmd.extend(["-c:v", codec])

        # Add extra arguments if provided
        if extra_args:
            cmd.extend(extra_args.split())

        # Audio encoding or disable
        if audio:
            cmd.extend(
                [
                    "-c:a",
                    "aac",
                    "-ac",
                    str(audio_channels),
                    "-ar",
                    str(audio_rate),
                    "-b:a",
                    "128k",
                ]
            )
        else:
            cmd.extend(["-an"])  # No audio

        # Pixel format for compatibility
        cmd.extend(["-pix_fmt", "yuv420p"])

        # Output file
        cmd.append(str(output_path))

        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=30,  # 30 second timeout
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _create_audio_only(self, output_path: Path, duration: float) -> bool:
        """Create an audio-only file."""
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={duration}",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=15)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


def main():
    """Main function to generate all fixtures."""
    fixtures_dir = Path(__file__).parent / "videos"
    generator = TestVideoGenerator(fixtures_dir)

    print("🎬 Video Processor Test Fixture Generator")
    print("=========================================")

    success = generator.generate_all()

    if success:
        print(f"\n✅ Test fixtures created in: {fixtures_dir}")
        print("\nGenerated fixture summary:")

        total_files = 0
        total_size = 0

        for subdir in ["valid", "corrupt", "edge_cases"]:
            subdir_path = fixtures_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.iterdir())
                size = sum(f.stat().st_size for f in files if f.is_file())
                total_files += len(files)
                total_size += size
                print(f"  {subdir}/: {len(files)} files ({size / 1024 / 1024:.1f} MB)")

        print(f"\nTotal: {total_files} files ({total_size / 1024 / 1024:.1f} MB)")
    else:
        print("\n❌ Failed to generate test fixtures")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
