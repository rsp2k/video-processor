"""Custom exceptions for video processing."""


class VideoProcessorError(Exception):
    """Base exception for video processor errors."""


class EncodingError(VideoProcessorError):
    """Raised when video encoding fails."""


class StorageError(VideoProcessorError):
    """Raised when storage operations fail."""


class ValidationError(VideoProcessorError):
    """Raised when input validation fails."""


class FFmpegError(VideoProcessorError):
    """Raised when FFmpeg operations fail."""
