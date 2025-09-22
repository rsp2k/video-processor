#!/usr/bin/env python3
"""
Download and prepare 360° test videos from open sources.

This module implements a comprehensive 360° video downloader that sources
test content from various platforms and prepares it for testing with proper
spherical metadata injection.
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path

from tqdm import tqdm

logger = logging.getLogger(__name__)


class Video360Downloader:
    """Download and prepare 360° test videos from curated sources."""

    # Curated 360° video sources with proper licensing
    VIDEO_360_SOURCES = {
        # YouTube 360° samples (Creative Commons)
        "youtube_360": {
            "urls": {
                # These require yt-dlp for download
                "swiss_alps_4k": "https://www.youtube.com/watch?v=tO01J-M3g0U",
                "diving_coral_reef": "https://www.youtube.com/watch?v=v64KOxKVLVg",
                "space_walk_nasa": "https://www.youtube.com/watch?v=qhLExhpXX0E",
                "aurora_borealis": "https://www.youtube.com/watch?v=WEeqHj3Nj2c",
            },
            "license": "CC-BY",
            "description": "YouTube 360° Creative Commons content",
            "trim": (30, 45),  # 15-second segments
            "priority": "high",
        },
        # Insta360 sample footage
        "insta360_samples": {
            "urls": {
                "insta360_one_x2": "https://file.insta360.com/static/infr/common/video/P0040087.MP4",
                "insta360_pro": "https://file.insta360.com/static/8k_sample.mp4",
                "tiny_planet": "https://file.insta360.com/static/tiny_planet_sample.mp4",
            },
            "license": "Sample Content",
            "description": "Insta360 camera samples",
            "trim": (0, 10),
            "priority": "medium",
        },
        # GoPro MAX samples
        "gopro_360": {
            "urls": {
                "gopro_max_360": "https://gopro.com/media/360_sample.mp4",
                "gopro_fusion": "https://gopro.com/media/fusion_sample.mp4",
            },
            "license": "Sample Content",
            "description": "GoPro 360° samples",
            "trim": (5, 15),
            "priority": "medium",
        },
        # Facebook/Meta 360 samples
        "facebook_360": {
            "urls": {
                "fb360_spatial": "https://github.com/facebook/360-Capture-SDK/raw/master/Samples/StitchedRenders/sample_360_equirect.mp4",
                "fb360_cubemap": "https://github.com/facebook/360-Capture-SDK/raw/master/Samples/CubemapRenders/sample_cubemap.mp4",
            },
            "license": "MIT/BSD",
            "description": "Facebook 360 Capture SDK samples",
            "trim": None,  # Usually short
            "priority": "high",
        },
        # Google VR samples
        "google_vr": {
            "urls": {
                "cardboard_demo": "https://storage.googleapis.com/cardboard/sample_360.mp4",
                "daydream_sample": "https://storage.googleapis.com/daydream/sample_360_equirect.mp4",
            },
            "license": "Apache 2.0",
            "description": "Google VR/Cardboard samples",
            "trim": (0, 10),
            "priority": "high",
        },
        # Open source 360° content
        "opensource_360": {
            "urls": {
                "blender_360": "https://download.blender.org/demo/vr/BlenderVR_360_stereo.mp4",
                "three_js_demo": "https://threejs.org/examples/textures/video/360_test.mp4",
                "webgl_sample": "https://webglsamples.org/assets/360_equirectangular.mp4",
            },
            "license": "CC-BY/MIT",
            "description": "Open source 360° demos",
            "trim": (0, 15),
            "priority": "medium",
        },
        # Archive.org 360° content
        "archive_360": {
            "urls": {
                "vintage_vr": "https://archive.org/download/360video_201605/360_video_sample.mp4",
                "stereo_3d_360": "https://archive.org/download/3d_360_test/3d_360_video.mp4",
                "historical_360": "https://archive.org/download/historical_360_collection/sample_360.mp4",
            },
            "license": "Public Domain",
            "description": "Archive.org 360° videos",
            "trim": (10, 25),
            "priority": "low",
        },
    }

    # Different 360° formats to ensure comprehensive testing
    VIDEO_360_FORMATS = {
        "projections": [
            "equirectangular",  # Standard 360° format
            "cubemap",  # 6 faces cube projection
            "eac",  # Equi-Angular Cubemap (YouTube)
            "fisheye",  # Dual fisheye (raw camera)
            "stereoscopic_lr",  # 3D left-right
            "stereoscopic_tb",  # 3D top-bottom
        ],
        "resolutions": [
            "3840x1920",  # 4K 360°
            "5760x2880",  # 6K 360°
            "7680x3840",  # 8K 360°
            "2880x2880",  # 3K×3K per eye (stereo)
            "3840x3840",  # 4K×4K per eye (stereo)
        ],
        "metadata_types": [
            "spherical",  # YouTube spherical metadata
            "st3d",  # Stereoscopic 3D metadata
            "sv3d",  # Spherical video 3D
            "mesh",  # Projection mesh data
        ],
    }

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create category directories
        self.dirs = {
            "equirectangular": self.output_dir / "equirectangular",
            "cubemap": self.output_dir / "cubemap",
            "stereoscopic": self.output_dir / "stereoscopic",
            "raw_camera": self.output_dir / "raw_camera",
            "spatial_audio": self.output_dir / "spatial_audio",
            "metadata_tests": self.output_dir / "metadata_tests",
            "high_resolution": self.output_dir / "high_resolution",
            "edge_cases": self.output_dir / "edge_cases",
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Track download status
        self.download_log = []
        self.failed_downloads = []

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        dependencies = {
            "yt-dlp": "yt-dlp --version",
            "ffmpeg": "ffmpeg -version",
            "ffprobe": "ffprobe -version",
        }

        missing = []
        for name, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True)
                if result.returncode != 0:
                    missing.append(name)
            except FileNotFoundError:
                missing.append(name)

        if missing:
            logger.error(f"Missing dependencies: {missing}")
            print(f"⚠️  Missing dependencies: {missing}")
            print("Install with:")
            if "yt-dlp" in missing:
                print("  pip install yt-dlp")
            if "ffmpeg" in missing or "ffprobe" in missing:
                print("  # Install FFmpeg from https://ffmpeg.org/")
            return False

        return True

    async def download_youtube_360(self, url: str, output_path: Path) -> bool:
        """Download 360° video from YouTube using yt-dlp."""
        try:
            # Use yt-dlp to download best quality 360° video
            cmd = [
                "yt-dlp",
                "-f",
                "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format",
                "mp4",
                "-o",
                str(output_path),
                "--no-playlist",
                "--embed-metadata",  # Embed metadata
                "--write-info-json",  # Save metadata
                url,
            ]

            logger.info(f"Downloading from YouTube: {url}")
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully downloaded: {output_path.name}")
                return True
            else:
                logger.error(f"yt-dlp failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return False

    async def download_file(
        self, url: str, output_path: Path, timeout: int = 120
    ) -> bool:
        """Download file with progress bar and timeout."""
        if output_path.exists():
            logger.info(f"Already exists: {output_path.name}")
            return True

        try:
            logger.info(f"Downloading: {url}")

            # Use aiohttp for async downloading
            import aiofiles
            import aiohttp

            timeout_config = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"HTTP {response.status}: {url}")
                        return False

                    total_size = int(response.headers.get("content-length", 0))

                    async with aiofiles.open(output_path, "wb") as f:
                        downloaded = 0

                        with tqdm(
                            total=total_size,
                            unit="B",
                            unit_scale=True,
                            desc=output_path.name,
                        ) as pbar:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                pbar.update(len(chunk))

            logger.info(f"Downloaded: {output_path.name}")
            return True

        except Exception as e:
            logger.error(f"Download failed {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            return False

    def inject_spherical_metadata(self, video_path: Path) -> bool:
        """Inject spherical metadata into video file using FFmpeg."""
        try:
            # First, check if video already has metadata
            if self.has_spherical_metadata(video_path):
                logger.info(f"Already has spherical metadata: {video_path.name}")
                return True

            # Use FFmpeg to add spherical metadata
            temp_path = video_path.with_suffix(".temp.mp4")

            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-c",
                "copy",
                "-metadata:s:v:0",
                "spherical=1",
                "-metadata:s:v:0",
                "stitched=1",
                "-metadata:s:v:0",
                "projection=equirectangular",
                "-metadata:s:v:0",
                "source_count=1",
                "-metadata:s:v:0",
                "init_view_heading=0",
                "-metadata:s:v:0",
                "init_view_pitch=0",
                "-metadata:s:v:0",
                "init_view_roll=0",
                str(temp_path),
                "-y",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Replace original with metadata version
                video_path.unlink()
                temp_path.rename(video_path)
                logger.info(f"Injected spherical metadata: {video_path.name}")
                return True
            else:
                logger.error(f"FFmpeg metadata injection failed: {result.stderr}")
                if temp_path.exists():
                    temp_path.unlink()
                return False

        except Exception as e:
            logger.error(f"Metadata injection failed: {e}")
            return False

    def has_spherical_metadata(self, video_path: Path) -> bool:
        """Check if video has spherical metadata."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        # Check for spherical tags
                        tags = stream.get("tags", {})
                        spherical_tags = [
                            "spherical",
                            "Spherical",
                            "projection",
                            "Projection",
                        ]
                        if any(tag in tags for tag in spherical_tags):
                            return True

        except Exception as e:
            logger.warning(f"Failed to check metadata: {e}")

        return False

    def trim_video(self, video_path: Path, start: float, duration: float) -> bool:
        """Trim video to specified duration."""
        temp_path = video_path.with_suffix(".trimmed.mp4")

        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            str(temp_path),
            "-y",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                video_path.unlink()
                temp_path.rename(video_path)
                logger.info(f"Trimmed to {duration}s: {video_path.name}")
                return True
            else:
                logger.error(f"Trim failed: {result.stderr}")
                if temp_path.exists():
                    temp_path.unlink()
                return False

        except Exception as e:
            logger.error(f"Trim error: {e}")
            return False

    def categorize_video(self, filename: str, source_info: dict) -> Path:
        """Determine which category directory to use for a video."""
        filename_lower = filename.lower()

        if (
            "stereo" in filename_lower
            or "3d" in filename_lower
            or "sbs" in filename_lower
            or "tb" in filename_lower
        ):
            return self.dirs["stereoscopic"]
        elif "cubemap" in filename_lower or "cube" in filename_lower:
            return self.dirs["cubemap"]
        elif "spatial" in filename_lower or "ambisonic" in filename_lower:
            return self.dirs["spatial_audio"]
        elif "8k" in filename_lower or "4320p" in filename_lower:
            return self.dirs["high_resolution"]
        elif "raw" in filename_lower or "fisheye" in filename_lower:
            return self.dirs["raw_camera"]
        else:
            return self.dirs["equirectangular"]

    async def download_category(self, category: str, info: dict) -> list[Path]:
        """Download all videos from a specific category."""
        downloaded_files = []

        print(f"\n📦 Downloading {category} ({info['description']}):")
        print(f"   License: {info['license']}")

        for name, url in info["urls"].items():
            try:
                # Determine output directory and filename
                out_dir = self.categorize_video(name, info)
                filename = f"{category}_{name}.mp4"
                output_path = out_dir / filename

                # Download based on source type
                success = False
                if "youtube.com" in url or "youtu.be" in url:
                    success = await self.download_youtube_360(url, output_path)
                else:
                    success = await self.download_file(url, output_path)

                if success and output_path.exists():
                    # Inject spherical metadata
                    self.inject_spherical_metadata(output_path)

                    # Trim if specified
                    if info.get("trim") and output_path.exists():
                        start, end = info["trim"]
                        duration = end - start
                        if duration > 0:
                            self.trim_video(output_path, start, duration)

                    if output_path.exists():
                        downloaded_files.append(output_path)
                        self.download_log.append(
                            {
                                "category": category,
                                "name": name,
                                "url": url,
                                "file": str(output_path),
                                "status": "success",
                            }
                        )
                        print(f"  ✓ {filename}")
                    else:
                        self.failed_downloads.append(
                            {
                                "category": category,
                                "name": name,
                                "url": url,
                                "error": "File disappeared after processing",
                            }
                        )
                        print(f"  ✗ {filename} (processing failed)")
                else:
                    self.failed_downloads.append(
                        {
                            "category": category,
                            "name": name,
                            "url": url,
                            "error": "Download failed",
                        }
                    )
                    print(f"  ✗ {filename} (download failed)")

                # Rate limiting to be respectful
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error downloading {name}: {e}")
                self.failed_downloads.append(
                    {"category": category, "name": name, "url": url, "error": str(e)}
                )
                print(f"  ✗ {name} (error: {e})")

        return downloaded_files

    async def download_all(self, priority_filter: str | None = None) -> dict:
        """Download all 360° test videos."""
        if not self.check_dependencies():
            return {"success": False, "error": "Missing dependencies"}

        print("🌐 Downloading 360° Test Videos...")

        all_downloaded = []

        # Filter by priority if specified
        sources_to_download = self.VIDEO_360_SOURCES
        if priority_filter:
            sources_to_download = {
                k: v
                for k, v in self.VIDEO_360_SOURCES.items()
                if v.get("priority", "medium") == priority_filter
            }

        # Download each category
        for category, info in sources_to_download.items():
            downloaded = await self.download_category(category, info)
            all_downloaded.extend(downloaded)

        # Create download summary
        self.save_download_summary()

        print("\n✅ Download complete!")
        print(f"   Successfully downloaded: {len(all_downloaded)} videos")
        print(f"   Failed downloads: {len(self.failed_downloads)}")
        print(f"   Output directory: {self.output_dir}")

        return {
            "success": True,
            "downloaded": len(all_downloaded),
            "failed": len(self.failed_downloads),
            "files": [str(f) for f in all_downloaded],
            "output_dir": str(self.output_dir),
        }

    def save_download_summary(self) -> None:
        """Save download summary to JSON file."""
        summary = {
            "timestamp": time.time(),
            "total_attempted": len(self.download_log) + len(self.failed_downloads),
            "successful": len(self.download_log),
            "failed": len(self.failed_downloads),
            "downloads": self.download_log,
            "failures": self.failed_downloads,
            "directories": {k: str(v) for k, v in self.dirs.items()},
        }

        summary_file = self.output_dir / "download_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Download summary saved: {summary_file}")


async def main():
    """Download 360° test videos."""
    import argparse

    parser = argparse.ArgumentParser(description="Download 360° test videos")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="tests/fixtures/videos/360",
        help="Output directory for downloaded videos",
    )
    parser.add_argument(
        "--priority",
        "-p",
        choices=["high", "medium", "low"],
        help="Only download videos with specified priority",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Create downloader and start downloading
    output_dir = Path(args.output_dir)
    downloader = Video360Downloader(output_dir)

    try:
        result = await downloader.download_all(priority_filter=args.priority)

        if result["success"]:
            print(f"\n🎉 Successfully downloaded {result['downloaded']} videos!")
            if result["failed"] > 0:
                print(
                    f"⚠️  {result['failed']} downloads failed - check download_summary.json"
                )
        else:
            print(f"❌ Download failed: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Download failed with exception")


if __name__ == "__main__":
    # Check if aiohttp and aiofiles are available
    try:
        import aiofiles
        import aiohttp
    except ImportError:
        print("❌ Missing async dependencies. Install with:")
        print("   pip install aiohttp aiofiles")
        exit(1)

    asyncio.run(main())
