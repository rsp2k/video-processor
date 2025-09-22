# Advanced Video Features Documentation

This document comprehensively details the advanced video processing capabilities already implemented in the video-processor library.

## 🎬 360° Video Processing Capabilities

### Core 360° Detection System (`src/video_processor/utils/video_360.py`)

**Sophisticated Multi-Method Detection**
- **Spherical Metadata Detection**: Reads Google/YouTube spherical video standard metadata tags
- **Aspect Ratio Analysis**: Detects equirectangular videos by 2:1 aspect ratio patterns
- **Filename Pattern Recognition**: Identifies 360° indicators in filenames ("360", "vr", "spherical", etc.)
- **Confidence Scoring**: Provides confidence levels (0.6-1.0) for detection reliability

**Supported Projection Types**
- `equirectangular` (most common, optimal for VR headsets)
- `cubemap` (6-face projection, efficient encoding)
- `cylindrical` (partial 360°, horizontal only)
- `stereographic` ("little planet" effect)

**Stereo Mode Support**
- `mono` (single eye view)
- `top-bottom` (3D stereoscopic, vertical split)
- `left-right` (3D stereoscopic, horizontal split)

### Advanced 360° Thumbnail Generation (`src/video_processor/core/thumbnails_360.py`)

**Multi-Angle Perspective Generation**
- **6 Directional Views**: front, back, left, right, up, down
- **Stereographic Projection**: "Little planet" effect for preview thumbnails
- **Custom Viewing Angles**: Configurable yaw/pitch for specific viewpoints
- **High-Quality Extraction**: Full-resolution frame extraction with quality preservation

**Technical Implementation**
- **Mathematical Projections**: Implements perspective and stereographic coordinate transformations
- **OpenCV Integration**: Uses cv2.remap for efficient image warping
- **Ray Casting**: 3D ray direction calculations for accurate perspective views
- **Spherical Coordinate Conversion**: Converts between Cartesian and spherical coordinate systems

**360° Sprite Sheet Generation**
- **Angle-Specific Sprites**: Creates seekbar sprites for specific viewing angles
- **WebVTT Integration**: Generates thumbnail preview files for video players
- **Batch Processing**: Efficiently processes multiple timestamps for sprite creation

### Intelligent Bitrate Optimization

**Projection-Aware Bitrate Multipliers**
```python
multipliers = {
    "equirectangular": 2.5,  # Most common, needs high bitrate due to pole distortion
    "cubemap": 2.0,          # More efficient encoding, less distortion
    "cylindrical": 1.8,      # Less immersive, lower multiplier acceptable
    "stereographic": 2.2,    # Good balance for artistic effect
    "unknown": 2.0,          # Safe default
}
```

**Optimal Resolution Recommendations**
- **Equirectangular**: 2K (1920×960) up to 8K (7680×3840)
- **Cubemap**: 1.5K to 4K per face
- **Automatic Resolution Selection**: Based on projection type and quality preset

## 🎯 Advanced Encoding System (`src/video_processor/core/encoders.py`)

### Multi-Pass Encoding Architecture

**MP4 Two-Pass Encoding**
- **Analysis Pass**: FFmpeg analyzes video content for optimal bitrate distribution
- **Encoding Pass**: Applies analysis results for superior quality/size ratio
- **Quality Presets**: 4 tiers (low/medium/high/ultra) with scientifically tuned parameters

**WebM VP9 Encoding**
- **CRF-Based Quality**: Constant Rate Factor for consistent visual quality
- **Opus Audio**: High-efficiency audio codec for web delivery
- **Smart Source Selection**: Uses MP4 as intermediate if available for better quality chain

**OGV Theora Encoding**
- **Single-Pass Efficiency**: Optimized for legacy browser support
- **Quality Scale**: Uses qscale for balanced quality/size ratio

### Advanced Quality Presets

| Quality | Video Bitrate | Min/Max Bitrate | Audio Bitrate | CRF | Use Case |
|---------|---------------|-----------------|---------------|-----|----------|
| **Low** | 1000k | 500k/1500k | 128k | 28 | Mobile, bandwidth-constrained |
| **Medium** | 2500k | 1000k/4000k | 192k | 23 | Standard web delivery |
| **High** | 5000k | 2000k/8000k | 256k | 18 | High-quality streaming |
| **Ultra** | 10000k | 5000k/15000k | 320k | 15 | Professional, archival |

## 🖼️ Sophisticated Thumbnail System

### Standard Thumbnail Generation (`src/video_processor/core/thumbnails.py`)

**Intelligent Timestamp Selection**
- **Duration-Aware**: Automatically adjusts timestamps beyond video duration
- **Quality Optimization**: Uses high-quality JPEG encoding (q=2)
- **Batch Processing**: Efficient generation of multiple thumbnails

**Sprite Sheet Generation**
- **msprites2 Integration**: Advanced sprite generation library
- **WebVTT Support**: Creates seekbar preview functionality
- **Customizable Layouts**: Configurable grid arrangements
- **Optimized File Sizes**: Balanced quality/size for web delivery

## 🔧 Production-Grade Configuration (`src/video_processor/config.py`)

### Comprehensive Settings Management

