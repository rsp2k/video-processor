"""
Video Processor - Standalone video processing pipeline.

A professional video processing library extracted from the demostar system,
featuring multiple format encoding, thumbnail generation, and background processing.
"""

from .config import ProcessorConfig
from .core.processor import VideoProcessor
from .exceptions import EncodingError, StorageError, VideoProcessorError

__version__ = "0.1.0"
__all__ = [
    "VideoProcessor",
    "ProcessorConfig",
    "VideoProcessorError",
    "EncodingError",
    "StorageError",
]
