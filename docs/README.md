# 📚 Video Processor Documentation

Welcome to the comprehensive documentation for **Video Processor v0.4.0** - the ultimate Python library for professional video processing and immersive media.

## 🗂️ Documentation Structure

### 📖 [User Guide](user-guide/)
Complete guides for end users and developers getting started with the video processor.

| Document | Description |
|----------|-------------|
| **[🚀 NEW_FEATURES_v0.4.0.md](user-guide/NEW_FEATURES_v0.4.0.md)** | Complete feature overview with examples for v0.4.0 |
| **[📘 README_v0.4.0.md](user-guide/README_v0.4.0.md)** | Comprehensive getting started guide and API reference |

### 🔄 [Migration & Upgrades](migration/)
Guides for upgrading between versions and migrating existing installations.

| Document | Description |
|----------|-------------|
| **[🔄 MIGRATION_GUIDE_v0.4.0.md](migration/MIGRATION_GUIDE_v0.4.0.md)** | Step-by-step upgrade instructions from previous versions |
| **[⬆️ UPGRADE.md](migration/UPGRADE.md)** | General upgrade procedures and best practices |

### 🛠️ [Development](development/)
Technical documentation for developers working on or extending the video processor.

| Document | Description |
|----------|-------------|
| **[🏗️ COMPREHENSIVE_DEVELOPMENT_SUMMARY.md](development/COMPREHENSIVE_DEVELOPMENT_SUMMARY.md)** | Complete development history and architecture decisions |

### 📋 [Reference](reference/)
API references, feature lists, and project roadmaps.

| Document | Description |
|----------|-------------|
| **[⚡ ADVANCED_FEATURES.md](reference/ADVANCED_FEATURES.md)** | Complete list of advanced features and capabilities |
| **[🗺️ ROADMAP.md](reference/ROADMAP.md)** | Project roadmap and future development plans |
| **[📝 CHANGELOG.md](reference/CHANGELOG.md)** | Detailed version history and changes |

### 💻 [Examples](examples/)
Comprehensive examples demonstrating all features and capabilities.

| Category | Examples | Description |
|----------|----------|-------------|
| **🚀 Getting Started** | [examples/](examples/) | Complete example documentation with 11 detailed examples |
| **🤖 AI Features** | `ai_enhanced_processing.py` | AI-powered content analysis and optimization |
| **🎥 Advanced Codecs** | `advanced_codecs_demo.py` | AV1, HEVC, and HDR processing |
| **📡 Streaming** | `streaming_demo.py` | Adaptive streaming (HLS/DASH) creation |
| **🌐 360° Video** | `360_video_examples.py` | Complete 360° processing with 7 examples |
| **🐳 Production** | `docker_demo.py`, `worker_compatibility.py` | Deployment and scaling |

---

## 🎯 Quick Navigation

### **New to Video Processor?**
Start here for a complete introduction:
1. **[📘 User Guide](user-guide/README_v0.4.0.md)** - Complete getting started guide
2. **[💻 Basic Examples](examples/)** - Hands-on examples to get you started
3. **[🚀 New Features](user-guide/NEW_FEATURES_v0.4.0.md)** - What's new in v0.4.0

### **Upgrading from Previous Version?**
Follow our migration guides:
1. **[🔄 Migration Guide](migration/MIGRATION_GUIDE_v0.4.0.md)** - Step-by-step upgrade instructions
2. **[📝 Changelog](reference/CHANGELOG.md)** - See what's changed

