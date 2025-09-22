"""AI-enhanced video processor building on existing infrastructure."""

import asyncio
import logging
from pathlib import Path

from ..ai.content_analyzer import ContentAnalysis, VideoContentAnalyzer
from ..config import ProcessorConfig
from .processor import VideoProcessingResult, VideoProcessor

logger = logging.getLogger(__name__)


class EnhancedVideoProcessingResult(VideoProcessingResult):
    """Enhanced processing result with AI analysis."""

    def __init__(
        self,
        content_analysis: ContentAnalysis | None = None,
        smart_thumbnails: list[Path] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.content_analysis = content_analysis
        self.smart_thumbnails = smart_thumbnails or []


class EnhancedVideoProcessor(VideoProcessor):
    """
    AI-enhanced video processor that builds on existing infrastructure.

    Extends the base VideoProcessor with AI-powered content analysis
    while maintaining full backward compatibility.
    """

    def __init__(self, config: ProcessorConfig, enable_ai: bool = True) -> None:
        super().__init__(config)
        self.enable_ai = enable_ai

        if enable_ai:
            self.content_analyzer = VideoContentAnalyzer()
            if not VideoContentAnalyzer.is_analysis_available():
                logger.warning(
                    "AI content analysis partially available. "
                    f"Missing dependencies: {VideoContentAnalyzer.get_missing_dependencies()}"
                )
        else:
            self.content_analyzer = None

    async def process_video_enhanced(
        self,
        input_path: Path,
        video_id: str | None = None,
        enable_smart_thumbnails: bool = True,
    ) -> EnhancedVideoProcessingResult:
        """
        Process video with AI enhancements.

        Args:
            input_path: Path to input video file
            video_id: Optional video ID (generated if not provided)
            enable_smart_thumbnails: Whether to use AI for smart thumbnail selection

        Returns:
            Enhanced processing result with AI analysis
        """
        logger.info(f"Starting enhanced video processing: {input_path}")

        # Run AI content analysis first (if enabled)
        content_analysis = None
        if self.enable_ai and self.content_analyzer:
            try:
                logger.info("Running AI content analysis...")
                content_analysis = await self.content_analyzer.analyze_content(
                    input_path
                )
                logger.info(
                    f"AI analysis complete - scenes: {content_analysis.scenes.scene_count}, "
                    f"quality: {content_analysis.quality_metrics.overall_quality:.2f}, "
                    f"360°: {content_analysis.is_360_video}"
                )
            except Exception as e:
                logger.warning(
                    f"AI content analysis failed, proceeding with standard processing: {e}"
                )

        # Use AI insights to optimize processing configuration
        optimized_config = self._optimize_config_with_ai(content_analysis)

        # Use optimized configuration for processing
        if optimized_config != self.config:
            logger.info("Using AI-optimized processing configuration")
            # Temporarily update encoder with optimized config
            original_config = self.config
            self.config = optimized_config
            self.encoder = self._create_encoder()

        try:
            # Run standard video processing (leverages all existing infrastructure)
            standard_result = await asyncio.to_thread(
                super().process_video, input_path, video_id
            )

            # Generate smart thumbnails if AI analysis available
            smart_thumbnails = []
            if (
                enable_smart_thumbnails
                and content_analysis
                and content_analysis.recommended_thumbnails
            ):
                smart_thumbnails = await self._generate_smart_thumbnails(
                    input_path,
                    standard_result.output_path,
                    content_analysis.recommended_thumbnails,
                    video_id or standard_result.video_id,
                )

            return EnhancedVideoProcessingResult(
                video_id=standard_result.video_id,
                input_path=standard_result.input_path,
                output_path=standard_result.output_path,
                encoded_files=standard_result.encoded_files,
                thumbnails=standard_result.thumbnails,
                sprite_file=standard_result.sprite_file,
                webvtt_file=standard_result.webvtt_file,
                metadata=standard_result.metadata,
                thumbnails_360=standard_result.thumbnails_360,
                sprite_360_files=standard_result.sprite_360_files,
                content_analysis=content_analysis,
                smart_thumbnails=smart_thumbnails,
            )

        finally:
            # Restore original configuration
            if optimized_config != self.config:
                self.config = original_config
                self.encoder = self._create_encoder()

    def _optimize_config_with_ai(
        self, analysis: ContentAnalysis | None
    ) -> ProcessorConfig:
        """
        Optimize processing configuration based on AI analysis.

        Uses content analysis to intelligently adjust processing parameters.
        """
        if not analysis:
            return self.config

        # Create optimized config (copy of original)
        optimized = ProcessorConfig(**self.config.model_dump())

        # Optimize based on 360° detection
        if analysis.is_360_video and hasattr(optimized, "enable_360_processing"):
            if not optimized.enable_360_processing:
                try:
                    logger.info("Enabling 360° processing based on AI detection")
                    optimized.enable_360_processing = True
                except ValueError as e:
                    # 360° dependencies not available
                    logger.warning(f"Cannot enable 360° processing: {e}")
                    pass

        # Optimize quality preset based on video characteristics
        if analysis.quality_metrics.overall_quality < 0.4:
            # Low quality source - use lower preset to save processing time
            if optimized.quality_preset in ["ultra", "high"]:
                logger.info("Reducing quality preset due to low source quality")
                optimized.quality_preset = "medium"

        elif (
            analysis.quality_metrics.overall_quality > 0.8
            and analysis.resolution[0] >= 1920
        ):
            # High quality source - consider upgrading preset
            if optimized.quality_preset == "low":
                logger.info("Upgrading quality preset due to high source quality")
                optimized.quality_preset = "medium"

        # Optimize thumbnail generation based on motion analysis
        if analysis.has_motion and analysis.motion_intensity > 0.7:
            # High motion video - generate more thumbnails
            if len(optimized.thumbnail_timestamps) < 3:
                logger.info("Increasing thumbnail count due to high motion content")
                duration_thirds = [
                    int(analysis.duration * 0.2),
                    int(analysis.duration * 0.5),
                    int(analysis.duration * 0.8),
                ]
                optimized.thumbnail_timestamps = duration_thirds

        # Optimize sprite generation interval
        if optimized.generate_sprites:
            if analysis.motion_intensity > 0.8:
                # High motion - reduce interval for smoother seeking
                optimized.sprite_interval = max(5, optimized.sprite_interval // 2)
            elif analysis.motion_intensity < 0.3:
                # Low motion - increase interval to save space
                optimized.sprite_interval = min(20, optimized.sprite_interval * 2)

        return optimized

    async def _generate_smart_thumbnails(
        self,
        input_path: Path,
        output_dir: Path,
        recommended_timestamps: list[float],
        video_id: str,
    ) -> list[Path]:
        """
        Generate thumbnails at AI-recommended timestamps.

        Uses existing thumbnail generation infrastructure with smart timestamp selection.
        """
        smart_thumbnails = []

        try:
            # Use existing thumbnail generator with smart timestamps
            for i, timestamp in enumerate(recommended_timestamps[:5]):  # Limit to 5
                thumbnail_path = await asyncio.to_thread(
                    self.thumbnail_generator.generate_thumbnail,
                    input_path,
                    output_dir,
                    int(timestamp),
                    f"{video_id}_smart_{i}",
                )
                smart_thumbnails.append(thumbnail_path)

        except Exception as e:
            logger.warning(f"Smart thumbnail generation failed: {e}")

        return smart_thumbnails

    def _create_encoder(self):
        """Create encoder with current configuration."""
        from .encoders import VideoEncoder

        return VideoEncoder(self.config)

    async def analyze_content_only(self, input_path: Path) -> ContentAnalysis | None:
        """
        Run only content analysis without video processing.

        Useful for getting insights before deciding on processing parameters.
        """
        if not self.enable_ai or not self.content_analyzer:
            return None

        return await self.content_analyzer.analyze_content(input_path)

    def get_ai_capabilities(self) -> dict[str, bool]:
        """Get information about available AI capabilities."""
        return {
            "content_analysis": self.enable_ai and self.content_analyzer is not None,
            "scene_detection": self.enable_ai
            and VideoContentAnalyzer.is_analysis_available(),
            "quality_assessment": self.enable_ai
            and VideoContentAnalyzer.is_analysis_available(),
            "motion_detection": self.enable_ai and self.content_analyzer is not None,
            "smart_thumbnails": self.enable_ai and self.content_analyzer is not None,
        }

    def get_missing_ai_dependencies(self) -> list[str]:
        """Get list of missing dependencies for full AI capabilities."""
        if not self.enable_ai:
            return []

        return VideoContentAnalyzer.get_missing_dependencies()

    # Maintain backward compatibility - delegate to parent class
    def process_video(
        self, input_path: Path, video_id: str | None = None
    ) -> VideoProcessingResult:
        """Process video using standard pipeline (backward compatibility)."""
        return super().process_video(input_path, video_id)
