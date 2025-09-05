"""
Download open source and Creative Commons videos for testing.
Sources include Blender Foundation, Wikimedia Commons, and more.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from urllib.parse import urlparse
import subprocess
import concurrent.futures
from tqdm import tqdm


class TestVideoDownloader:
    """Download and prepare open source test videos."""
    
    # Curated list of open source test videos
    TEST_VIDEOS = {
        # Blender Foundation (Creative Commons)
        "big_buck_bunny": {
            "urls": {
                "1080p_30fps": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "720p": "http://techslides.com/demos/sample-videos/small.mp4",
            },
            "license": "CC-BY",
            "description": "Big Buck Bunny - Blender Foundation",
            "trim": (10, 20),  # Use 10-20 second segment
        },
        
        # Test patterns and samples
        "test_patterns": {
            "urls": {
                "sample_video": "http://techslides.com/demos/sample-videos/small.mp4",
            },
            "license": "Public Domain",
            "description": "Professional test patterns", 
            "trim": (0, 5),
        },
    }
    
    def __init__(self, output_dir: Path, max_size_mb: int = 50):
        """
        Initialize downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
            max_size_mb: Maximum size per video in MB
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create category directories
        self.dirs = {
            "standard": self.output_dir / "standard",
            "codecs": self.output_dir / "codecs", 
            "resolutions": self.output_dir / "resolutions",
            "patterns": self.output_dir / "patterns",
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, output_path: Path, 
                     expected_hash: Optional[str] = None) -> bool:
        """
        Download a file with progress bar.
        
        Args:
            url: URL to download
            output_path: Path to save file
            expected_hash: Optional SHA256 hash for verification
        
        Returns:
            Success status
        """
        if output_path.exists():
            if expected_hash:
                with open(output_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    if file_hash == expected_hash:
                        print(f"✓ Already exists: {output_path.name}")
                        return True
            else:
                print(f"✓ Already exists: {output_path.name}")
                return True
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Check size limit
            if total_size > self.max_size_bytes:
                print(f"⚠ Skipping {url}: Too large ({total_size / 1024 / 1024:.1f}MB)")
                return False
            
            # Download with progress bar
            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, 
                         desc=output_path.name) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            # Verify hash if provided
            if expected_hash:
                with open(output_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    if file_hash != expected_hash:
                        output_path.unlink()
                        print(f"✗ Hash mismatch for {output_path.name}")
                        return False
            
            print(f"✓ Downloaded: {output_path.name}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to download {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            return False
    
    def trim_video(self, input_path: Path, output_path: Path,
                  start: float, duration: float) -> bool:
        """
        Trim video to specified duration using FFmpeg.
        
        Args:
            input_path: Input video path
            output_path: Output video path
            start: Start time in seconds
            duration: Duration in seconds
        
        Returns:
            Success status
        """
        try:
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start),
                '-i', str(input_path),
                '-t', str(duration),
                '-c', 'copy',  # Copy codecs (fast)
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Remove original and rename trimmed
                input_path.unlink()
                output_path.rename(input_path)
                return True
            else:
                print(f"✗ Failed to trim {input_path.name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error trimming {input_path.name}: {e}")
            return False
    
    def download_all(self):
        """Download all test videos."""
        print("🎬 Downloading Open Source Test Videos...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📊 Max size per file: {self.max_size_bytes / 1024 / 1024:.0f}MB\n")
        
        # Download main test videos
        for category, info in self.TEST_VIDEOS.items():
            print(f"\n📦 Downloading {category}...")
            print(f"   License: {info['license']}")
            print(f"   {info['description']}\n")
            
            for name, url in info["urls"].items():
                # Determine output directory based on content type
                if "1080p" in name or "720p" in name or "4k" in name:
                    out_dir = self.dirs["resolutions"]
                elif "pattern" in category:
                    out_dir = self.dirs["patterns"]
                else:
                    out_dir = self.dirs["standard"]
                
                # Generate filename
                ext = Path(urlparse(url).path).suffix or '.mp4'
                filename = f"{category}_{name}{ext}"
                output_path = out_dir / filename
                
                # Download file
                if self.download_file(url, output_path):
                    # Trim if specified
                    if info.get("trim"):
                        start, end = info["trim"]
                        duration = end - start
                        temp_path = output_path.with_suffix('.tmp' + output_path.suffix)
                        if self.trim_video(output_path, temp_path, start, duration):
                            print(f"   ✂ Trimmed to {duration}s")
        
        print("\n✅ Download complete!")
        self.generate_manifest()
    
    def generate_manifest(self):
        """Generate a manifest of downloaded videos with metadata."""
        manifest = {
            "videos": [],
            "total_size_mb": 0,
            "categories": {}
        }
        
        for category, dir_path in self.dirs.items():
            if not dir_path.exists():
                continue
            
            manifest["categories"][category] = []
            
            for video_file in dir_path.glob("*"):
                if video_file.is_file() and video_file.suffix in ['.mp4', '.webm', '.mkv', '.mov', '.ogv']:
                    # Get video metadata using ffprobe
                    metadata = self.get_video_metadata(video_file)
                    
                    video_info = {
                        "path": str(video_file.relative_to(self.output_dir)),
                        "category": category,
                        "size_mb": video_file.stat().st_size / 1024 / 1024,
                        "metadata": metadata
                    }
                    
                    manifest["videos"].append(video_info)
                    manifest["categories"][category].append(video_info["path"])
                    manifest["total_size_mb"] += video_info["size_mb"]
        
        # Save manifest
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n📋 Manifest saved to: {manifest_path}")
        print(f"   Total videos: {len(manifest['videos'])}")
        print(f"   Total size: {manifest['total_size_mb']:.1f}MB")
    
    def get_video_metadata(self, video_path: Path) -> dict:
        """Extract video metadata using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                video_stream = next(
                    (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                    {}
                )
                
                audio_stream = next(
                    (s for s in data.get('streams', []) if s['codec_type'] == 'audio'),
                    {}
                )
                
                return {
                    "duration": float(data.get('format', {}).get('duration', 0)),
                    "video_codec": video_stream.get('codec_name'),
                    "width": video_stream.get('width'),
                    "height": video_stream.get('height'),
                    "fps": eval(video_stream.get('r_frame_rate', '0/1')),
                    "audio_codec": audio_stream.get('codec_name'),
                    "audio_channels": audio_stream.get('channels'),
                    "format": data.get('format', {}).get('format_name')
                }
            
        except Exception:
            pass
        
        return {}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download open source test videos")
    parser.add_argument("--output", "-o", default="tests/fixtures/videos/opensource",
                       help="Output directory")
    parser.add_argument("--max-size", "-m", type=int, default=50,
                       help="Max size per video in MB")
    
    args = parser.parse_args()
    
    downloader = TestVideoDownloader(
        output_dir=Path(args.output),
        max_size_mb=args.max_size
    )
    
    downloader.download_all()