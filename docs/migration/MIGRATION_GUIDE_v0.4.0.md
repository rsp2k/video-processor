# 📈 Migration Guide to v0.4.0

This guide helps you upgrade from previous versions to v0.4.0, which introduces **four major phases** of new functionality while maintaining backward compatibility.

## 🔄 Overview of Changes

v0.4.0 represents a **major evolution** from a simple video processor to a comprehensive multimedia processing platform:

- **✅ Backward Compatible**: Existing code continues to work
- **🚀 Enhanced APIs**: New features available through extended APIs
- **📦 Modular Installation**: Choose only the features you need
- **🔧 Configuration Updates**: New configuration options (all optional)

---

## 📦 Installation Updates

### **New Installation Options**
```bash
# Basic installation (same as before)
uv add video-processor

# Install with specific feature sets
uv add video-processor[ai]        # Add AI analysis
uv add video-processor[360]       # Add 360° processing
uv add video-processor[streaming] # Add adaptive streaming
uv add video-processor[all]       # Install everything

# Development installation
uv add video-processor[dev]       # Development dependencies
```

### **Optional Dependencies**
The new features require additional dependencies that are automatically installed with feature flags:

```bash
# AI Analysis features
pip install opencv-python numpy

# 360° Processing features  
pip install numpy opencv-python

# No additional dependencies needed for:
# - Advanced codecs (uses system FFmpeg)
# - Adaptive streaming (uses existing dependencies)
```

---

## 🔧 Configuration Migration

### **Before (v0.3.x)**
```python
from video_processor import ProcessorConfig

config = ProcessorConfig(
    quality_preset="medium",
    output_formats=["mp4"],
    base_path="/tmp/videos"
)
```

### **After (v0.4.0) - Backward Compatible**
```python
from video_processor import ProcessorConfig

# Your existing config still works exactly the same
config = ProcessorConfig(
    quality_preset="medium", 
    output_formats=["mp4"],
    base_path="/tmp/videos"
)

# But now you can add new optional features
config = ProcessorConfig(
    # Existing settings (unchanged)
    quality_preset="medium",
    output_formats=["mp4"],
    base_path="/tmp/videos",
    
    # New optional AI features
    enable_ai_analysis=True,  # Default: True
    
    # New optional codec features
    enable_av1_encoding=False,  # Default: False
    enable_hevc_encoding=False,  # Default: False
    enable_hdr_processing=False,  # Default: False
    
    # New optional 360° features
    enable_360_processing=True,  # Default: auto-detected
    auto_detect_360=True,  # Default: True
    generate_360_thumbnails=True,  # Default: True
)
```

---

## 📝 API Migration Examples

### **Basic Video Processing (No Changes Required)**

**Before:**
```python
from video_processor import VideoProcessor

processor = VideoProcessor(config)
result = await processor.process_video("input.mp4", "./output/")
print(f"Encoded files: {result.encoded_files}")
```

**After (Same Code Works):**
```python
from video_processor import VideoProcessor

processor = VideoProcessor(config) 
result = await processor.process_video("input.mp4", "./output/")
print(f"Encoded files: {result.encoded_files}")

# But now you get additional information automatically:
if hasattr(result, 'quality_analysis'):
    print(f"Quality score: {result.quality_analysis.overall_quality:.1f}/10")

if hasattr(result, 'is_360_video') and result.is_360_video:
    print(f"360° projection: {result.video_360.projection_type}")
```

### **Enhanced Results Object**

**Before:**
```python
# v0.3.x result object
result.video_id           # Video identifier
result.encoded_files      # Dict of encoded files  
result.thumbnail_files    # List of thumbnail files
result.sprite_files       # Dict of sprite files
```

**After (All Previous Fields + New Ones):**
```python
# v0.4.0 result object - everything from before PLUS:
result.video_id           # ✅ Same as before
result.encoded_files      # ✅ Same as before  
result.thumbnail_files    # ✅ Same as before
result.sprite_files       # ✅ Same as before

# New optional fields (only present if features enabled):
result.quality_analysis   # AI quality assessment (if AI enabled)
result.is_360_video      # Boolean for 360° detection
result.video_360         # 360° analysis (if 360° video detected)
result.streaming_ready   # Streaming package info (if streaming enabled)
```

---

## 🆕 Adopting New Features

### **Phase 1: AI-Powered Content Analysis**

**Add AI analysis to existing workflows:**
```python
# Enable AI analysis (requires opencv-python)
config = ProcessorConfig(
    # ... your existing settings ...
    enable_ai_analysis=True  # New feature
)

processor = VideoProcessor(config)
result = await processor.process_video("input.mp4", "./output/")

# Access new AI insights
if result.quality_analysis:
    print(f"Scene count: {result.quality_analysis.scenes.scene_count}")
    print(f"Motion intensity: {result.quality_analysis.motion_intensity:.2f}")
    print(f"Quality score: {result.quality_analysis.quality_metrics.overall_quality:.2f}")
    print(f"Optimal thumbnails: {result.quality_analysis.recommended_thumbnails}")
```

