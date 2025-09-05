"""
Video Processor - Standalone video processing pipeline.

A professional video processing library extracted from the demostar system,
featuring multiple format encoding, thumbnail generation, and background processing.
"""

from .config import ProcessorConfig
from .core.processor import VideoProcessor
from .exceptions import EncodingError, StorageError, VideoProcessorError

# Optional 360° imports
try:
    from .core.thumbnails_360 import Thumbnail360Generator
    from .utils.video_360 import HAS_360_SUPPORT, Video360Detection, Video360Utils
except ImportError:
    HAS_360_SUPPORT = False

__version__ = "0.1.0"
__all__ = [
    "VideoProcessor",
    "ProcessorConfig",
    "VideoProcessorError",
    "EncodingError",
    "StorageError",
    "HAS_360_SUPPORT",
]

# Add 360° exports if available
if HAS_360_SUPPORT:
    __all__.extend([
        "Video360Detection",
        "Video360Utils",
        "Thumbnail360Generator",
    ])
