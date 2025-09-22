#!/usr/bin/env python3
"""
Generate synthetic 360° test videos for comprehensive testing.

This module creates synthetic 360° videos with known characteristics for
testing projection conversions, viewport extraction, stereoscopic processing,
and spatial audio functionality.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class Synthetic360Generator:
    """Generate synthetic 360° test videos with controlled characteristics."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create category directories
        self.dirs = {
            "equirectangular": self.output_dir / "equirectangular",
            "cubemap": self.output_dir / "cubemap",
            "stereoscopic": self.output_dir / "stereoscopic",
            "projections": self.output_dir / "projections",
            "spatial_audio": self.output_dir / "spatial_audio",
            "edge_cases": self.output_dir / "edge_cases",
            "motion_tests": self.output_dir / "motion_tests",
            "patterns": self.output_dir / "patterns",
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Generation log
        self.generated_files = []
        self.failed_generations = []

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        dependencies = {
            "ffmpeg": "ffmpeg -version",
            "opencv": 'python -c "import cv2; print(cv2.__version__)"',
            "numpy": 'python -c "import numpy; print(numpy.__version__)"',
        }

        missing = []
        for name, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True)
                if result.returncode != 0:
                    missing.append(name)
            except FileNotFoundError:
                missing.append(name)

        if missing:
            logger.error(f"Missing dependencies: {missing}")
            print(f"⚠️  Missing dependencies: {missing}")
            return False

        return True

    async def generate_all(self):
        """Generate all synthetic 360° test videos."""
        if not self.check_dependencies():
            print("❌ Missing dependencies for synthetic video generation")
            return

        print("🎥 Generating Synthetic 360° Videos...")

        try:
            # Equirectangular projection tests
            await self.generate_equirectangular_tests()

            # Cubemap projection tests
            await self.generate_cubemap_tests()

            # Stereoscopic tests
            await self.generate_stereoscopic_tests()

            # Projection conversion tests
            await self.generate_projection_tests()

            # Spatial audio tests
            await self.generate_spatial_audio_tests()

            # Motion analysis tests
            await self.generate_motion_tests()

            # Edge cases
            await self.generate_360_edge_cases()

            # Test patterns
            await self.generate_pattern_tests()

            # Save generation summary
            self.save_generation_summary()

            print("\n✅ Synthetic 360° generation complete!")
            print(f"   Generated: {len(self.generated_files)} videos")
            print(f"   Failed: {len(self.failed_generations)}")

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            print(f"❌ Generation failed: {e}")

    async def generate_equirectangular_tests(self):
        """Generate equirectangular projection test videos."""
        print("\n📐 Generating Equirectangular Tests...")
        equirect_dir = self.dirs["equirectangular"]

        # Standard equirectangular resolutions
        resolutions = [
            ("2048x1024", "2k_equirect.mp4", 3),
            ("3840x1920", "4k_equirect.mp4", 3),
            ("5760x2880", "6k_equirect.mp4", 2),  # Shorter for large files
            ("7680x3840", "8k_equirect.mp4", 2),
            ("4096x2048", "dci_4k_equirect.mp4", 3),
        ]

        for resolution, filename, duration in resolutions:
            await self.create_equirectangular_pattern(
                equirect_dir / filename, resolution, duration
            )

        # Generate with grid pattern for distortion testing
        await self.create_equirect_grid(equirect_dir / "grid_pattern.mp4")

        # Moving object in 360 space
        await self.create_moving_object_360(equirect_dir / "moving_object.mp4")

        # Latitude/longitude test pattern
        await self.create_lat_lon_pattern(equirect_dir / "lat_lon_test.mp4")

    async def generate_cubemap_tests(self):
        """Generate cubemap projection test videos."""
        print("\n🎲 Generating Cubemap Tests...")
        cubemap_dir = self.dirs["cubemap"]

        # Different cubemap layouts
        layouts = [
            ("3x2", "cubemap_3x2.mp4"),  # YouTube format
            ("6x1", "cubemap_6x1.mp4"),  # Strip format
            ("1x6", "cubemap_1x6.mp4"),  # Vertical strip
            ("2x3", "cubemap_2x3.mp4"),  # Alternative layout
        ]

        for layout, filename in layouts:
            await self.create_cubemap_layout(cubemap_dir / filename, layout)

        # EAC (Equi-Angular Cubemap) for YouTube
        await self.create_eac_video(cubemap_dir / "eac_youtube.mp4")

        # Cubemap with face labels
        await self.create_labeled_cubemap(cubemap_dir / "labeled_faces.mp4")

    async def generate_stereoscopic_tests(self):
        """Generate stereoscopic 360° test videos."""
        print("\n👁️  Generating Stereoscopic Tests...")
        stereo_dir = self.dirs["stereoscopic"]

        # Top-bottom stereo
        await self.create_stereoscopic_video(stereo_dir / "stereo_tb.mp4", "top_bottom")

        # Side-by-side stereo
        await self.create_stereoscopic_video(
            stereo_dir / "stereo_sbs.mp4", "left_right"
        )

        # VR180 (half sphere stereoscopic)
        await self.create_vr180_video(stereo_dir / "vr180.mp4")

        # Stereoscopic with depth variation
        await self.create_depth_test_stereo(stereo_dir / "depth_test.mp4")

    async def generate_projection_tests(self):
        """Generate videos for projection conversion testing."""
        print("\n🔄 Generating Projection Conversion Tests...")
        proj_dir = self.dirs["projections"]

        # Different projection types for conversion testing
        projections = [
            ("fisheye", "fisheye_dual.mp4"),
            ("littleplanet", "little_planet.mp4"),
            ("mercator", "mercator_projection.mp4"),
            ("pannini", "pannini_projection.mp4"),
            ("cylindrical", "cylindrical_projection.mp4"),
        ]

        for proj_type, filename in projections:
            await self.create_projection_test(proj_dir / filename, proj_type)

    async def generate_spatial_audio_tests(self):
        """Generate 360° videos with spatial audio."""
        print("\n🔊 Generating Spatial Audio Tests...")
        audio_dir = self.dirs["spatial_audio"]

        # Ambisonic audio (B-format)
        await self.create_ambisonic_video(audio_dir / "ambisonic_bformat.mp4")

        # Head-locked stereo audio
        await self.create_head_locked_audio(audio_dir / "head_locked_stereo.mp4")

        # Object-based spatial audio
        await self.create_object_audio_360(audio_dir / "object_audio.mp4")

        # Binaural audio test
        await self.create_binaural_360(audio_dir / "binaural_test.mp4")

    async def generate_motion_tests(self):
        """Generate videos for motion analysis testing."""
        print("\n🏃 Generating Motion Analysis Tests...")
        motion_dir = self.dirs["motion_tests"]

        # High motion content
        await self.create_high_motion_360(motion_dir / "high_motion.mp4")

        # Low motion content
        await self.create_low_motion_360(motion_dir / "low_motion.mp4")

        # Rotating camera movement
        await self.create_camera_rotation(motion_dir / "camera_rotation.mp4")

        # Scene transitions
        await self.create_scene_transitions(motion_dir / "scene_transitions.mp4")

    async def generate_360_edge_cases(self):
        """Generate edge case 360° videos."""
        print("\n⚠️  Generating Edge Cases...")
        edge_dir = self.dirs["edge_cases"]

        # Non-standard aspect ratios
        weird_ratios = [
            ("3840x3840", "square_360.mp4"),
            ("1920x1920", "square_360_small.mp4"),
            ("8192x2048", "ultra_wide_360.mp4"),
            ("2048x4096", "ultra_tall_360.mp4"),
        ]

        for resolution, filename in weird_ratios:
            await self.create_unusual_aspect_ratio(edge_dir / filename, resolution)

        # Incomplete sphere (180° video)
        await self.create_180_video(edge_dir / "hemisphere_180.mp4")

        # Tilted/rotated initial view
        await self.create_tilted_view(edge_dir / "tilted_initial_view.mp4")

        # Missing or corrupt metadata
        await self.create_no_metadata_360(edge_dir / "no_metadata_360.mp4")

        # Single frame 360° video
        await self.create_single_frame_360(edge_dir / "single_frame.mp4")

    async def generate_pattern_tests(self):
        """Generate test pattern videos."""
        print("\n📊 Generating Test Patterns...")
        pattern_dir = self.dirs["patterns"]

        # Color test patterns
        await self.create_color_bars_360(pattern_dir / "color_bars.mp4")

        # Resolution test pattern
        await self.create_resolution_test(pattern_dir / "resolution_test.mp4")

        # Geometric test patterns
        await self.create_geometric_patterns(pattern_dir / "geometric_test.mp4")

    # =================================================================
    # Individual video generation methods
    # =================================================================

    async def create_equirectangular_pattern(
        self, output_path: Path, resolution: str, duration: int
    ):
        """Create basic equirectangular pattern using FFmpeg."""
        try:
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={resolution}:duration={duration}:rate=30",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=equirectangular",
                str(output_path),
                "-y",
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self.generated_files.append(str(output_path))
                print(f"  ✓ {output_path.name}")
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                self.failed_generations.append(
                    {"file": str(output_path), "error": stderr.decode()}
                )

        except Exception as e:
            logger.error(f"Error generating {output_path}: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_equirect_grid(self, output_path: Path):
        """Create equirectangular video with latitude/longitude grid using OpenCV."""
        try:
            width, height = 3840, 1920
            fps = 30
            duration = 5

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            temp_path = output_path.with_suffix(".temp.mp4")
            out = cv2.VideoWriter(str(temp_path), fourcc, fps, (width, height))

            for frame_num in range(fps * duration):
                # Create base image
                img = np.zeros((height, width, 3), dtype=np.uint8)
                img.fill(20)  # Dark gray background

                # Draw latitude lines (horizontal)
                for lat in range(-90, 91, 15):
                    y = int((90 - lat) / 180 * height)
                    color = (
                        (0, 255, 0) if lat == 0 else (0, 150, 0)
                    )  # Bright green for equator
                    thickness = 2 if lat == 0 else 1
                    cv2.line(img, (0, y), (width, y), color, thickness)

                    # Add latitude labels
                    label = f"{lat}°"
                    cv2.putText(
                        img,
                        label,
                        (20, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                    )

                # Draw longitude lines (vertical)
                for lon in range(-180, 181, 30):
                    x = int((lon + 180) / 360 * width)
                    color = (
                        (0, 0, 255) if lon == 0 else (0, 0, 150)
                    )  # Bright red for prime meridian
                    thickness = 2 if lon == 0 else 1
                    cv2.line(img, (x, 0), (x, height), color, thickness)

                    # Add longitude labels
                    label = f"{lon}°"
                    cv2.putText(
                        img, label, (x + 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                    )

                # Add animated element
                angle = (frame_num / fps) * 2 * np.pi
                marker_x = int(width / 2 + 200 * np.cos(angle))
                marker_y = int(height / 2 + 100 * np.sin(angle))
                cv2.circle(img, (marker_x, marker_y), 20, (255, 255, 0), -1)

                # Add title
                title = f"360° EQUIRECTANGULAR GRID TEST - Frame {frame_num}"
                cv2.putText(
                    img,
                    title,
                    (width // 2 - 300, height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )

                out.write(img)

            out.release()

            # Add metadata with FFmpeg
            await self.add_spherical_metadata(temp_path, output_path)
            temp_path.unlink()

            self.generated_files.append(str(output_path))
            print(f"  ✓ {output_path.name}")

        except Exception as e:
            logger.error(f"Grid generation failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_moving_object_360(self, output_path: Path):
        """Create 360° video with objects moving through the sphere."""
        try:
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=3840x1920:duration=8:rate=30",
                "-vf",
                "v360=e:e:yaw=t*45:pitch=sin(t*2)*30",  # Animated view
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=equirectangular",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"Moving object generation failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_lat_lon_pattern(self, output_path: Path):
        """Create latitude/longitude test pattern."""
        try:
            # Use drawgrid filter to create precise grid
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:size=3840x1920:duration=4",
                "-vf",
                "drawgrid=w=iw/12:h=ih/6:t=2:c=white@0.5",
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=equirectangular",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"Lat/lon pattern failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_cubemap_layout(self, output_path: Path, layout: str):
        """Create cubemap with specified layout."""
        try:
            cols, rows = map(int, layout.split("x"))
            face_size = 1024
            width = face_size * cols
            height = face_size * rows

            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={width}x{height}:duration=3:rate=30",
                "-vf",
                f"v360=e:c{layout}",
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=cubemap",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"Cubemap {layout} failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_eac_video(self, output_path: Path):
        """Create Equi-Angular Cubemap video."""
        try:
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=3840x1920:duration=3:rate=30",
                "-vf",
                "v360=e:eac",
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=eac",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"EAC generation failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_labeled_cubemap(self, output_path: Path):
        """Create cubemap with labeled faces."""
        try:
            # Create image sequence with face labels using OpenCV
            temp_dir = output_path.parent / "temp_cubemap"
            temp_dir.mkdir(exist_ok=True)

            face_names = ["FRONT", "RIGHT", "BACK", "LEFT", "TOP", "BOTTOM"]
            colors = [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 255, 0),
                (255, 0, 255),
                (0, 255, 255),
            ]

            face_size = 512
            duration = 3
            fps = 30

            for frame_num in range(fps * duration):
                # Create 3x2 cubemap layout
                img = np.zeros((face_size * 2, face_size * 3, 3), dtype=np.uint8)

                # Layout: [LEFT][FRONT][RIGHT]
                #         [BOTTOM][TOP][BACK]
                positions = [
                    (1, 0),  # FRONT
                    (2, 0),  # RIGHT
                    (2, 1),  # BACK
                    (0, 0),  # LEFT
                    (1, 1),  # TOP
                    (0, 1),  # BOTTOM
                ]

                for i, (face_name, color) in enumerate(
                    zip(face_names, colors, strict=False)
                ):
                    col, row = positions[i]
                    x1, y1 = col * face_size, row * face_size
                    x2, y2 = x1 + face_size, y1 + face_size

                    # Fill face with color
                    img[y1:y2, x1:x2] = color

                    # Add face label
                    text_size = cv2.getTextSize(
                        face_name, cv2.FONT_HERSHEY_SIMPLEX, 2, 3
                    )[0]
                    text_x = x1 + (face_size - text_size[0]) // 2
                    text_y = y1 + (face_size + text_size[1]) // 2
                    cv2.putText(
                        img,
                        face_name,
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (255, 255, 255),
                        3,
                    )

                # Save frame
                frame_path = temp_dir / f"frame_{frame_num:04d}.png"
                cv2.imwrite(str(frame_path), img)

            # Convert to video with FFmpeg
            cmd = [
                "ffmpeg",
                "-framerate",
                str(fps),
                "-i",
                str(temp_dir / "frame_%04d.png"),
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=cubemap",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

            # Cleanup temp files
            import shutil

            shutil.rmtree(temp_dir)

        except Exception as e:
            logger.error(f"Labeled cubemap failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_stereoscopic_video(self, output_path: Path, stereo_mode: str):
        """Create stereoscopic 360° video."""
        try:
            if stereo_mode == "top_bottom":
                size = "3840x3840"  # Double height for TB
                metadata_mode = "top_bottom"
            else:  # left_right
                size = "7680x1920"  # Double width for SBS
                metadata_mode = "left_right"

            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={size}:duration=3:rate=30",
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=equirectangular",
                "-metadata",
                f"stereo_mode={metadata_mode}",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"Stereoscopic {stereo_mode} failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_vr180_video(self, output_path: Path):
        """Create VR180 (half-sphere stereoscopic) video."""
        try:
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=3840x3840:duration=3:rate=30",
                "-c:v",
                "libx264",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=half_equirectangular",
                "-metadata",
                "stereo_mode=top_bottom",
                "-metadata",
                "fov_horizontal=180",
                "-metadata",
                "fov_vertical=180",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"VR180 generation failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    async def create_ambisonic_video(self, output_path: Path):
        """Create video with ambisonic B-format audio."""
        try:
            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=3840x1920:duration=5:rate=30",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=5",  # W (omni)
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=550:duration=5",  # X (front-back)
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=660:duration=5",  # Y (left-right)
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=770:duration=5",  # Z (up-down)
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-map",
                "2:a",
                "-map",
                "3:a",
                "-map",
                "4:a",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-metadata",
                "spherical=1",
                "-metadata",
                "projection=equirectangular",
                "-metadata",
                "audio_type=ambisonic",
                "-metadata",
                "audio_channels=4",
                str(output_path),
                "-y",
            ]

            await self.run_ffmpeg_command(cmd, output_path)

        except Exception as e:
            logger.error(f"Ambisonic video failed: {e}")
            self.failed_generations.append({"file": str(output_path), "error": str(e)})

    # =================================================================
    # Utility methods
    # =================================================================

    async def run_ffmpeg_command(self, cmd: list[str], output_path: Path):
        """Run FFmpeg command and handle results."""
        result = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()

        if result.returncode == 0:
            self.generated_files.append(str(output_path))
            print(f"  ✓ {output_path.name}")
        else:
            logger.error(f"FFmpeg failed for {output_path.name}: {stderr.decode()}")
            self.failed_generations.append(
                {"file": str(output_path), "error": stderr.decode()}
            )

    async def add_spherical_metadata(self, input_path: Path, output_path: Path):
        """Add spherical metadata to video file."""
        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c",
            "copy",
            "-metadata",
            "spherical=1",
            "-metadata",
            "projection=equirectangular",
            str(output_path),
            "-y",
        ]

        result = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await result.communicate()

    # Placeholder methods for remaining generators
    async def create_depth_test_stereo(self, output_path: Path):
        """Create stereoscopic video with depth testing."""
        await self.create_stereoscopic_video(output_path, "top_bottom")

    async def create_projection_test(self, output_path: Path, proj_type: str):
        """Create video for projection testing."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=2048x2048:duration=2:rate=30",
            "-c:v",
            "libx264",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_head_locked_audio(self, output_path: Path):
        """Create head-locked stereo audio."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=5:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=5",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-metadata",
            "spherical=1",
            "-metadata",
            "audio_type=head_locked",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_object_audio_360(self, output_path: Path):
        """Create object-based spatial audio."""
        await self.create_head_locked_audio(output_path)  # Simplified

    async def create_binaural_360(self, output_path: Path):
        """Create binaural 360° audio."""
        await self.create_head_locked_audio(output_path)  # Simplified

    async def create_high_motion_360(self, output_path: Path):
        """Create high motion 360° content."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=5:rate=60",
            "-vf",
            "v360=e:e:yaw=t*180:pitch=sin(t*4)*45",  # Fast rotation
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_low_motion_360(self, output_path: Path):
        """Create low motion 360° content."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=8:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_camera_rotation(self, output_path: Path):
        """Create camera rotation test."""
        await self.create_high_motion_360(output_path)  # Simplified

    async def create_scene_transitions(self, output_path: Path):
        """Create scene transition test."""
        await self.create_low_motion_360(output_path)  # Simplified

    async def create_unusual_aspect_ratio(self, output_path: Path, resolution: str):
        """Create video with unusual aspect ratio."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={resolution}:duration=2:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_180_video(self, output_path: Path):
        """Create 180° hemisphere video."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=2048x2048:duration=3:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            "-metadata",
            "projection=half_equirectangular",
            "-metadata",
            "fov_horizontal=180",
            "-metadata",
            "fov_vertical=180",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_tilted_view(self, output_path: Path):
        """Create video with tilted initial view."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=2:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            "-metadata",
            "initial_view_heading_degrees=45",
            "-metadata",
            "initial_view_pitch_degrees=30",
            "-metadata",
            "initial_view_roll_degrees=15",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_no_metadata_360(self, output_path: Path):
        """Create 360° video without metadata."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=2:rate=30",
            "-c:v",
            "libx264",
            str(output_path),
            "-y",  # No metadata
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_single_frame_360(self, output_path: Path):
        """Create single frame 360° video."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x1920:duration=0.1:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_color_bars_360(self, output_path: Path):
        """Create color bars test pattern."""
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "smptebars=size=3840x1920:duration=3:rate=30",
            "-c:v",
            "libx264",
            "-metadata",
            "spherical=1",
            str(output_path),
            "-y",
        ]
        await self.run_ffmpeg_command(cmd, output_path)

    async def create_resolution_test(self, output_path: Path):
        """Create resolution test pattern."""
        await self.create_color_bars_360(output_path)  # Simplified

    async def create_geometric_patterns(self, output_path: Path):
        """Create geometric test patterns."""
        await self.create_color_bars_360(output_path)  # Simplified

    def save_generation_summary(self):
        """Save generation summary to JSON."""
        summary = {
            "timestamp": time.time(),
            "generated": len(self.generated_files),
            "failed": len(self.failed_generations),
            "files": self.generated_files,
            "failures": self.failed_generations,
            "directories": {k: str(v) for k, v in self.dirs.items()},
        }

        summary_file = self.output_dir / "generation_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)


async def main():
    """Generate synthetic 360° test videos."""
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Generate synthetic 360° test videos")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="tests/fixtures/videos/360_synthetic",
        help="Output directory for generated videos",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    output_dir = Path(args.output_dir)
    generator = Synthetic360Generator(output_dir)

    try:
        start_time = time.time()
        await generator.generate_all()
        elapsed = time.time() - start_time

        print(f"\n🎉 Generation completed in {elapsed:.1f} seconds!")
        print(f"   Output directory: {output_dir}")

    except KeyboardInterrupt:
        print("\n⚠️  Generation interrupted by user")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        logger.exception("Generation failed with exception")


if __name__ == "__main__":
    import time

    asyncio.run(main())
