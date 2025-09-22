"""
Video Processor - AI-Enhanced Professional Video Processing Library.

Features comprehensive video processing with 360° support, AI-powered content analysis,
multiple format encoding, intelligent thumbnail generation, and background processing.
"""

from .config import ProcessorConfig
from .core.processor import VideoProcessingResult, VideoProcessor
from .exceptions import (
    EncodingError,
    FFmpegError,
    StorageError,
    ValidationError,
    VideoProcessorError,
)

# Optional 360° imports
try:
    from .core.thumbnails_360 import Thumbnail360Generator
    from .utils.video_360 import HAS_360_SUPPORT, Video360Detection, Video360Utils
except ImportError:
    HAS_360_SUPPORT = False

# Optional AI imports
try:
    from .ai import ContentAnalysis, SceneAnalysis, VideoContentAnalyzer
    from .core.enhanced_processor import (
        EnhancedVideoProcessingResult,
        EnhancedVideoProcessor,
    )

    HAS_AI_SUPPORT = True
except ImportError:
    HAS_AI_SUPPORT = False

# Advanced codecs imports
try:
    from .core.advanced_encoders import AdvancedVideoEncoder, HDRProcessor

    HAS_ADVANCED_CODECS = True
except ImportError:
    HAS_ADVANCED_CODECS = False

__version__ = "0.3.0"
__all__ = [
    "VideoProcessor",
    "VideoProcessingResult",
    "ProcessorConfig",
    "VideoProcessorError",
    "ValidationError",
    "StorageError",
    "EncodingError",
    "FFmpegError",
    "HAS_360_SUPPORT",
    "HAS_AI_SUPPORT",
    "HAS_ADVANCED_CODECS",
]

# Add 360° exports if available
if HAS_360_SUPPORT:
    __all__.extend(
        [
            "Video360Detection",
            "Video360Utils",
            "Thumbnail360Generator",
        ]
    )

# Add AI exports if available
if HAS_AI_SUPPORT:
    __all__.extend(
        [
            "EnhancedVideoProcessor",
            "EnhancedVideoProcessingResult",
            "VideoContentAnalyzer",
            "ContentAnalysis",
            "SceneAnalysis",
        ]
    )

# Add advanced codec exports if available
if HAS_ADVANCED_CODECS:
    __all__.extend(
        [
            "AdvancedVideoEncoder",
            "HDRProcessor",
        ]
    )
