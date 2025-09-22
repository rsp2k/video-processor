"""Custom pytest plugin for video processing test framework."""

import pytest
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import TestingConfig, TestCategory
from .quality import QualityMetricsCalculator, TestHistoryDatabase
from .reporters import HTMLReporter, JSONReporter, ConsoleReporter, TestResult


class VideoProcessorTestPlugin:
    """Main pytest plugin for video processor testing framework."""

    def __init__(self):
        self.config = TestingConfig.from_env()
        self.html_reporter = HTMLReporter(self.config)
        self.json_reporter = JSONReporter(self.config)
        self.console_reporter = ConsoleReporter(self.config)
        self.quality_db = TestHistoryDatabase(self.config.database_path)

        # Test session tracking
        self.session_start_time = 0
        self.test_metrics: Dict[str, QualityMetricsCalculator] = {}

    def pytest_configure(self, config):
        """Configure pytest with custom markers and settings."""
        # Register custom markers
        config.addinivalue_line("markers", "unit: Unit tests")
        config.addinivalue_line("markers", "integration: Integration tests")
        config.addinivalue_line("markers", "performance: Performance tests")
        config.addinivalue_line("markers", "smoke: Smoke tests")
        config.addinivalue_line("markers", "regression: Regression tests")
        config.addinivalue_line("markers", "e2e: End-to-end tests")
        config.addinivalue_line("markers", "video_360: 360° video processing tests")
        config.addinivalue_line("markers", "ai_analysis: AI-powered analysis tests")
        config.addinivalue_line("markers", "streaming: Streaming/adaptive bitrate tests")
        config.addinivalue_line("markers", "requires_ffmpeg: Tests requiring FFmpeg")
        config.addinivalue_line("markers", "requires_gpu: Tests requiring GPU acceleration")
        config.addinivalue_line("markers", "slow: Slow-running tests")
        config.addinivalue_line("markers", "memory_intensive: Memory-intensive tests")
        config.addinivalue_line("markers", "cpu_intensive: CPU-intensive tests")

    def pytest_sessionstart(self, session):
        """Called at the start of test session."""
        self.session_start_time = time.time()
        print(f"\n🎬 Starting Video Processor Test Suite")
        print(f"Configuration: {self.config.parallel_workers} parallel workers")
        print(f"Reports will be saved to: {self.config.reports_dir}")

    def pytest_sessionfinish(self, session, exitstatus):
        """Called at the end of test session."""
        session_duration = time.time() - self.session_start_time

        # Generate reports
        html_path = self.html_reporter.save_report()
        json_path = self.json_reporter.save_report()

        # Console summary
        self.console_reporter.print_summary()

        # Print report locations
        print(f"📊 HTML Report: {html_path}")
        print(f"📋 JSON Report: {json_path}")

        # Quality summary
        if self.html_reporter.test_results:
            avg_quality = self.html_reporter._calculate_average_quality()
            print(f"🏆 Overall Quality Score: {avg_quality['overall']:.1f}/10")

        print(f"⏱️  Total Session Duration: {session_duration:.2f}s")

    def pytest_runtest_setup(self, item):
        """Called before each test runs."""
        test_name = f"{item.parent.name}::{item.name}"
        self.test_metrics[test_name] = QualityMetricsCalculator(test_name)

        # Add quality tracker to test item
        item.quality_tracker = self.test_metrics[test_name]

    def pytest_runtest_call(self, item):
        """Called during test execution."""
        # This is where the actual test runs
        # The quality tracker will be used by fixtures
        pass

    def pytest_runtest_teardown(self, item):
        """Called after each test completes."""
        test_name = f"{item.parent.name}::{item.name}"

        if test_name in self.test_metrics:
            # Finalize quality metrics
            quality_metrics = self.test_metrics[test_name].finalize()

            # Save to database if enabled
            if self.config.enable_test_history:
                self.quality_db.save_metrics(quality_metrics)

            # Store in test item for reporting
            item.quality_metrics = quality_metrics

    def pytest_runtest_logreport(self, report):
        """Called when test result is available."""
        if report.when != "call":
            return

        # Determine test category from markers
        category = self._get_test_category(report.nodeid, getattr(report, 'keywords', {}))

        # Create test result
        test_result = TestResult(
            name=report.nodeid,
            status=self._get_test_status(report),
            duration=report.duration,
            category=category,
            error_message=self._get_error_message(report),
            artifacts=self._get_test_artifacts(report),
            quality_metrics=getattr(report, 'quality_metrics', None)
        )

        # Add to reporters
        self.html_reporter.add_test_result(test_result)
        self.json_reporter.add_test_result(test_result)
        self.console_reporter.add_test_result(test_result)

    def _get_test_category(self, nodeid: str, keywords: Dict[str, Any]) -> str:
        """Determine test category from path and markers."""
        # Check markers first
        marker_to_category = {
            'unit': 'Unit',
            'integration': 'Integration',
            'performance': 'Performance',
            'smoke': 'Smoke',
            'regression': 'Regression',
            'e2e': 'E2E',
            'video_360': '360°',
            'ai_analysis': 'AI',
            'streaming': 'Streaming'
        }

        for marker, category in marker_to_category.items():
            if marker in keywords:
                return category

        # Fallback to path-based detection
        if '/unit/' in nodeid:
            return 'Unit'
        elif '/integration/' in nodeid:
            return 'Integration'
        elif 'performance' in nodeid.lower():
            return 'Performance'
        elif '360' in nodeid:
            return '360°'
        elif 'ai' in nodeid.lower():
            return 'AI'
        elif 'stream' in nodeid.lower():
            return 'Streaming'
        else:
            return 'Other'

    def _get_test_status(self, report) -> str:
        """Get test status from report."""
        if report.passed:
            return "passed"
        elif report.failed:
            return "failed"
        elif report.skipped:
            return "skipped"
        else:
            return "error"

    def _get_error_message(self, report) -> Optional[str]:
        """Extract error message from report."""
        if hasattr(report, 'longrepr') and report.longrepr:
            return str(report.longrepr)[:500]  # Truncate long messages
        return None

    def _get_test_artifacts(self, report) -> List[str]:
        """Get test artifacts (screenshots, videos, etc.)."""
        artifacts = []

        # Look for common artifact patterns
        test_name = report.nodeid.replace("::", "_").replace("/", "_")
        artifacts_dir = self.config.artifacts_dir

        for pattern in ["*.png", "*.jpg", "*.mp4", "*.webm", "*.log"]:
            for artifact in artifacts_dir.glob(f"{test_name}*{pattern[1:]}"):
                artifacts.append(str(artifact.relative_to(artifacts_dir)))

        return artifacts