### **Phase 2: Advanced Codecs**

**Add modern codec support:**
```python
config = ProcessorConfig(
    # Add new formats to existing output_formats
    output_formats=["mp4", "av1_mp4", "hevc"],  # Enhanced list
    
    # Enable advanced features
    enable_av1_encoding=True,
    enable_hevc_encoding=True,
    enable_hdr_processing=True,  # For HDR content
    
    quality_preset="ultra"  # Can now use "ultra" preset
)

# Same processing call - just get more output formats
result = await processor.process_video("input.mp4", "./output/")
print(f"Generated formats: {list(result.encoded_files.keys())}")
# Output: ['mp4', 'av1_mp4', 'hevc']
```

### **Phase 3: Adaptive Streaming**

**Add streaming capabilities to existing workflows:**
```python
from video_processor.streaming import AdaptiveStreamProcessor

# Process video normally first
processor = VideoProcessor(config)
result = await processor.process_video("input.mp4", "./output/")

# Then create streaming package
stream_processor = AdaptiveStreamProcessor(config)
streaming_package = await stream_processor.create_adaptive_stream(
    video_path="input.mp4",
    output_dir="./streaming/",
    formats=["hls", "dash"]
)

print(f"HLS playlist: {streaming_package.hls_playlist}")
print(f"DASH manifest: {streaming_package.dash_manifest}")
```

### **Phase 4: 360° Video Processing**

**Add 360° support (automatically detected):**
```python
# Enable 360° processing
config = ProcessorConfig(
    # ... your existing settings ...
    enable_360_processing=True,  # Default: auto-detected
    auto_detect_360=True,        # Automatic detection
    generate_360_thumbnails=True  # 360° specific thumbnails
)

# Same processing call - automatically handles 360° videos
processor = VideoProcessor(config)
result = await processor.process_video("360_video.mp4", "./output/")

# Check if 360° video was detected
if result.is_360_video:
    print(f"360° projection: {result.video_360.projection_type}")
    print(f"Spatial audio: {result.video_360.has_spatial_audio}")
    print(f"Recommended viewports: {len(result.video_360.optimal_viewports)}")
    
    # Access 360° specific outputs
    print(f"360° thumbnails: {result.video_360.thumbnail_tracks}")
```

---

## 🗄️ Database Migration

### **Procrastinate Task System Updates**

If you're using the Procrastinate task system, there are new database fields:

**Automatic Migration:**
```bash
# Migration is handled automatically when you upgrade
uv run python -m video_processor.tasks.migration migrate

# Or use the enhanced migration system
from video_processor.tasks.migration import ProcrastinateMigrator

migrator = ProcrastinateMigrator(db_url)
await migrator.migrate_to_latest()
```

**New Database Fields (Added Automatically):**
- `quality_analysis`: JSON field for AI analysis results
- `is_360_video`: Boolean for 360° video detection  
- `video_360_metadata`: JSON field for 360° specific data
- `streaming_outputs`: JSON field for streaming package info

### **Worker Compatibility**

**Backward Compatible**: Existing workers continue to work with new tasks:

```python
# Existing workers automatically support new features
# No code changes required in worker processes

# But you can enable enhanced processing:
from video_processor.tasks.enhanced_worker import EnhancedWorker

# Enhanced worker with all new features
worker = EnhancedWorker(
    enable_ai_analysis=True,
    enable_360_processing=True,
    enable_advanced_codecs=True
)
```

---

## ⚠️ Breaking Changes (Minimal)

### **None for Basic Usage**
- ✅ All existing APIs work unchanged
- ✅ Configuration is backward compatible  
- ✅ Database migrations are automatic
- ✅ Workers continue functioning normally

### **Optional Breaking Changes (Advanced Usage)**

**1. Custom Encoder Implementations**
If you've implemented custom encoders, you may want to update them:

```python
# Before (still works)
class CustomEncoder:
    def encode_video(self, input_path, output_path, options):
        # Your implementation
        pass

# After (enhanced with new features)
class CustomEncoder:
    def encode_video(self, input_path, output_path, options):
        # Your implementation
        pass
    
    # Optional: Add support for new codecs
    def supports_av1(self):
        return False  # Override if you support AV1
        
    def supports_hevc(self):
        return False  # Override if you support HEVC
```

**2. Custom Storage Backends**
Custom storage backends gain new optional methods:

```python
# Before (still works)
class CustomStorageBackend:
    def store_file(self, source, destination):
        # Your implementation
        pass

# After (optional enhancements)
class CustomStorageBackend:
    def store_file(self, source, destination):
        # Your implementation  
        pass
    
    # Optional: Handle 360° specific files
    def store_360_files(self, files_dict, base_path):
        # Default implementation calls store_file for each
        for name, path in files_dict.items():
            self.store_file(path, base_path / name)
    
    # Optional: Handle streaming manifests
    def store_streaming_package(self, package, base_path):
        # Default implementation available
        pass
```

---

## 🧪 Testing Your Migration

### **Basic Compatibility Test**
```python
import asyncio
from video_processor import VideoProcessor, ProcessorConfig

async def test_migration():
    # Test with your existing configuration
    config = ProcessorConfig(
        # Your existing settings here
        quality_preset="medium",
        output_formats=["mp4"]
    )
    
    processor = VideoProcessor(config)
    
    # This should work exactly as before
    result = await processor.process_video("test_video.mp4", "./output/")
    
    print("✅ Basic compatibility: PASSED")
    print(f"Encoded files: {list(result.encoded_files.keys())}")
    
    # Test new features if enabled
    if hasattr(result, 'quality_analysis'):
        print("✅ AI analysis: ENABLED")
        
    if hasattr(result, 'is_360_video'):
        print("✅ 360° detection: ENABLED")
        
    return result

# Run compatibility test
result = asyncio.run(test_migration())
```

### **Feature Test Suite**
```bash
# Run the built-in migration tests
uv run pytest tests/test_migration_compatibility.py -v

# Test specific features
uv run pytest tests/test_360_basic.py -v          # 360° features
uv run pytest tests/unit/test_ai_content_analyzer.py -v  # AI features  
uv run pytest tests/unit/test_adaptive_streaming.py -v   # Streaming features
```

---

## 📚 Getting Help

### **Documentation Resources**
- 📖 **NEW_FEATURES_v0.4.0.md**: Complete feature overview
- 🔧 **examples/**: 20+ updated examples showing new capabilities
- 🏗️ **COMPREHENSIVE_DEVELOPMENT_SUMMARY.md**: Full architecture overview
- 🧪 **tests/**: Comprehensive test suite with examples

### **Common Migration Scenarios**

**Scenario 1: Just want better quality**
```python
config = ProcessorConfig(
    quality_preset="ultra",  # New preset available
    enable_ai_analysis=True  # Better thumbnail selection
)
```

**Scenario 2: Need modern codecs**
```python  
config = ProcessorConfig(
    output_formats=["mp4", "av1_mp4"],  # Add AV1
    enable_av1_encoding=True
)
```

**Scenario 3: Have 360° videos**
```python
config = ProcessorConfig(
    enable_360_processing=True,  # Auto-detects 360° videos
    generate_360_thumbnails=True
)
```

**Scenario 4: Need streaming**
```python
# Process video first, then create streams
streaming_package = await stream_processor.create_adaptive_stream(
    video_path, streaming_dir, formats=["hls", "dash"]
)
```

### **Support & Community**
- 🐛 **Issues**: Report problems in GitHub issues
- 💡 **Feature Requests**: Suggest improvements  
- 📧 **Migration Help**: Tag issues with `migration-help`
- 📖 **Documentation**: Full API docs available

---

## 🎯 Recommended Migration Path

### **Step 1: Update Dependencies**
```bash
# Update to latest version
uv add video-processor

# Install optional dependencies for features you want
uv add video-processor[ai,360,streaming]
```

### **Step 2: Test Existing Code**
```python
# Run your existing code - should work unchanged
# Enable logging to see new features being detected
import logging
logging.basicConfig(level=logging.INFO)
```

### **Step 3: Enable New Features Gradually**
```python
# Start with AI analysis (most universal benefit)
config.enable_ai_analysis = True

# Add advanced codecs if you need better compression
config.enable_av1_encoding = True
config.output_formats.append("av1_mp4")

# Enable 360° if you process immersive videos  
config.enable_360_processing = True

# Add streaming for web delivery
# (Separate API call - doesn't change existing workflow)
```

### **Step 4: Update Your Code to Use New Features**
```python
# Take advantage of new analysis results
if result.quality_analysis:
    # Use AI-recommended thumbnails
    best_thumbnails = result.quality_analysis.recommended_thumbnails
    
if result.is_360_video:
    # Handle 360° specific outputs
    projection = result.video_360.projection_type
    viewports = result.video_360.optimal_viewports
```

This migration maintains **100% backward compatibility** while giving you access to cutting-edge video processing capabilities. Your existing code continues working while you gradually adopt new features at your own pace.

---

*Need help with migration? Check our examples directory or create a GitHub issue with the `migration-help` tag.*