**Storage Backend Abstraction**
- **Local Filesystem**: Production-ready local storage with permission management
- **S3 Integration**: Prepared for cloud storage (backend planned)
- **Path Validation**: Automatic absolute path resolution and validation

**360° Configuration Integration**
```python
# 360° specific settings
enable_360_processing: bool = Field(default=HAS_360_SUPPORT)
auto_detect_360: bool = Field(default=True)
force_360_projection: ProjectionType | None = Field(default=None)
video_360_bitrate_multiplier: float = Field(default=2.5, ge=1.0, le=5.0)
generate_360_thumbnails: bool = Field(default=True)
thumbnail_360_projections: list[ViewingAngle] = Field(default=["front", "stereographic"])
```

**Validation & Safety**
- **Dependency Checking**: Automatically validates 360° library availability
- **Configuration Validation**: Pydantic-based type checking and value validation
- **Graceful Fallbacks**: Handles missing optional dependencies elegantly

## 🎮 Advanced Codec Support

### Existing Codec Capabilities

**Video Codecs**
- **H.264 (AVC)**: Industry standard, broad compatibility
- **VP9**: Next-gen web codec, excellent compression
- **Theora**: Open source, legacy browser support

**Audio Codecs**
- **AAC**: High-quality, broad compatibility
- **Opus**: Superior efficiency for web delivery
- **Vorbis**: Open source alternative

**Container Formats**
- **MP4**: Universal compatibility, mobile-optimized
- **WebM**: Web-native, progressive loading
- **OGV**: Open source, legacy support

## 🚀 Performance Optimizations

### Intelligent Processing Chains

**Quality Cascading**
```python
# WebM uses MP4 as intermediate source if available for better quality
mp4_file = output_dir / f"{video_id}.mp4"
source_file = mp4_file if mp4_file.exists() else input_path
```

**Resource Management**
- **Automatic Cleanup**: Temporary file management with try/finally blocks
- **Memory Efficiency**: Streaming processing without loading entire videos
- **Error Recovery**: Graceful handling of FFmpeg failures with detailed error reporting

### FFmpeg Integration Excellence

**Advanced FFmpeg Command Construction**
- **Dynamic Parameter Assembly**: Builds commands based on configuration and content analysis
- **Process Management**: Proper subprocess handling with stderr capture
- **Log File Management**: Automatic cleanup of FFmpeg pass logs
- **Cross-Platform Compatibility**: Works on Linux, macOS, Windows

## 🧩 Optional Dependencies System

### Modular Architecture

**360° Feature Dependencies**
```python
# Smart dependency detection
try:
    import cv2
    import numpy as np
    import py360convert
    import exifread
    HAS_360_SUPPORT = True
except ImportError:
    HAS_360_SUPPORT = False
```

**Graceful Degradation**
- **Feature Detection**: Automatically enables/disables features based on available libraries
- **Clear Error Messages**: Helpful installation instructions when dependencies missing
- **Type Safety**: Maintains type hints even when optional dependencies unavailable

## 🔍 Dependency Status

### Required Core Dependencies
- ✅ **FFmpeg**: Video processing engine (system dependency)
- ✅ **Pydantic V2**: Configuration validation and settings
- ✅ **ffmpeg-python**: Python FFmpeg bindings

### Optional 360° Dependencies
- 🔄 **OpenCV** (`cv2`): Image processing and computer vision
- 🔄 **NumPy**: Numerical computing for coordinate transformations
- 🔄 **py360convert**: 360° video projection conversions
- 🔄 **exifread**: Metadata extraction from video files

### Installation Commands
```bash
# Core functionality
uv add video-processor

# With 360° support
uv add "video-processor[video-360]"

# Development dependencies
uv add --dev video-processor
```

## 📊 Current Advanced Feature Matrix

| Feature Category | Implementation Status | Quality Level | Production Ready |
|------------------|----------------------|---------------|-----------------|
| **360° Detection** | ✅ Complete | Professional | ✅ Yes |
| **Multi-Projection Support** | ✅ Complete | Professional | ✅ Yes |
| **Advanced Thumbnails** | ✅ Complete | Professional | ✅ Yes |
| **Multi-Pass Encoding** | ✅ Complete | Professional | ✅ Yes |
| **Quality Presets** | ✅ Complete | Professional | ✅ Yes |
| **Sprite Generation** | ✅ Complete | Professional | ✅ Yes |
| **Configuration System** | ✅ Complete | Professional | ✅ Yes |
| **Error Handling** | ✅ Complete | Professional | ✅ Yes |

## 🎯 Advanced Features Summary

The video-processor library already includes **production-grade advanced video processing capabilities** that rival commercial solutions:

1. **Comprehensive 360° Video Pipeline**: Full detection, processing, and thumbnail generation
2. **Professional Encoding Quality**: Multi-pass encoding with scientific quality presets
3. **Advanced Mathematical Projections**: Sophisticated coordinate transformations for 360° content
4. **Intelligent Content Analysis**: Metadata-driven processing decisions
5. **Modular Architecture**: Graceful handling of optional advanced features
6. **Production Reliability**: Comprehensive error handling and resource management

This foundation provides an excellent base for future enhancements while already delivering enterprise-grade video processing capabilities.