### **Looking for Specific Features?**
- **🤖 AI Analysis**: [AI Implementation Summary](development/AI_IMPLEMENTATION_SUMMARY.md)
- **🎥 Modern Codecs**: [Codec Implementation](development/PHASE_2_CODECS_SUMMARY.md)
- **📡 Streaming**: [Streaming Examples](examples/#-streaming-examples)
- **🌐 360° Video**: [360° Examples](examples/#-360-video-processing)

### **Need Technical Details?**
- **🏗️ Architecture**: [Development Summary](development/COMPREHENSIVE_DEVELOPMENT_SUMMARY.md)
- **⚡ Advanced Features**: [Feature Reference](reference/ADVANCED_FEATURES.md)
- **🗺️ Roadmap**: [Future Plans](reference/ROADMAP.md)

---

## 🎬 Video Processor Capabilities

The Video Processor v0.4.0 provides a complete multimedia processing platform with four integrated phases:

### **🤖 Phase 1: AI-Powered Content Analysis**
- Intelligent scene detection and boundary identification
- Comprehensive quality assessment (sharpness, brightness, contrast)
- Motion analysis with intensity scoring
- AI-powered thumbnail selection for optimal engagement
- 360° content intelligence with automatic detection

### **🎥 Phase 2: Next-Generation Codecs**
- **AV1 encoding** with 50% better compression than H.264
- **HEVC/H.265** support with hardware acceleration
- **HDR10 processing** with tone mapping and metadata preservation
- **Multi-color space** support (Rec.2020, P3, sRGB)
- **Two-pass optimization** for intelligent bitrate allocation

### **📡 Phase 3: Adaptive Streaming**
- **HLS & DASH** adaptive streaming with multi-bitrate support
- **Smart bitrate ladders** based on content analysis
- **Real-time processing** with Procrastinate async tasks
- **Multi-device optimization** for mobile, desktop, TV
- **Progressive upload** capabilities

### **🌐 Phase 4: Complete 360° Video Processing**
- **Multi-projection support**: Equirectangular, Cubemap, EAC, Stereographic, Fisheye
- **Spatial audio processing**: Ambisonic, binaural, object-based, head-locked
- **Viewport-adaptive streaming** with up to 75% bandwidth savings
- **Tiled encoding** for streaming only visible regions
- **Stereoscopic 3D** support for immersive content

---

## 🚀 Quick Start

### **Installation**
```bash
# Install with all features
uv add video-processor[all]

# Or install specific feature sets
uv add video-processor[ai,360,streaming]
```

### **Basic Usage**
```python
from video_processor import VideoProcessor
from video_processor.config import ProcessorConfig

# Initialize with all features
config = ProcessorConfig(
    quality_preset="high",
    enable_ai_analysis=True,
    enable_360_processing=True,
    output_formats=["mp4", "av1_mp4"]
)

processor = VideoProcessor(config)

# Process any video (2D or 360°) with full analysis
result = await processor.process_video("input.mp4", "./output/")

# Automatic optimization based on content type
if result.is_360_video:
    print(f"🌐 360° {result.video_360.projection_type} processed")
else:
    print("🎥 Standard video processed with AI analysis")

print(f"Quality: {result.quality_analysis.overall_quality:.1f}/10")
```

For complete examples, see the **[Examples Documentation](examples/)**.

---

## 🔧 Development & Contributing

### **Development Setup**
```bash
git clone https://git.supported.systems/MCP/video-processor
cd video-processor
uv sync --dev
```

### **Running Tests**
```bash
# Full test suite
uv run pytest

# Specific feature tests
uv run pytest tests/test_360_basic.py -v
uv run pytest tests/unit/test_ai_content_analyzer.py -v
```

### **Code Quality**
```bash
uv run ruff check .    # Linting
uv run mypy src/       # Type checking
uv run ruff format .   # Code formatting
```

See the **[Development Documentation](development/)** for detailed technical information.

---

## 🤝 Community & Support

- **📖 Documentation**: You're here! Complete guides and references
- **💻 Examples**: [examples/](examples/) - 11 comprehensive examples
- **🐛 Issues**: Report bugs and request features on the repository
- **🚀 Discussions**: Share use cases and get help from the community
- **📧 Support**: Tag issues with appropriate labels for faster response

---

## 📜 License

MIT License - see [LICENSE](../LICENSE) for details.

---

<div align="center">

**🎬 Video Processor v0.4.0**

*From Simple Encoding to Immersive Experiences*

**Complete Multimedia Processing Platform** | **Production Ready** | **Open Source**

</div>