# Fixtures that integrate with the plugin
@pytest.fixture
def quality_tracker(request):
    """Fixture to access the quality tracker for current test."""
    return getattr(request.node, 'quality_tracker', None)


@pytest.fixture
def test_artifacts_dir(request):
    """Fixture providing test-specific artifacts directory."""
    config = TestingConfig.from_env()
    test_name = request.node.name.replace("::", "_").replace("/", "_")
    artifacts_dir = config.artifacts_dir / test_name
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


@pytest.fixture
def video_test_config():
    """Fixture providing video test configuration."""
    return TestingConfig.from_env()


# Pytest collection hooks for smart test discovery
def pytest_collection_modifyitems(config, items):
    """Modify collected test items for better organization."""
    # Auto-add markers based on test location
    for item in items:
        # Add markers based on file path
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add performance marker for tests with 'performance' in name
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)

        # Add slow marker for integration tests
        if item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.slow)

        # Add video processing specific markers
        if "360" in item.name:
            item.add_marker(pytest.mark.video_360)

        if "ai" in item.name.lower() or "analysis" in item.name.lower():
            item.add_marker(pytest.mark.ai_analysis)

        if "stream" in item.name.lower():
            item.add_marker(pytest.mark.streaming)

        # Add requirement markers based on test content (simplified)
        if "ffmpeg" in item.name.lower():
            item.add_marker(pytest.mark.requires_ffmpeg)


# Performance tracking hooks
def pytest_runtest_protocol(item, nextitem):
    """Track test performance and resource usage."""
    # This could be extended to track memory/CPU usage during tests
    return None


# Custom assertions for video processing
class VideoAssertions:
    """Custom assertions for video processing tests."""

    @staticmethod
    def assert_video_quality(quality_score: float, min_threshold: float = 7.0):
        """Assert video quality meets minimum threshold."""
        assert quality_score >= min_threshold, f"Video quality {quality_score} below threshold {min_threshold}"

    @staticmethod
    def assert_encoding_performance(fps: float, min_fps: float = 1.0):
        """Assert encoding performance meets minimum FPS."""
        assert fps >= min_fps, f"Encoding FPS {fps} below minimum {min_fps}"

    @staticmethod
    def assert_file_size_reasonable(file_size_mb: float, max_size_mb: float = 100.0):
        """Assert output file size is reasonable."""
        assert file_size_mb <= max_size_mb, f"File size {file_size_mb}MB exceeds maximum {max_size_mb}MB"

    @staticmethod
    def assert_duration_preserved(input_duration: float, output_duration: float, tolerance: float = 0.1):
        """Assert video duration is preserved within tolerance."""
        diff = abs(input_duration - output_duration)
        assert diff <= tolerance, f"Duration difference {diff}s exceeds tolerance {tolerance}s"


# Make custom assertions available as fixture
@pytest.fixture
def video_assert():
    """Fixture providing video-specific assertions."""
    return VideoAssertions()


# Plugin registration
def pytest_configure(config):
    """Register the plugin."""
    if not hasattr(config, '_video_processor_plugin'):
        config._video_processor_plugin = VideoProcessorTestPlugin()
        config.pluginmanager.register(config._video_processor_plugin, "video_processor_plugin")


# Export key components
__all__ = [
    "VideoProcessorTestPlugin",
    "quality_tracker",
    "test_artifacts_dir",
    "video_test_config",
    "video_assert",
    "VideoAssertions"
]