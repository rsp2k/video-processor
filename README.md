<div align="center">

# 🎬 Video Processor

**A Modern Python Library for Professional Video Processing**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-green)](https://github.com/astral-sh/uv)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-52%20passed-brightgreen)](https://pytest.org/)
[![Version](https://img.shields.io/badge/version-0.3.0-blue)](https://github.com/your-repo/releases)

*Extracted from the demostar Django application, now a standalone powerhouse for video encoding, thumbnail generation, and sprite creation.*

## 🚀 **LATEST: v0.4.0 - Complete Multimedia Platform!**
🤖 **AI Analysis** • 🎥 **AV1/HEVC/HDR** • 📡 **Adaptive Streaming** • 🌐 **360° Video Processing** • ✅ **Production Ready**

[📚 **Full Documentation**](docs/) •
[🚀 Features](#-features) •
[⚡ Quick Start](#-quick-start) •
[💻 Examples](#-examples) •
[🔄 Migration](#-migration-to-v040)

</div>

---

## 📚 Documentation

### **Complete Documentation Suite Available in [`docs/`](docs/)**

| Documentation | Description |
|---------------|-------------|
| **[📖 User Guide](docs/user-guide/)** | Complete getting started guides and feature overviews |
| **[🔄 Migration](docs/migration/)** | Upgrade instructions and migration guides |
| **[🛠️ Development](docs/development/)** | Technical implementation details and architecture |
| **[📋 Reference](docs/reference/)** | API references, roadmaps, and feature lists |
| **[💻 Examples](docs/examples/)** | 11 comprehensive examples covering all features |

### **Quick Links**
- **[🚀 NEW_FEATURES_v0.4.0.md](docs/user-guide/NEW_FEATURES_v0.4.0.md)** - Complete v0.4.0 feature overview
- **[📘 README_v0.4.0.md](docs/user-guide/README_v0.4.0.md)** - Comprehensive getting started guide
- **[🔄 MIGRATION_GUIDE_v0.4.0.md](docs/migration/MIGRATION_GUIDE_v0.4.0.md)** - Upgrade instructions
- **[💻 Examples Documentation](docs/examples/README.md)** - Hands-on usage examples

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎥 **Video Encoding**
- **Multi-format support**: MP4 (H.264), WebM (VP9), OGV (Theora)
- **Two-pass encoding** for optimal quality
- **Professional presets**: Low, Medium, High, Ultra
- **Customizable bitrates** and quality settings

</td>
<td width="50%">

### 🖼️ **Thumbnails & Sprites**
- **Smart thumbnail extraction** at any timestamp
- **Seekbar sprite sheets** with WebVTT files
- **Configurable intervals** and dimensions
- **Mobile-optimized** output options

</td>
</tr>
<tr>
<td width="50%">

### ⚡ **Background Processing**
- **Procrastinate integration** for async tasks
- **PostgreSQL job queue** management
- **Scalable worker architecture**
- **Progress tracking** and error handling

</td>
<td width="50%">

### 🛠️ **Modern Development**
- **Type-safe** with full type hints
- **Pydantic V2** configuration validation
- **uv** for lightning-fast dependency management
- **ruff** for code quality and formatting

</td>
</tr>
<tr>
<td colspan="2">

### 🌐 **360° Video Support** *(Optional)*
- **Spherical video detection** and metadata extraction
- **Projection conversions** (equirectangular, cubemap, stereographic)
- **360° thumbnail generation** with multiple viewing angles
- **Spatial audio processing** for immersive experiences

</td>
</tr>
</table>

---

## 📦 Installation

### Quick Install

```bash
# Basic installation (standard video processing)
uv add video-processor

# With 360° video support
uv add "video-processor[video-360]"

# With spatial audio processing  
uv add "video-processor[spatial-audio]"

# Complete 360° feature set
uv add "video-processor[video-360-full]"

# Or using pip
pip install video-processor
pip install "video-processor[video-360-full]"
```

### Optional Features

#### 🌐 360° Video Processing
For immersive video processing capabilities:
- **`video-360`**: Core 360° video processing (py360convert, opencv, numpy, scipy)
- **`spatial-audio`**: Spatial audio processing (librosa, soundfile)  
- **`metadata-360`**: Enhanced 360° metadata extraction (exifread)
- **`video-360-full`**: Complete 360° package (includes all above)

#### 📦 Dependency Details
```bash
# Core 360° processing
uv add "video-processor[video-360]"
# Includes: py360convert, opencv-python, numpy, scipy

# Spatial audio support  
uv add "video-processor[spatial-audio]"
# Includes: librosa, soundfile

# Complete 360° experience
uv add "video-processor[video-360-full]"
# Includes: All 360° dependencies + exifread
```

### ⚡ Procrastinate Migration (2.x → 3.x)

This library supports both **Procrastinate 2.x** and **3.x** for smooth migration:

#### 🔄 Automatic Version Detection
```python
from video_processor.tasks.compat import get_version_info, IS_PROCRASTINATE_3_PLUS

version_info = get_version_info()
print(f"Using Procrastinate {version_info['procrastinate_version']}")
print(f"Features available: {list(version_info['features'].keys())}")

# Version-aware setup
if IS_PROCRASTINATE_3_PLUS:
    # Use 3.x features like improved performance, graceful shutdown
    pass
```

#### 📋 Migration Steps
1. **Install compatible version**:
   ```bash
   uv add "procrastinate>=3.5.2,<4.0.0"  # Or keep 2.x support: ">=2.15.1,<4.0.0"
   ```

2. **Apply database migrations**:
   ```bash
   # Procrastinate 3.x (two-step process)
   procrastinate schema --apply --mode=pre    # Before deploying
   # Deploy new code
   procrastinate schema --apply --mode=post   # After deploying
   
   # Procrastinate 2.x (single step)
   procrastinate schema --apply
   ```

3. **Use migration helper**:
   ```python
   from video_processor.tasks.migration import migrate_database
   
   # Automatic version-aware migration
   success = await migrate_database("postgresql://localhost/mydb")
   ```

4. **Update worker configuration**:
   ```python
   from video_processor.tasks import get_worker_kwargs
   
   # Automatically normalizes options for your version
   worker_options = get_worker_kwargs(
       concurrency=4,
       timeout=5,  # Maps to fetch_job_polling_interval in 3.x
       remove_error=True,  # Maps to remove_failed in 3.x
   )
   ```

#### 🆕 Procrastinate 3.x Benefits
- **Better performance** with improved job fetching
- **Graceful shutdown** with `shutdown_graceful_timeout`
- **Enhanced error handling** and job cancellation
- **Schema compatibility** improvements (3.5.2+)

### Development Setup

```bash
git clone <repository>
cd video_processor

# Install with all development dependencies
uv sync --dev

# Install with dev + 360° features
uv sync --dev --extra video-360-full

# Verify installation
uv run pytest
```

---

## 🚀 Quick Start

### Basic Video Processing

```python
from pathlib import Path
from video_processor import VideoProcessor, ProcessorConfig

# 📋 Configure your processor
config = ProcessorConfig(
    base_path=Path("/tmp/video_output"),
    output_formats=["mp4", "webm"],
    quality_preset="high"  # 🎯 Professional quality
)

# 🎬 Initialize and process
processor = VideoProcessor(config)
result = processor.process_video(
    input_path="input_video.mp4",
    output_dir="outputs"
)

# 📊 Results
print(f"🎥 Video ID: {result.video_id}")
print(f"📁 Formats: {list(result.encoded_files.keys())}")
print(f"🖼️ Thumbnail: {result.thumbnail_file}")
print(f"🎞️ Sprites: {result.sprite_files}")
```

### Async Background Processing

```python
import asyncio
from video_processor.tasks import setup_procrastinate

async def process_in_background():
    # 🗄️ Connect to PostgreSQL
    app = setup_procrastinate("postgresql://user:pass@localhost/db")
    
    # 📤 Submit job
    job = await app.tasks.process_video_async.defer_async(
        input_path="/path/to/video.mp4",
        output_dir="/path/to/output",
        config_dict={"quality_preset": "ultra"}
    )
    
    print(f"✅ Job queued: {job.id}")

asyncio.run(process_in_background())
```

---

## ⚙️ Configuration

### Quality Presets Comparison

<div align="center">

| 🎯 Preset | 📺 Video Bitrate | 🔊 Audio Bitrate | 🎨 CRF | 💡 Best For |
|-----------|------------------|------------------|---------|-------------|
| **Low** | 1,000k | 128k | 28 | 📱 Mobile, limited bandwidth |
| **Medium** | 2,500k | 192k | 23 | 🌐 Standard web delivery |
| **High** | 5,000k | 256k | 18 | 🎬 High-quality streaming |
| **Ultra** | 10,000k | 320k | 15 | 🏛️ Archive, professional use |

</div>

### Advanced Configuration

```python
from video_processor import ProcessorConfig
from pathlib import Path

config = ProcessorConfig(
    # 📂 Storage & Paths
    base_path=Path("/media/videos"),
    storage_backend="local",  # 🔮 S3 coming soon!
    
    # 🎥 Video Settings
    output_formats=["mp4", "webm", "ogv"],
    quality_preset="ultra",
    
    # 🖼️ Thumbnails & Sprites
    thumbnail_timestamp=30,    # 📍 30 seconds in
    sprite_interval=5.0,       # 🎞️ Every 5 seconds
    
    # 🛠️ System
    ffmpeg_path="/usr/local/bin/ffmpeg"  # 🔧 Custom FFmpeg
)
```

---

## 🧪 Testing

### 🎯 **NEW in v0.3.0**: Comprehensive Test Infrastructure

Video Processor now includes a world-class testing framework with **108+ video fixtures** and **perfect test compatibility**!

#### ⚡ Quick Testing
```bash
# Run all tests
make test

# Unit tests only (fast)
uv run pytest tests/unit/

# Integration tests with Docker
make test-docker

# Test specific categories
uv run pytest -m "smoke"        # Quick smoke tests
uv run pytest -m "edge_cases"   # Edge case scenarios  
uv run pytest -m "codecs"       # Codec compatibility
```

#### 🎬 Test Video Fixtures

Our comprehensive test suite includes:
- **Edge Cases**: Single frame videos, unusual resolutions (16x16, 1920x2), extreme aspect ratios
- **Multiple Codecs**: H.264, H.265, VP8, VP9, Theora, MPEG4 with various profiles  
- **Audio Variations**: Mono/stereo, different sample rates, no audio, audio-only files
- **Visual Patterns**: SMPTE bars, RGB test patterns, YUV test, checkerboard patterns
- **Motion Tests**: Rotation, camera shake, scene changes, complex motion
- **Stress Tests**: High complexity scenes, noise patterns, encoding challenges

#### 📊 Test Results
```bash
✅ 52 passing tests (0 failures!)
✅ 108+ test video fixtures  
✅ Complete Docker integration
✅ Perfect API compatibility
```

#### 🐳 Docker Integration Testing
```bash
# Complete integration testing environment
make test-docker

# Test specific services  
make test-db-migration    # Database migration testing
make test-worker         # Procrastinate worker testing
make clean-docker        # Clean up test environment
```

#### 🔧 Advanced Testing
```bash
# Generate/update test video fixtures
uv run python tests/fixtures/test_suite_manager.py --setup

# Validate test suite integrity
uv run python tests/fixtures/test_suite_manager.py --validate

# Generate synthetic videos for edge cases
uv run python tests/fixtures/generate_synthetic_videos.py

# Download open source test videos
uv run python tests/fixtures/download_test_videos.py
```

#### 🎨 Test Categories

| Category | Description | Video Count |
|----------|-------------|-------------|
| **smoke** | Quick validation tests | 2 videos |
| **basic** | Standard functionality | 5 videos |  
| **codecs** | Format compatibility | 9 videos |
| **edge_cases** | Boundary conditions | 12+ videos |
| **stress** | Performance testing | 2+ videos |
| **full** | Complete test suite | 108+ videos |

---

## 💡 Examples

Explore our comprehensive examples in the [`examples/`](examples/) directory:

### 📝 Available Examples

| Example | Description | Features |
|---------|-------------|-----------|
| [`basic_usage.py`](examples/basic_usage.py) | 🎯 Simple synchronous processing | Configuration, encoding, thumbnails |
| [`async_processing.py`](examples/async_processing.py) | ⚡ Background task processing | Procrastinate, job queuing, monitoring |
| [`custom_config.py`](examples/custom_config.py) | 🛠️ Advanced configuration scenarios | Quality presets, validation, custom paths |
| [`docker_demo.py`](examples/docker_demo.py) | 🐳 Complete containerized demo | Docker, PostgreSQL, async workers |
| [`web_demo.py`](examples/web_demo.py) | 🌐 Flask web interface | Browser-based processing, job submission |

### 🐳 Docker Quick Start

Get up and running in seconds with our complete Docker environment:

```bash
# Start all services (PostgreSQL, Redis, app, workers)
docker-compose up -d

# View logs from the demo application
docker-compose logs -f app

# Access web demo at http://localhost:8080
docker-compose up demo

# Run tests in Docker
docker-compose run test

# Clean up
docker-compose down -v
```

**Services included:**
- 🗄️ **PostgreSQL** - Database with Procrastinate job queue
- 🎬 **App** - Main video processor demo
- ⚡ **Worker** - Background job processor
- 🧪 **Test** - Automated testing environment
- 🌐 **Demo** - Web interface for browser-based testing

### 🎬 Real-World Usage Patterns

<details>
<summary><b>🏢 Production Video Pipeline</b></summary>

```python
# Multi-format encoding for video platform
config = ProcessorConfig(
    base_path=Path("/var/media/uploads"),
    output_formats=["mp4", "webm"],  # Cross-browser support
    quality_preset="high",
    sprite_interval=10.0  # Balanced performance
)

processor = VideoProcessor(config)
result = processor.process_video(user_upload, output_dir)

# Generate multiple qualities
for quality in ["medium", "high"]:
    config.quality_preset = quality
    processor = VideoProcessor(config)
    # Process to different quality folders...
```

</details>

<details>
<summary><b>📱 Mobile-Optimized Processing</b></summary>

```python
# Lightweight encoding for mobile delivery
mobile_config = ProcessorConfig(
    base_path=Path("/tmp/mobile_videos"),
    output_formats=["mp4"],  # Mobile-friendly format
    quality_preset="low",    # Reduced bandwidth
    sprite_interval=15.0     # Fewer sprites
)
```

</details>

---

## 📚 API Reference

### 🎬 VideoProcessor

The main orchestrator for all video processing operations.

#### 🔧 Methods

```python
# Process video to all configured formats
result = processor.process_video(
    input_path: Path | str,
    output_dir: Path | str | None = None,
    video_id: str | None = None
) -> VideoProcessingResult

# Encode to specific format
output_path = processor.encode_video(
    input_path: Path,
    output_dir: Path,
    format_name: str,
    video_id: str
) -> Path

# Generate thumbnail at timestamp
thumbnail = processor.generate_thumbnail(
    video_path: Path,
    output_dir: Path,
    timestamp: int,
    video_id: str
) -> Path

# Create sprite sheet and WebVTT
sprites = processor.generate_sprites(
    video_path: Path,
    output_dir: Path,
    video_id: str
) -> tuple[Path, Path]
```

### ⚙️ ProcessorConfig

Type-safe configuration with automatic validation.

#### 📋 Essential Fields

```python
class ProcessorConfig:
    base_path: Path                    # 📂 Base directory
    output_formats: list[str]          # 🎥 Video formats
    quality_preset: str                # 🎯 Quality level
    storage_backend: str               # 💾 Storage type
    ffmpeg_path: str                   # 🛠️ FFmpeg binary
    thumbnail_timestamp: int           # 🖼️ Thumbnail position
    sprite_interval: float             # 🎞️ Sprite frequency
```

### 📊 VideoProcessingResult

Comprehensive result object with all output information.

```python
@dataclass
class VideoProcessingResult:
    video_id: str                      # 🆔 Unique identifier
    encoded_files: dict[str, Path]     # 📁 Format → file mapping
    thumbnail_file: Path | None        # 🖼️ Thumbnail image
    sprite_files: tuple[Path, Path] | None  # 🎞️ Sprite + WebVTT
    metadata: VideoMetadata            # 📊 Video properties
```

---

## 🧪 Development

### 🛠️ Development Commands

```bash
# 📦 Install dependencies
uv sync

# 🧪 Run test suite
uv run pytest -v

# 📊 Test coverage
uv run pytest --cov=video_processor

# ✨ Code formatting
uv run ruff format .

# 🔍 Linting
uv run ruff check .

# 🎯 Type checking
uv run mypy src/
```

### 📈 Test Coverage

Our comprehensive test suite covers:

- ✅ **Configuration** validation and type checking
- ✅ **Path utilities** and file operations  
- ✅ **FFmpeg integration** and error handling
- ✅ **Video metadata** extraction
- ✅ **Background task** processing
- ✅ **Procrastinate compatibility** (2.x/3.x versions)
- ✅ **Database migrations** with version detection
- ✅ **Worker configuration** and option mapping
- ✅ **360° video processing** (when dependencies available)

```bash
========================== test session starts ==========================
tests/test_config.py ✅✅✅✅✅           [15%] 
tests/test_utils.py ✅✅✅✅✅✅✅✅       [30%]
tests/test_procrastinate_compat.py ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅  [85%]
tests/test_procrastinate_migration.py ✅✅✅✅✅✅✅✅✅✅✅✅✅   [100%]

======================== 43 passed in 0.52s ========================
```

---

## 📦 Dependencies

### 🎯 Core Dependencies

| Package | Purpose | Why We Use It |
|---------|---------|---------------|
| `ffmpeg-python` | FFmpeg integration | 🎬 Professional video processing |
| `msprites2` | Sprite generation | 🎞️ Seekbar thumbnails (forked for fixes) |
| `procrastinate` | Background tasks | ⚡ Scalable async processing |
| `pydantic` | Configuration | ⚙️ Type-safe settings validation |
| `pillow` | Image processing | 🖼️ Thumbnail manipulation |

### 🔧 Development Tools

| Tool | Purpose | Benefits |
|------|---------|----------|
| `uv` | Package management | 🚀 Ultra-fast dependency resolution |
| `ruff` | Linting & formatting | ⚡ Lightning-fast code quality |
| `pytest` | Testing framework | 🧪 Reliable test execution |
| `mypy` | Type checking | 🎯 Static type analysis |
| `coverage` | Test coverage | 📊 Quality assurance |

---

## 🌟 Why Video Processor?

<div align="center">

### 🆚 Comparison with Alternatives

| Feature | Video Processor | FFmpeg CLI | moviepy | OpenCV |
|---------|----------------|------------|---------|--------|
| **Two-pass encoding** | ✅ | ✅ | ❌ | ❌ |
| **Multiple formats** | ✅ | ✅ | ✅ | ❌ |
| **Background processing** | ✅ | ❌ | ❌ | ❌ |
| **Type safety** | ✅ | ❌ | ❌ | ❌ |
| **Sprite generation** | ✅ | ❌ | ❌ | ❌ |
| **Modern Python** | ✅ | N/A | ❌ | ❌ |

</div>

---

## 📋 Requirements

### 🖥️ System Requirements

- **Python 3.11+** - Modern Python features
- **FFmpeg** - Video processing engine
- **PostgreSQL** - Background job processing (optional)

### 🐧 Installation Commands

```bash
# Ubuntu/Debian
sudo apt install ffmpeg postgresql-client

# macOS
brew install ffmpeg postgresql

# Arch Linux
sudo pacman -S ffmpeg postgresql
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🚀 Quick Contribution Guide

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **📝 Make** your changes with tests
4. **🧪 Test** everything (`uv run pytest`)
5. **✨ Format** code (`uv run ruff format .`)
6. **📤 Submit** a pull request

### 🎯 Areas We'd Love Help With

- 🌐 **S3 storage backend** implementation
- 🎞️ **Additional video formats** (AV1, HEVC)
- 📊 **Progress tracking** and monitoring
- 🐳 **Docker integration** examples
- 📖 **Documentation** improvements

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🎉 Changelog

### 🚀 v0.2.0 - Procrastinate 3.x Migration & Docker Support

- 🔄 **Procrastinate 3.x compatibility** with backward support for 2.x
- 🎯 **Automatic version detection** and feature flagging 
- 📋 **Database migration utilities** with pre/post migration support
- 🐳 **Complete Docker environment** with multi-service orchestration
- 🌐 **Web demo interface** with Flask-based UI
- ⚡ **Worker compatibility layer** with unified CLI
- 🧪 **30+ comprehensive tests** covering all compatibility scenarios
- 📊 **uv caching optimization** following Docker best practices

### 🌟 v0.1.0 - Initial Release

- ✨ **Multi-format encoding**: MP4, WebM, OGV support
- 🖼️ **Thumbnail generation** with customizable timestamps
- 🎞️ **Sprite sheet creation** with WebVTT files
- ⚡ **Background processing** with Procrastinate integration
- ⚙️ **Type-safe configuration** with Pydantic V2
- 🛠️ **Modern tooling**: uv, ruff, pytest integration
- 📚 **Comprehensive documentation** and examples

---

## 🔄 Migration to v0.4.0

### **Upgrading from Previous Versions**

Video Processor v0.4.0 maintains **100% backward compatibility** while adding powerful new features:

```python
# Your existing code continues to work unchanged
processor = VideoProcessor(config)
result = await processor.process_video("video.mp4", "./output/")

# But now you get additional features automatically:
if result.is_360_video:
    print(f"360° projection: {result.video_360.projection_type}")

if result.quality_analysis:
    print(f"Quality score: {result.quality_analysis.overall_quality:.1f}/10")
```

### **New Features Available**
- **🤖 AI Analysis**: Automatic scene detection and quality assessment
- **🎥 Modern Codecs**: AV1, HEVC, and HDR support
- **📡 Streaming**: HLS and DASH adaptive streaming
- **🌐 360° Processing**: Complete immersive video pipeline

### **Migration Resources**
- **[📋 Complete Migration Guide](docs/migration/MIGRATION_GUIDE_v0.4.0.md)** - Step-by-step upgrade instructions
- **[🚀 New Features Overview](docs/user-guide/NEW_FEATURES_v0.4.0.md)** - What's new in v0.4.0
- **[💻 Updated Examples](docs/examples/README.md)** - New capabilities in action

---

<div align="center">

### 🙋‍♀️ Questions? Issues? Ideas?

**Found a bug?** [Open an issue](https://github.com/your-repo/issues/new/choose)  
**Have a feature request?** [Start a discussion](https://github.com/your-repo/discussions)  
**Want to contribute?** Check out our [contribution guide](#-contributing)

---

**Built with ❤️ for the video processing community**

*Making professional video encoding accessible to everyone*

</div>