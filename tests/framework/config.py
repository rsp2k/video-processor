"""Testing framework configuration management."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class TestCategory(Enum):
    """Test category classifications."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SMOKE = "smoke"
    REGRESSION = "regression"
    E2E = "e2e"
    VIDEO_360 = "360"
    AI_ANALYSIS = "ai"
    STREAMING = "streaming"


class ReportFormat(Enum):
    """Available report formats."""
    HTML = "html"
    JSON = "json"
    CONSOLE = "console"
    JUNIT = "junit"


@dataclass
class TestingConfig:
    """Configuration for the video processor testing framework."""

    # Core settings
    project_name: str = "Video Processor"
    version: str = "1.0.0"

    # Test execution
    parallel_workers: int = 4
    timeout_seconds: int = 300
    retry_failed_tests: int = 1
    fail_fast: bool = False

    # Test categories
    enabled_categories: Set[TestCategory] = field(default_factory=lambda: {
        TestCategory.UNIT,
        TestCategory.INTEGRATION,
        TestCategory.SMOKE
    })

    # Report generation
    report_formats: Set[ReportFormat] = field(default_factory=lambda: {
        ReportFormat.HTML,
        ReportFormat.JSON
    })

    # Paths
    reports_dir: Path = field(default_factory=lambda: Path("test-reports"))
    artifacts_dir: Path = field(default_factory=lambda: Path("test-artifacts"))
    temp_dir: Path = field(default_factory=lambda: Path("temp-test-files"))

    # Video processing specific
    video_fixtures_dir: Path = field(default_factory=lambda: Path("tests/fixtures/videos"))
    ffmpeg_timeout: int = 60
    max_video_size_mb: int = 100
    supported_codecs: Set[str] = field(default_factory=lambda: {
        "h264", "h265", "vp9", "av1"
    })

    # Quality thresholds
    min_test_coverage: float = 80.0
    min_performance_score: float = 7.0
    max_memory_usage_mb: float = 512.0

    # Theme and styling
    theme: str = "video-dark"
    color_scheme: str = "terminal"

    # Database tracking
    enable_test_history: bool = True
    database_path: Path = field(default_factory=lambda: Path("test-history.db"))

    # CI/CD integration
    ci_mode: bool = field(default_factory=lambda: bool(os.getenv("CI")))
    upload_artifacts: bool = False
    artifact_retention_days: int = 30

    def __post_init__(self):
        """Ensure directories exist and validate configuration."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Validate thresholds
        if not 0 <= self.min_test_coverage <= 100:
            raise ValueError("min_test_coverage must be between 0 and 100")

        if self.parallel_workers < 1:
            raise ValueError("parallel_workers must be at least 1")

    @classmethod
    def from_env(cls) -> "TestingConfig":
        """Create configuration from environment variables."""
        return cls(
            parallel_workers=int(os.getenv("TEST_PARALLEL_WORKERS", "4")),
            timeout_seconds=int(os.getenv("TEST_TIMEOUT", "300")),
            ci_mode=bool(os.getenv("CI")),
            fail_fast=bool(os.getenv("TEST_FAIL_FAST")),
            reports_dir=Path(os.getenv("TEST_REPORTS_DIR", "test-reports")),
            min_test_coverage=float(os.getenv("MIN_COVERAGE", "80.0")),
        )

    def get_pytest_args(self) -> List[str]:
        """Generate pytest command line arguments from config."""
        args = [
            f"--maxfail={1 if self.fail_fast else 0}",
            f"--timeout={self.timeout_seconds}",
        ]

        if self.parallel_workers > 1:
            args.extend(["-n", str(self.parallel_workers)])

        if self.ci_mode:
            args.extend(["--tb=short", "--no-header"])
        else:
            args.extend(["--tb=long", "-v"])

        return args

    def get_coverage_args(self) -> List[str]:
        """Generate coverage arguments for pytest."""
        return [
            "--cov=src/",
            f"--cov-fail-under={self.min_test_coverage}",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=json",
        ]


# Global configuration instance
config = TestingConfig.from_env()