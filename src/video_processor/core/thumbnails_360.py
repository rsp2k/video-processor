"""360° video thumbnail generation with projection support."""

import math
from pathlib import Path
from typing import Literal

import ffmpeg

from ..config import ProcessorConfig
from ..exceptions import EncodingError, FFmpegError

# Optional dependency handling
try:
    import cv2
    import numpy as np

    from ..utils.video_360 import HAS_360_SUPPORT, ProjectionType, Video360Utils
except ImportError:
    # Fallback types when dependencies not available
    ProjectionType = str
    HAS_360_SUPPORT = False

ViewingAngle = Literal["front", "back", "left", "right", "up", "down", "stereographic"]


class Thumbnail360Generator:
    """Handles 360° video thumbnail generation with various projections."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

        if not HAS_360_SUPPORT:
            raise ImportError(
                "360° thumbnail generation requires optional dependencies. "
                "Install with: uv add 'video-processor[video-360]'"
            )

    def generate_360_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        timestamp: int,
        video_id: str,
        projection_type: ProjectionType = "equirectangular",
        viewing_angles: list[ViewingAngle] | None = None,
    ) -> dict[str, Path]:
        """
        Generate 360° thumbnails for different viewing angles.

        Args:
            video_path: Path to 360° video file
            output_dir: Output directory
            timestamp: Time in seconds to extract thumbnail
            video_id: Unique video identifier
            projection_type: Type of 360° projection
            viewing_angles: List of viewing angles to generate

        Returns:
            Dictionary mapping viewing angles to thumbnail paths
        """
        if viewing_angles is None:
            viewing_angles = self.config.thumbnail_360_projections

        thumbnails = {}

        # First extract a full equirectangular frame
        equirect_frame = self._extract_equirectangular_frame(
            video_path, timestamp, output_dir, video_id
        )

        try:
            # Load the equirectangular image
            equirect_img = cv2.imread(str(equirect_frame))
            if equirect_img is None:
                raise EncodingError(f"Failed to load equirectangular frame: {equirect_frame}")

            # Generate thumbnails for each viewing angle
            for angle in viewing_angles:
                thumbnail_path = self._generate_angle_thumbnail(
                    equirect_img, angle, output_dir, video_id, timestamp
                )
                thumbnails[angle] = thumbnail_path

        finally:
            # Clean up temporary equirectangular frame
            if equirect_frame.exists():
                equirect_frame.unlink()

        return thumbnails

    def _extract_equirectangular_frame(
        self, video_path: Path, timestamp: int, output_dir: Path, video_id: str
    ) -> Path:
        """Extract a full equirectangular frame from the 360° video."""
        temp_frame = output_dir / f"{video_id}_temp_equirect_{timestamp}.jpg"

        try:
            # Get video info
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(
                stream for stream in probe["streams"]
                if stream["codec_type"] == "video"
            )

            width = video_stream["width"]
            height = video_stream["height"]
            duration = float(video_stream.get("duration", 0))

            # Adjust timestamp if beyond video duration
            if timestamp >= duration:
                timestamp = max(1, int(duration // 2))

            # Extract full resolution frame
            (
                ffmpeg.input(str(video_path), ss=timestamp)
                .filter("scale", width, height)
                .output(str(temp_frame), vframes=1, q=2)  # High quality
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            raise FFmpegError(f"Frame extraction failed: {error_msg}") from e

        if not temp_frame.exists():
            raise EncodingError("Frame extraction failed - output file not created")

        return temp_frame

    def _generate_angle_thumbnail(
        self,
        equirect_img: "np.ndarray",
        viewing_angle: ViewingAngle,
        output_dir: Path,
        video_id: str,
        timestamp: int,
    ) -> Path:
        """Generate thumbnail for a specific viewing angle."""
        output_path = output_dir / f"{video_id}_360_{viewing_angle}_{timestamp}.jpg"

        if viewing_angle == "stereographic":
            # Generate "little planet" stereographic projection
            thumbnail = self._create_stereographic_projection(equirect_img)
        else:
            # Generate perspective projection for the viewing angle
            thumbnail = self._create_perspective_projection(equirect_img, viewing_angle)

        # Save thumbnail
        cv2.imwrite(str(output_path), thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return output_path

    def _create_perspective_projection(
        self, equirect_img: "np.ndarray", viewing_angle: ViewingAngle
    ) -> "np.ndarray":
        """Create perspective projection for a viewing angle."""
        height, width = equirect_img.shape[:2]

        # Define viewing directions (yaw, pitch) in radians
        viewing_directions = {
            "front": (0, 0),
            "back": (math.pi, 0),
            "left": (-math.pi/2, 0),
            "right": (math.pi/2, 0),
            "up": (0, math.pi/2),
            "down": (0, -math.pi/2),
        }

        if viewing_angle not in viewing_directions:
            viewing_angle = "front"

        yaw, pitch = viewing_directions[viewing_angle]

        # Generate perspective view
        thumbnail_size = self.config.thumbnail_width
        fov = math.pi / 3  # 60 degrees field of view

        # Create coordinate maps for perspective projection
        u_map, v_map = self._create_perspective_maps(
            thumbnail_size, thumbnail_size, fov, yaw, pitch, width, height
        )

        # Apply remapping
        thumbnail = cv2.remap(equirect_img, u_map, v_map, cv2.INTER_LINEAR)

        return thumbnail

    def _create_stereographic_projection(self, equirect_img: "np.ndarray") -> "np.ndarray":
        """Create stereographic 'little planet' projection."""
        height, width = equirect_img.shape[:2]

        # Output size for stereographic projection
        output_size = self.config.thumbnail_width

        # Create coordinate maps for stereographic projection
        y_coords, x_coords = np.mgrid[0:output_size, 0:output_size]

        # Convert to centered coordinates
        x_centered = (x_coords - output_size // 2) / (output_size // 2)
        y_centered = (y_coords - output_size // 2) / (output_size // 2)

        # Calculate distance from center
        r = np.sqrt(x_centered**2 + y_centered**2)

        # Create mask for circular boundary
        mask = r <= 1.0

        # Convert to spherical coordinates for stereographic projection
        theta = np.arctan2(y_centered, x_centered)
        phi = 2 * np.arctan(r)

        # Convert to equirectangular coordinates
        u = (theta + np.pi) / (2 * np.pi) * width
        v = (np.pi/2 - phi) / np.pi * height

        # Clamp coordinates
        u = np.clip(u, 0, width - 1)
        v = np.clip(v, 0, height - 1)

        # Create maps for remapping
        u_map = u.astype(np.float32)
        v_map = v.astype(np.float32)

        # Apply remapping
        thumbnail = cv2.remap(equirect_img, u_map, v_map, cv2.INTER_LINEAR)

        # Apply circular mask
        thumbnail[~mask] = [0, 0, 0]  # Black background

        return thumbnail

    def _create_perspective_maps(
        self,
        out_width: int,
        out_height: int,
        fov: float,
        yaw: float,
        pitch: float,
        equirect_width: int,
        equirect_height: int,
    ) -> tuple["np.ndarray", "np.ndarray"]:
        """Create coordinate mapping for perspective projection."""
        # Create output coordinate grids
        y_coords, x_coords = np.mgrid[0:out_height, 0:out_width]

        # Convert to normalized device coordinates [-1, 1]
        x_ndc = (x_coords - out_width / 2) / (out_width / 2)
        y_ndc = (y_coords - out_height / 2) / (out_height / 2)

        # Apply perspective projection
        focal_length = 1.0 / math.tan(fov / 2)

        # Create 3D ray directions
        x_3d = x_ndc / focal_length
        y_3d = y_ndc / focal_length
        z_3d = np.ones_like(x_3d)

        # Normalize ray directions
        ray_length = np.sqrt(x_3d**2 + y_3d**2 + z_3d**2)
        x_3d /= ray_length
        y_3d /= ray_length
        z_3d /= ray_length

        # Apply rotation for viewing direction
        # Rotate by yaw (around Y axis)
        cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
        x_rot = x_3d * cos_yaw - z_3d * sin_yaw
        z_rot = x_3d * sin_yaw + z_3d * cos_yaw

        # Rotate by pitch (around X axis)
        cos_pitch, sin_pitch = math.cos(pitch), math.sin(pitch)
        y_rot = y_3d * cos_pitch - z_rot * sin_pitch
        z_final = y_3d * sin_pitch + z_rot * cos_pitch

        # Convert 3D coordinates to spherical
        theta = np.arctan2(x_rot, z_final)
        phi = np.arcsin(np.clip(y_rot, -1, 1))

        # Convert spherical to equirectangular coordinates
        u = (theta + np.pi) / (2 * np.pi) * equirect_width
        v = (np.pi/2 - phi) / np.pi * equirect_height

        # Clamp to image boundaries
        u = np.clip(u, 0, equirect_width - 1)
        v = np.clip(v, 0, equirect_height - 1)

        return u.astype(np.float32), v.astype(np.float32)

    def generate_360_sprite_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        video_id: str,
        projection_type: ProjectionType = "equirectangular",
        viewing_angle: ViewingAngle = "front",
    ) -> tuple[Path, Path]:
        """
        Generate 360° sprite sheet for a specific viewing angle.
        
        Args:
            video_path: Path to 360° video file
            output_dir: Output directory
            video_id: Unique video identifier
            projection_type: Type of 360° projection
            viewing_angle: Viewing angle for sprite generation
            
        Returns:
            Tuple of (sprite_file_path, webvtt_file_path)
        """
        sprite_file = output_dir / f"{video_id}_360_{viewing_angle}_sprite.jpg"
        webvtt_file = output_dir / f"{video_id}_360_{viewing_angle}_sprite.webvtt"
        frames_dir = output_dir / "frames_360"

        # Create frames directory
        frames_dir.mkdir(exist_ok=True)

        try:
            # Get video duration
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe["format"]["duration"])

            # Generate frames at specified intervals
            interval = self.config.sprite_interval
            timestamps = list(range(0, int(duration), interval))

            frame_paths = []
            for i, timestamp in enumerate(timestamps):
                # Generate 360° thumbnail for this timestamp
                thumbnails = self.generate_360_thumbnails(
                    video_path, frames_dir, timestamp, f"{video_id}_frame_{i}",
                    projection_type, [viewing_angle]
                )

                if viewing_angle in thumbnails:
                    frame_paths.append(thumbnails[viewing_angle])

            # Create sprite sheet from frames
            if frame_paths:
                self._create_sprite_sheet(frame_paths, sprite_file, timestamps, webvtt_file)

            return sprite_file, webvtt_file

        finally:
            # Clean up frame files
            if frames_dir.exists():
                for frame_file in frames_dir.glob("*"):
                    if frame_file.is_file():
                        frame_file.unlink()
                frames_dir.rmdir()

    def _create_sprite_sheet(
        self,
        frame_paths: list[Path],
        sprite_file: Path,
        timestamps: list[int],
        webvtt_file: Path,
    ) -> None:
        """Create sprite sheet from individual frames."""
        if not frame_paths:
            raise EncodingError("No frames available for sprite sheet creation")

        # Load first frame to get dimensions
        first_frame = cv2.imread(str(frame_paths[0]))
        if first_frame is None:
            raise EncodingError(f"Failed to load first frame: {frame_paths[0]}")

        frame_height, frame_width = first_frame.shape[:2]

        # Calculate sprite sheet layout
        cols = 10  # 10 thumbnails per row
        rows = math.ceil(len(frame_paths) / cols)

        sprite_width = cols * frame_width
        sprite_height = rows * frame_height

        # Create sprite sheet
        sprite_img = np.zeros((sprite_height, sprite_width, 3), dtype=np.uint8)

        # Create WebVTT content
        webvtt_content = ["WEBVTT", ""]

        # Place frames in sprite sheet and create WebVTT entries
        for i, (frame_path, timestamp) in enumerate(zip(frame_paths, timestamps, strict=False)):
            frame = cv2.imread(str(frame_path))
            if frame is None:
                continue

            # Calculate position in sprite
            col = i % cols
            row = i // cols

            x_start = col * frame_width
            y_start = row * frame_height
            x_end = x_start + frame_width
            y_end = y_start + frame_height

            # Place frame in sprite
            sprite_img[y_start:y_end, x_start:x_end] = frame

            # Create WebVTT entry
            start_time = f"{timestamp//3600:02d}:{(timestamp%3600)//60:02d}:{timestamp%60:02d}.000"
            end_time = f"{(timestamp+1)//3600:02d}:{((timestamp+1)%3600)//60:02d}:{(timestamp+1)%60:02d}.000"

            webvtt_content.extend([
                f"{start_time} --> {end_time}",
                f"{sprite_file.name}#xywh={x_start},{y_start},{frame_width},{frame_height}",
                ""
            ])

        # Save sprite sheet
        cv2.imwrite(str(sprite_file), sprite_img, [cv2.IMWRITE_JPEG_QUALITY, 85])

        # Save WebVTT file
        with open(webvtt_file, 'w') as f:
            f.write('\n'.join(webvtt_content))
