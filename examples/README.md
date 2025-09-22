# 📚 Examples Documentation

This directory contains comprehensive examples demonstrating all features of the Video Processor v0.4.0.

## 🚀 Getting Started Examples

### [basic_usage.py](../../examples/basic_usage.py)
**Start here!** Shows the fundamental video processing workflow with the main `VideoProcessor` class.

```python
# Simple video processing
processor = VideoProcessor(config)
result = await processor.process_video("input.mp4", "./output/")
```

### [custom_config.py](../../examples/custom_config.py)
Demonstrates advanced configuration options and quality presets.

```python
# Custom configuration for different use cases
config = ProcessorConfig(
    quality_preset="ultra",
    output_formats=["mp4", "av1_mp4"],
    enable_ai_analysis=True
)
```

## 🤖 AI-Powered Features

### [ai_enhanced_processing.py](../../examples/ai_enhanced_processing.py)
Complete AI content analysis with scene detection and quality assessment.

```python
# AI-powered content analysis
analysis = await analyzer.analyze_content(video_path)
print(f"Scenes: {analysis.scenes.scene_count}")
print(f"Quality: {analysis.quality_metrics.overall_quality}")
```

## 🎥 Advanced Codec Examples

### [advanced_codecs_demo.py](../../examples/advanced_codecs_demo.py)
Demonstrates AV1, HEVC, and HDR processing capabilities.

```python
# Modern codec encoding
config = ProcessorConfig(
    output_formats=["mp4", "av1_mp4", "hevc"],
    enable_av1_encoding=True,
    enable_hdr_processing=True
)
```

## 📡 Streaming Examples

### [streaming_demo.py](../../examples/streaming_demo.py)
Shows how to create adaptive streaming packages (HLS/DASH) for web delivery.

```python
# Create adaptive streaming
streaming_package = await stream_processor.create_adaptive_stream(
    video_path, output_dir, formats=["hls", "dash"]
)
```

## 🌐 360° Video Processing

### [360_video_examples.py](../../examples/360_video_examples.py)
**Comprehensive 360° showcase** with 7 detailed examples:

1. **Basic 360° Analysis** - Detect and analyze spherical videos
2. **Projection Conversion** - Convert between equirectangular, cubemap, etc.
3. **Viewport Extraction** - Extract flat videos from specific viewing angles
4. **Spatial Audio Processing** - Handle ambisonic and binaural audio
5. **360° Adaptive Streaming** - Viewport-adaptive streaming with bandwidth optimization
6. **Batch Processing** - Convert multiple projections in parallel
7. **Quality Analysis** - Assess 360° video quality and get optimization recommendations

### [video_360_example.py](../../examples/video_360_example.py)
Focused example showing core 360° processing features.

## 🐳 Production Deployment

### [docker_demo.py](../../examples/docker_demo.py)
Production deployment with Docker containers and environment configuration.

### [worker_compatibility.py](../../examples/worker_compatibility.py)
Distributed processing with Procrastinate workers for scalable deployments.

### [async_processing.py](../../examples/async_processing.py)
Advanced async patterns for high-throughput video processing.

## 🌐 Web Integration

### [web_demo.py](../../examples/web_demo.py)
Flask web application demonstrating video processing API integration.

```python
# Web API endpoint
@app.post("/process")
async def process_video_api(file: UploadFile):
    result = await processor.process_video(file.path, output_dir)
    return {"status": "success", "formats": list(result.encoded_files.keys())}
```

## 🏃‍♂️ Running the Examples

### Prerequisites
```bash
# Install with all features
uv add video-processor[all]

# Or install specific feature sets
uv add video-processor[ai,360,streaming]
```

### Basic Examples
```bash
# Run basic usage example
uv run python examples/basic_usage.py

# Test AI analysis
uv run python examples/ai_enhanced_processing.py

# Try 360° processing
uv run python examples/360_video_examples.py
```

### Advanced Examples
```bash
# Set up Docker environment
uv run python examples/docker_demo.py

# Test streaming capabilities
uv run python examples/streaming_demo.py

# Run web demo (requires Flask)
uv add flask
uv run python examples/web_demo.py
```

## 🎯 Example Categories

| Category | Examples | Features Demonstrated |
|----------|----------|----------------------|
| **Basics** | `basic_usage.py`, `custom_config.py` | Core processing, configuration |
| **AI Features** | `ai_enhanced_processing.py` | Scene detection, quality analysis |
| **Modern Codecs** | `advanced_codecs_demo.py` | AV1, HEVC, HDR processing |
| **Streaming** | `streaming_demo.py` | HLS, DASH adaptive streaming |
| **360° Video** | `360_video_examples.py`, `video_360_example.py` | Immersive video processing |
| **Production** | `docker_demo.py`, `worker_compatibility.py` | Deployment, scaling |
| **Integration** | `web_demo.py`, `async_processing.py` | Web APIs, async patterns |

## 💡 Tips for Learning

1. **Start Simple**: Begin with `basic_usage.py` to understand the core concepts
2. **Progress Gradually**: Move through AI → Codecs → Streaming → 360° features
3. **Experiment**: Modify the examples with your own video files
4. **Check Logs**: Enable logging to see detailed processing information
5. **Read Comments**: Each example includes detailed explanations and best practices

## 🔧 Troubleshooting

### Common Issues

**Missing Dependencies**
```bash
# AI features require OpenCV
pip install opencv-python

# 360° processing needs additional packages
pip install numpy opencv-python
```

**FFmpeg Not Found**
```bash
# Install FFmpeg (varies by OS)
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from ffmpeg.org
```

**Import Errors**
```bash
# Ensure video-processor is installed
uv add video-processor

# For development
uv sync --dev
```

### Getting Help

- Check the [migration guide](../migration/MIGRATION_GUIDE_v0.4.0.md) for upgrade instructions
- See [user guide](../user-guide/NEW_FEATURES_v0.4.0.md) for complete feature documentation
- Review [development docs](../development/) for technical implementation details

---

*These examples demonstrate the full capabilities of Video Processor v0.4.0 - from simple format conversion to advanced 360° immersive experiences with AI optimization.*