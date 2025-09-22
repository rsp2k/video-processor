"""
Manage the complete test video suite.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


class TestSuiteManager:
    """Manage test video suite with categorization and validation."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.opensource_dir = self.base_dir / "opensource"
        self.synthetic_dir = self.base_dir / "synthetic"
        self.custom_dir = self.base_dir / "custom"

        # Test categories
        self.categories = {
            "smoke": "Quick smoke tests (< 5 videos)",
            "basic": "Basic functionality tests",
            "codecs": "Codec-specific tests",
            "edge_cases": "Edge cases and boundary conditions",
            "stress": "Stress and performance tests",
            "regression": "Regression test suite",
            "full": "Complete test suite",
        }

        # Test suites
        self.suites = {
            "smoke": [
                "opensource/standard/big_buck_bunny_1080p_30fps.mp4",
                "synthetic/patterns/smpte_bars.mp4",
                "synthetic/edge_cases/single_frame.mp4",
            ],
            "basic": [
                "opensource/standard/*.mp4",
                "opensource/resolutions/*.mp4",
                "synthetic/patterns/*.mp4",
            ],
            "codecs": [
                "synthetic/codecs/*.webm",
                "synthetic/codecs/*.ogv",
                "synthetic/codecs/*.mp4",
            ],
            "edge_cases": [
                "synthetic/edge_cases/*.mp4",
                "synthetic/audio/no_audio.mp4",
                "synthetic/audio/audio_only.mp4",
            ],
            "stress": [
                "synthetic/stress/*.mp4",
                "synthetic/motion/fast_*.mp4",
            ],
        }

    def setup(self):
        """Set up the complete test suite."""
        print("🔧 Setting up test video suite...")

        # Create directories
        for dir_path in [self.opensource_dir, self.synthetic_dir, self.custom_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Download open source videos
        try:
            from download_test_videos import TestVideoDownloader

            downloader = TestVideoDownloader(self.opensource_dir)
            downloader.download_all()
        except Exception as e:
            print(f"⚠ Failed to download opensource videos: {e}")

        # Generate synthetic videos
        try:
            from generate_synthetic_videos import SyntheticVideoGenerator

            generator = SyntheticVideoGenerator(self.synthetic_dir)
            generator.generate_all()
        except Exception as e:
            print(f"⚠ Failed to generate synthetic videos: {e}")

        # Validate suite
        self.validate()

        # Generate test configuration
        self.generate_config()

        print("✅ Test suite setup complete!")

    def validate(self):
        """Validate all test videos are accessible and valid."""
        print("\n🔍 Validating test suite...")

        invalid_files = []
        valid_count = 0

        for ext in ["*.mp4", "*.webm", "*.ogv", "*.mkv", "*.avi"]:
            for video_file in self.base_dir.rglob(ext):
                if self.validate_video(video_file):
                    valid_count += 1
                else:
                    invalid_files.append(video_file)

        print(f"  ✓ Valid videos: {valid_count}")

        if invalid_files:
            print(f"  ✗ Invalid videos: {len(invalid_files)}")
            for f in invalid_files[:5]:  # Show first 5
                print(f"    - {f.relative_to(self.base_dir)}")

        return len(invalid_files) == 0

    def validate_video(self, video_path: Path) -> bool:
        """Validate a single video file."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", str(video_path)],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def generate_config(self):
        """Generate test configuration file."""
        config = {
            "base_dir": str(self.base_dir),
            "categories": self.categories,
            "suites": {},
            "videos": {},
        }

        # Expand suite patterns
        for suite_name, patterns in self.suites.items():
            suite_files = []
            for pattern in patterns:
                if "*" in pattern:
                    # Glob pattern
                    for f in self.base_dir.glob(pattern):
                        if f.is_file():
                            suite_files.append(str(f.relative_to(self.base_dir)))
                else:
                    # Specific file
                    f = self.base_dir / pattern
                    if f.exists():
                        suite_files.append(pattern)

            config["suites"][suite_name] = sorted(set(suite_files))

        # Catalog all videos
        for ext in ["*.mp4", "*.webm", "*.ogv", "*.mkv", "*.avi"]:
            for video_file in self.base_dir.rglob(ext):
                rel_path = str(video_file.relative_to(self.base_dir))
                config["videos"][rel_path] = {
                    "size_mb": video_file.stat().st_size / 1024 / 1024,
                    "hash": self.get_file_hash(video_file),
                }

        # Save configuration
        config_path = self.base_dir / "test_suite.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"\n📋 Test configuration saved to: {config_path}")

        # Print summary
        print("\n📊 Test Suite Summary:")
        for suite_name, files in config["suites"].items():
            print(f"  {suite_name}: {len(files)} videos")
        print(f"  Total: {len(config['videos'])} videos")

        total_size = sum(v["size_mb"] for v in config["videos"].values())
        print(f"  Total size: {total_size:.1f} MB")

    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file (first 1MB for speed)."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            hasher.update(f.read(1024 * 1024))  # First 1MB
        return hasher.hexdigest()[:16]  # Short hash

    def get_suite_videos(self, suite_name: str) -> list[Path]:
        """Get list of videos for a specific test suite."""
        config_path = self.base_dir / "test_suite.json"

        if not config_path.exists():
            self.generate_config()

        with open(config_path) as f:
            config = json.load(f)

        if suite_name not in config["suites"]:
            raise ValueError(f"Unknown suite: {suite_name}")

        return [self.base_dir / p for p in config["suites"][suite_name]]

    def cleanup(self, keep_suite: str | None = None):
        """Clean up test videos, optionally keeping specific suite."""
        if keep_suite:
            # Get videos to keep
            keep_videos = set(self.get_suite_videos(keep_suite))

            # Remove others
            for ext in ["*.mp4", "*.webm", "*.ogv"]:
                for video_file in self.base_dir.rglob(ext):
                    if video_file not in keep_videos:
                        video_file.unlink()

            print(f"✓ Cleaned up, kept {keep_suite} suite ({len(keep_videos)} videos)")
        else:
            # Remove all
            shutil.rmtree(self.base_dir, ignore_errors=True)
            print("✓ Removed all test videos")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage test video suite")
    parser.add_argument("--setup", action="store_true", help="Set up complete suite")
    parser.add_argument(
        "--validate", action="store_true", help="Validate existing suite"
    )
    parser.add_argument("--cleanup", action="store_true", help="Clean up test videos")
    parser.add_argument("--keep", help="Keep specific suite when cleaning")
    parser.add_argument(
        "--base-dir",
        default="tests/fixtures/videos",
        help="Base directory for test videos",
    )

    args = parser.parse_args()

    manager = TestSuiteManager(Path(args.base_dir))

    if args.setup:
        manager.setup()
    elif args.validate:
        manager.validate()
        manager.generate_config()
    elif args.cleanup:
        manager.cleanup(keep_suite=args.keep)
    else:
        parser.print_help()
