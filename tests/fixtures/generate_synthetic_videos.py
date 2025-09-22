"""
Generate synthetic test videos using ffmpeg for specific test scenarios.
Creates specific test scenarios that are hard to find in real videos.
"""

import subprocess
from pathlib import Path


class SyntheticVideoGenerator:
    """Generate synthetic test videos for specific test scenarios."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        """Generate all synthetic test videos."""
        print("🎥 Generating Synthetic Test Videos...")

        # Edge cases
        self.generate_edge_cases()

        # Codec stress tests
        self.generate_codec_tests()

        # Audio tests
        self.generate_audio_tests()

        # Visual pattern tests
        self.generate_pattern_tests()

        # Motion tests
        self.generate_motion_tests()

        # Encoding stress tests
        self.generate_stress_tests()

        print("✅ Synthetic video generation complete!")

    def generate_edge_cases(self):
        """Generate edge case test videos."""
        edge_dir = self.output_dir / "edge_cases"
        edge_dir.mkdir(exist_ok=True)

        # Single frame video
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=640x480:d=0.04",
                "-vframes",
                "1",
                str(edge_dir / "single_frame.mp4"),
            ]
        )
        print("  ✓ Generated: single_frame.mp4")

        # Very long duration but static (low bitrate possible)
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:d=300",  # 5 minutes
                "-c:v",
                "libx264",
                "-crf",
                "51",  # Very high compression
                str(edge_dir / "long_static.mp4"),
            ]
        )
        print("  ✓ Generated: long_static.mp4")

        # Extremely high FPS
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=s=640x480:r=120:d=2",
                "-r",
                "120",
                str(edge_dir / "high_fps_120.mp4"),
            ]
        )
        print("  ✓ Generated: high_fps_120.mp4")

        # Unusual resolutions
        resolutions = [
            ("16x16", "tiny_16x16.mp4"),
            ("100x100", "small_square.mp4"),
            ("1920x2", "line_horizontal.mp4"),
            ("2x1080", "line_vertical.mp4"),
            ("1337x999", "odd_dimensions.mp4"),
        ]

        for resolution, filename in resolutions:
            try:
                self._run_ffmpeg(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"testsrc2=s={resolution}:d=1",
                        str(edge_dir / filename),
                    ]
                )
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename} (resolution not supported)")

        # Extreme aspect ratios
        aspects = [
            ("3840x240", "ultra_wide_16_1.mp4"),
            ("240x3840", "ultra_tall_1_16.mp4"),
        ]

        for spec, filename in aspects:
            try:
                self._run_ffmpeg(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"testsrc2=s={spec}:d=2",
                        str(edge_dir / filename),
                    ]
                )
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename} (aspect ratio not supported)")

    def generate_codec_tests(self):
        """Generate videos with various codecs and encoding parameters."""
        codec_dir = self.output_dir / "codecs"
        codec_dir.mkdir(exist_ok=True)

        # H.264 profiles and levels
        h264_tests = [
            ("baseline", "3.0", "h264_baseline_3_0.mp4"),
            ("main", "4.0", "h264_main_4_0.mp4"),
            ("high", "5.1", "h264_high_5_1.mp4"),
        ]

        for profile, level, filename in h264_tests:
            try:
                self._run_ffmpeg(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc2=s=1280x720:d=3",
                        "-c:v",
                        "libx264",
                        "-profile:v",
                        profile,
                        "-level",
                        level,
                        str(codec_dir / filename),
                    ]
                )
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename} (profile not supported)")

        # Different codecs
        codec_tests = [
            ("libx265", "h265_hevc.mp4", []),
            ("libvpx", "vp8.webm", []),
            ("libvpx-vp9", "vp9.webm", []),
            ("libtheora", "theora.ogv", []),
            ("mpeg4", "mpeg4.mp4", []),
        ]

        for codec, filename, extra_opts in codec_tests:
            try:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=s=1280x720:d=2",
                    "-c:v",
                    codec,
                ]
                cmd.extend(extra_opts)
                cmd.append(str(codec_dir / filename))

                self._run_ffmpeg(cmd)
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename} (codec not available)")

        # Bit depth variations (if x265 available)
        try:
            self._run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=s=1280x720:d=2",
                    "-c:v",
                    "libx265",
                    "-pix_fmt",
                    "yuv420p10le",
                    str(codec_dir / "10bit.mp4"),
                ]
            )
            print("  ✓ Generated: 10bit.mp4")
        except:
            print("  ⚠ Skipped: 10bit.mp4")

    def generate_audio_tests(self):
        """Generate videos with various audio configurations."""
        audio_dir = self.output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        # No audio stream
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=s=640x480:d=3",
                "-an",
                str(audio_dir / "no_audio.mp4"),
            ]
        )
        print("  ✓ Generated: no_audio.mp4")

        # Various audio configurations
        audio_configs = [
            (1, 8000, "mono_8khz.mp4"),
            (1, 22050, "mono_22khz.mp4"),
            (2, 44100, "stereo_44khz.mp4"),
            (2, 48000, "stereo_48khz.mp4"),
        ]

        for channels, sample_rate, filename in audio_configs:
            try:
                self._run_ffmpeg(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc2=s=640x480:d=2",
                        "-f",
                        "lavfi",
                        "-i",
                        f"sine=frequency=440:sample_rate={sample_rate}:duration=2",
                        "-c:v",
                        "libx264",
                        "-c:a",
                        "aac",
                        "-ac",
                        str(channels),
                        "-ar",
                        str(sample_rate),
                        str(audio_dir / filename),
                    ]
                )
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename}")

        # Audio-only file (no video stream)
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=5",
                "-c:a",
                "aac",
                str(audio_dir / "audio_only.mp4"),
            ]
        )
        print("  ✓ Generated: audio_only.mp4")

    def generate_pattern_tests(self):
        """Generate videos with specific visual patterns."""
        pattern_dir = self.output_dir / "patterns"
        pattern_dir.mkdir(exist_ok=True)

        patterns = [
            ("smptebars", "smpte_bars.mp4"),
            ("rgbtestsrc", "rgb_test.mp4"),
            ("yuvtestsrc", "yuv_test.mp4"),
        ]

        for pattern, filename in patterns:
            try:
                self._run_ffmpeg(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"{pattern}=s=1280x720:d=3",
                        str(pattern_dir / filename),
                    ]
                )
                print(f"  ✓ Generated: {filename}")
            except:
                print(f"  ⚠ Skipped: {filename}")

        # Checkerboard pattern
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "nullsrc=s=1280x720:d=3",
                "-vf",
                "geq=lum='if(mod(floor(X/40)+floor(Y/40),2),255,0)'",
                str(pattern_dir / "checkerboard.mp4"),
            ]
        )
        print("  ✓ Generated: checkerboard.mp4")

    def generate_motion_tests(self):
        """Generate videos with specific motion patterns."""
        motion_dir = self.output_dir / "motion"
        motion_dir.mkdir(exist_ok=True)

        # Fast rotation motion
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=s=1280x720:r=30:d=3",
                "-vf",
                "rotate=PI*t",
                str(motion_dir / "fast_rotation.mp4"),
            ]
        )
        print("  ✓ Generated: fast_rotation.mp4")

        # Slow rotation motion
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=s=1280x720:r=30:d=3",
                "-vf",
                "rotate=PI*t/10",
                str(motion_dir / "slow_rotation.mp4"),
            ]
        )
        print("  ✓ Generated: slow_rotation.mp4")

        # Shake effect (simulated camera shake)
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=s=1280x720:r=30:d=3",
                "-vf",
                "crop=in_w-20:in_h-20:10*sin(t*10):10*cos(t*10)",
                str(motion_dir / "camera_shake.mp4"),
            ]
        )
        print("  ✓ Generated: camera_shake.mp4")

        # Scene changes
        try:
            self.create_scene_change_video(motion_dir / "scene_changes.mp4")
            print("  ✓ Generated: scene_changes.mp4")
        except:
            print("  ⚠ Skipped: scene_changes.mp4 (concat not supported)")

    def generate_stress_tests(self):
        """Generate videos that stress test the encoder."""
        stress_dir = self.output_dir / "stress"
        stress_dir.mkdir(exist_ok=True)

        # High complexity scene (mandelbrot fractal)
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "mandelbrot=s=1280x720:r=30",
                "-t",
                "3",
                str(stress_dir / "high_complexity.mp4"),
            ]
        )
        print("  ✓ Generated: high_complexity.mp4")

        # Noise (hard to compress)
        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "noise=alls=100:allf=t",
                "-s",
                "1280x720",
                "-t",
                "3",
                str(stress_dir / "noise_high.mp4"),
            ]
        )
        print("  ✓ Generated: noise_high.mp4")

    def create_scene_change_video(self, output_path: Path):
        """Create a video with multiple scene changes."""
        colors = ["red", "green", "blue", "yellow", "magenta", "cyan", "white", "black"]
        segments = []

        for i, color in enumerate(colors):
            segment_path = output_path.with_suffix(f".seg{i}.mp4")
            self._run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c={color}:s=640x480:d=0.5",
                    str(segment_path),
                ]
            )
            segments.append(str(segment_path))

        # Concatenate
        with open(output_path.with_suffix(".txt"), "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        self._run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(output_path.with_suffix(".txt")),
                "-c",
                "copy",
                str(output_path),
            ]
        )

        # Cleanup
        for seg in segments:
            Path(seg).unlink()
        output_path.with_suffix(".txt").unlink()

    def _run_ffmpeg(self, cmd: list[str]):
        """Run FFmpeg command safely."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            # print(f"FFmpeg error: {e.stderr}")
            raise e


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic test videos")
    parser.add_argument(
        "--output",
        "-o",
        default="tests/fixtures/videos/synthetic",
        help="Output directory",
    )

    args = parser.parse_args()

    generator = SyntheticVideoGenerator(Path(args.output))
    generator.generate_all()
