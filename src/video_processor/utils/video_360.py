"""360° video detection and utility functions."""

from pathlib import Path
from typing import Any, Literal

# Optional dependency handling
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import py360convert
    HAS_PY360CONVERT = True
except ImportError:
    HAS_PY360CONVERT = False

try:
    import exifread
    HAS_EXIFREAD = True
except ImportError:
    HAS_EXIFREAD = False

# Overall 360° support requires core dependencies
HAS_360_SUPPORT = HAS_OPENCV and HAS_NUMPY and HAS_PY360CONVERT


ProjectionType = Literal["equirectangular", "cubemap", "cylindrical", "stereographic", "unknown"]
StereoMode = Literal["mono", "top-bottom", "left-right", "unknown"]


class Video360Detection:
    """Utilities for detecting and analyzing 360° videos."""
    
    @staticmethod
    def detect_360_video(video_metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Detect if a video is a 360° video based on metadata and resolution.
        
        Args:
            video_metadata: Video metadata dictionary from ffmpeg probe
            
        Returns:
            Dictionary with 360° detection results
        """
        detection_result = {
            "is_360_video": False,
            "projection_type": "unknown",
            "stereo_mode": "mono",
            "confidence": 0.0,
            "detection_methods": [],
        }
        
        # Check for spherical video metadata (Google/YouTube standard)
        spherical_metadata = Video360Detection._check_spherical_metadata(video_metadata)
        if spherical_metadata["found"]:
            detection_result.update({
                "is_360_video": True,
                "projection_type": spherical_metadata["projection_type"],
                "stereo_mode": spherical_metadata["stereo_mode"],
                "confidence": 1.0,
            })
            detection_result["detection_methods"].append("spherical_metadata")
        
        # Check aspect ratio for equirectangular projection
        aspect_ratio_check = Video360Detection._check_aspect_ratio(video_metadata)
        if aspect_ratio_check["is_likely_360"]:
            if not detection_result["is_360_video"]:
                detection_result.update({
                    "is_360_video": True,
                    "projection_type": "equirectangular",
                    "confidence": aspect_ratio_check["confidence"],
                })
            detection_result["detection_methods"].append("aspect_ratio")
        
        # Check filename patterns
        filename_check = Video360Detection._check_filename_patterns(video_metadata)
        if filename_check["is_likely_360"]:
            if not detection_result["is_360_video"]:
                detection_result.update({
                    "is_360_video": True,
                    "projection_type": filename_check["projection_type"],
                    "confidence": filename_check["confidence"],
                })
            detection_result["detection_methods"].append("filename")
        
        return detection_result
    
    @staticmethod
    def _check_spherical_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """Check for spherical video metadata tags."""
        result = {
            "found": False,
            "projection_type": "equirectangular",
            "stereo_mode": "mono",
        }
        
        # Check format tags for spherical metadata
        format_tags = metadata.get("format", {}).get("tags", {})
        
        # Google spherical video standard
        if "spherical" in format_tags:
            result["found"] = True
            
        # Check for specific spherical video tags
        spherical_indicators = [
            "Spherical",
            "spherical-video",
            "SphericalVideo",
            "ProjectionType",
            "projection_type",
        ]
        
        for tag_name, tag_value in format_tags.items():
            if any(indicator.lower() in tag_name.lower() for indicator in spherical_indicators):
                result["found"] = True
                
                # Determine projection type from metadata
                if isinstance(tag_value, str):
                    tag_lower = tag_value.lower()
                    if "equirectangular" in tag_lower:
                        result["projection_type"] = "equirectangular"
                    elif "cubemap" in tag_lower:
                        result["projection_type"] = "cubemap"
        
        # Check for stereo mode indicators
        stereo_indicators = ["StereoMode", "stereo_mode", "StereoscopicMode"]
        for tag_name, tag_value in format_tags.items():
            if any(indicator.lower() in tag_name.lower() for indicator in stereo_indicators):
                if isinstance(tag_value, str):
                    tag_lower = tag_value.lower()
                    if "top-bottom" in tag_lower or "tb" in tag_lower:
                        result["stereo_mode"] = "top-bottom"
                    elif "left-right" in tag_lower or "lr" in tag_lower:
                        result["stereo_mode"] = "left-right"
        
        return result
    
    @staticmethod
    def _check_aspect_ratio(metadata: dict[str, Any]) -> dict[str, Any]:
        """Check if aspect ratio suggests 360° video."""
        result = {
            "is_likely_360": False,
            "confidence": 0.0,
        }
        
        video_info = metadata.get("video", {})
        if not video_info:
            return result
        
        width = video_info.get("width", 0)
        height = video_info.get("height", 0)
        
        if width <= 0 or height <= 0:
            return result
        
        aspect_ratio = width / height
        
        # Equirectangular videos typically have 2:1 aspect ratio
        if 1.9 <= aspect_ratio <= 2.1:
            result["is_likely_360"] = True
            result["confidence"] = 0.8
            
            # Higher confidence for exact 2:1 ratio
            if 1.98 <= aspect_ratio <= 2.02:
                result["confidence"] = 0.9
        
        # Some 360° videos use different aspect ratios
        elif 1.5 <= aspect_ratio <= 2.5:
            # Common resolutions for 360° video
            common_360_resolutions = [
                (3840, 1920),  # 4K 360°
                (1920, 960),   # 2K 360°
                (2560, 1280),  # QHD 360°
                (4096, 2048),  # Cinema 4K 360°
                (5760, 2880),  # 6K 360°
            ]
            
            for res_width, res_height in common_360_resolutions:
                if (width == res_width and height == res_height) or \
                   (width == res_height and height == res_width):
                    result["is_likely_360"] = True
                    result["confidence"] = 0.7
                    break
        
        return result
    
    @staticmethod
    def _check_filename_patterns(metadata: dict[str, Any]) -> dict[str, Any]:
        """Check filename for 360° indicators."""
        result = {
            "is_likely_360": False,
            "projection_type": "equirectangular",
            "confidence": 0.0,
        }
        
        filename = metadata.get("filename", "").lower()
        if not filename:
            return result
        
        # Common 360° filename patterns
        patterns_360 = [
            "360", "vr", "spherical", "equirectangular", 
            "panoramic", "immersive", "omnidirectional"
        ]
        
        # Projection type patterns
        projection_patterns = {
            "equirectangular": ["equirect", "equi", "spherical"],
            "cubemap": ["cube", "cubemap", "cubic"],
            "cylindrical": ["cylindrical", "cylinder"],
        }
        
        # Check for 360° indicators
        for pattern in patterns_360:
            if pattern in filename:
                result["is_likely_360"] = True
                result["confidence"] = 0.6
                break
        
        # Check for specific projection types
        if result["is_likely_360"]:
            for projection, patterns in projection_patterns.items():
                if any(pattern in filename for pattern in patterns):
                    result["projection_type"] = projection
                    result["confidence"] = 0.7
                    break
        
        return result


class Video360Utils:
    """Utility functions for 360° video processing."""
    
    @staticmethod
    def get_recommended_bitrate_multiplier(projection_type: ProjectionType) -> float:
        """
        Get recommended bitrate multiplier for 360° videos.
        
        360° videos typically need higher bitrates than regular videos
        due to the immersive viewing experience and projection distortion.
        
        Args:
            projection_type: Type of 360° projection
            
        Returns:
            Multiplier to apply to standard bitrates
        """
        multipliers = {
            "equirectangular": 2.5,  # Most common, needs high bitrate
            "cubemap": 2.0,          # More efficient encoding
            "cylindrical": 1.8,      # Less immersive, lower multiplier
            "stereographic": 2.2,    # Good balance
            "unknown": 2.0,          # Safe default
        }
        
        return multipliers.get(projection_type, 2.0)
    
    @staticmethod
    def get_optimal_resolutions(projection_type: ProjectionType) -> list[tuple[int, int]]:
        """
        Get optimal resolutions for different 360° projection types.
        
        Args:
            projection_type: Type of 360° projection
            
        Returns:
            List of (width, height) tuples for optimal resolutions
        """
        resolutions = {
            "equirectangular": [
                (1920, 960),   # 2K 360°
                (2560, 1280),  # QHD 360°
                (3840, 1920),  # 4K 360°
                (4096, 2048),  # Cinema 4K 360°
                (5760, 2880),  # 6K 360°
                (7680, 3840),  # 8K 360°
            ],
            "cubemap": [
                (1536, 1536),  # 1.5K per face
                (2048, 2048),  # 2K per face
                (3072, 3072),  # 3K per face
                (4096, 4096),  # 4K per face
            ],
        }
        
        return resolutions.get(projection_type, resolutions["equirectangular"])
    
    @staticmethod
    def is_360_library_available() -> bool:
        """Check if 360° processing libraries are available."""
        return HAS_360_SUPPORT
    
    @staticmethod
    def get_missing_dependencies() -> list[str]:
        """Get list of missing dependencies for 360° processing."""
        missing = []
        
        if not HAS_OPENCV:
            missing.append("opencv-python")
            
        if not HAS_NUMPY:
            missing.append("numpy")
            
        if not HAS_PY360CONVERT:
            missing.append("py360convert")
            
        if not HAS_EXIFREAD:
            missing.append("exifread")
            
        return missing