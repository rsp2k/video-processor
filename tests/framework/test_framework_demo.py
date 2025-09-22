#!/usr/bin/env python3
"""Demo showing the video processing testing framework in action."""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import framework components directly
from tests.framework.config import TestingConfig
from tests.framework.quality import QualityMetricsCalculator
from tests.framework.reporters import HTMLReporter, JSONReporter, TestResult


@pytest.mark.smoke
def test_framework_smoke_demo():
    """Demo smoke test showing framework capabilities."""
    # Create quality tracker
    tracker = QualityMetricsCalculator("framework_smoke_demo")

    # Record some test activity
    tracker.record_assertion(True, "Framework initialization successful")
    tracker.record_assertion(True, "Configuration loaded correctly")
    tracker.record_assertion(True, "Quality tracker working")

    # Test configuration
    config = TestingConfig()
    assert config.project_name == "Video Processor"
    assert config.parallel_workers >= 1

    # Simulate video processing
    tracker.record_video_processing(
        input_size_mb=50.0,
        duration=2.5,
        output_quality=8.7
    )

    print("✅ Framework smoke test completed successfully")


@pytest.mark.unit
def test_enhanced_configuration():
    """Test enhanced configuration capabilities."""
    tracker = QualityMetricsCalculator("enhanced_configuration")

    # Create configuration from environment
    config = TestingConfig.from_env()

    # Test configuration properties
    tracker.record_assertion(config.parallel_workers > 0, "Parallel workers configured")
    tracker.record_assertion(config.timeout_seconds > 0, "Timeout configured")
    tracker.record_assertion(config.reports_dir.exists(), "Reports directory exists")

    # Test pytest args generation
    args = config.get_pytest_args()
    tracker.record_assertion(len(args) > 0, "Pytest args generated")

    # Test coverage args
    coverage_args = config.get_coverage_args()
    tracker.record_assertion("--cov=src/" in coverage_args, "Coverage configured for src/")

    print("✅ Enhanced configuration test completed")


@pytest.mark.unit
def test_quality_scoring():
    """Test quality metrics and scoring system."""
    tracker = QualityMetricsCalculator("quality_scoring_test")

    # Record comprehensive test data
    for i in range(10):
        tracker.record_assertion(True, f"Test assertion {i+1}")

    # Record one expected failure
    tracker.record_assertion(False, "Expected edge case failure for testing")

    # Record a warning
    tracker.record_warning("Non-critical issue detected during testing")

    # Record multiple video processing operations
    for i in range(3):
        tracker.record_video_processing(
            input_size_mb=40.0 + i * 10,
            duration=1.5 + i * 0.5,
            output_quality=8.0 + i * 0.3
        )

    # Finalize and check metrics
    metrics = tracker.finalize()

    # Validate metrics
    assert metrics.test_name == "quality_scoring_test"
    assert metrics.assertions_total == 11
    assert metrics.assertions_passed == 10
    assert metrics.videos_processed == 3
    assert metrics.overall_score > 0

    print(f"✅ Quality scoring test completed - Overall Score: {metrics.overall_score:.1f}/10")
    print(f"   Grade: {metrics.grade}")


@pytest.mark.integration
def test_html_report_generation():
    """Test HTML report generation with video theme."""
    config = TestingConfig()
    reporter = HTMLReporter(config)

    # Create mock test results with quality metrics
    from tests.framework.quality import TestQualityMetrics
    from datetime import datetime

    # Create various test scenarios
    test_scenarios = [
        {
            "name": "test_video_encoding_h264",
            "status": "passed",
            "duration": 2.5,
            "category": "Unit",
            "quality": TestQualityMetrics(
                test_name="test_video_encoding_h264",
                timestamp=datetime.now(),
                duration=2.5,
                success=True,
                functional_score=9.0,
                performance_score=8.5,
                reliability_score=9.2,
                maintainability_score=8.8,
                assertions_passed=15,
                assertions_total=15,
                videos_processed=1,
                encoding_fps=12.0
            )
        },
        {
            "name": "test_360_video_processing",
            "status": "passed",
            "duration": 15.2,
            "category": "360°",
            "quality": TestQualityMetrics(
                test_name="test_360_video_processing",
                timestamp=datetime.now(),
                duration=15.2,
                success=True,
                functional_score=8.7,
                performance_score=7.5,
                reliability_score=8.9,
                maintainability_score=8.2,
                assertions_passed=22,
                assertions_total=25,
                videos_processed=1,
                encoding_fps=3.2
            )
        },
        {
            "name": "test_streaming_integration",
            "status": "failed",
            "duration": 5.8,
            "category": "Integration",
            "error_message": "Streaming endpoint connection timeout after 30s",
            "quality": TestQualityMetrics(
                test_name="test_streaming_integration",
                timestamp=datetime.now(),
                duration=5.8,
                success=False,
                functional_score=4.0,
                performance_score=6.0,
                reliability_score=3.5,
                maintainability_score=7.0,
                assertions_passed=8,
                assertions_total=12,
                error_count=1
            )
        },
        {
            "name": "test_ai_analysis_smoke",
            "status": "skipped",
            "duration": 0.1,
            "category": "AI",
            "error_message": "AI analysis dependencies not available in CI environment"
        }
    ]

    # Add test results to reporter
    for scenario in test_scenarios:
        result = TestResult(
            name=scenario["name"],
            status=scenario["status"],
            duration=scenario["duration"],
            category=scenario["category"],
            error_message=scenario.get("error_message"),
            quality_metrics=scenario.get("quality")
        )
        reporter.add_test_result(result)

    # Generate HTML report
    html_content = reporter.generate_report()

    # Validate report content
    assert "Video Processor Test Report" in html_content
    assert "test_video_encoding_h264" in html_content
    assert "test_360_video_processing" in html_content
    assert "test_streaming_integration" in html_content
    assert "test_ai_analysis_smoke" in html_content

    # Check for video theme elements
    assert "--bg-primary: #0d1117" in html_content  # Dark theme
    assert "video-accent" in html_content  # Video accent color
    assert "Quality Metrics Overview" in html_content
    assert "Test Analytics & Trends" in html_content

    # Save report to temp file for manual inspection
    temp_dir = Path(tempfile.mkdtemp())
    report_path = temp_dir / "demo_report.html"
    with open(report_path, "w") as f:
        f.write(html_content)

    print(f"✅ HTML report generation test completed")
    print(f"   Report saved to: {report_path}")

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.performance
def test_performance_simulation():
    """Simulate performance testing with benchmarks."""
    tracker = QualityMetricsCalculator("performance_simulation")

    # Simulate different encoding scenarios
    encoding_tests = [
        {"codec": "h264", "resolution": "720p", "target_fps": 15.0, "actual_fps": 18.2},
        {"codec": "h264", "resolution": "1080p", "target_fps": 8.0, "actual_fps": 9.5},
        {"codec": "h265", "resolution": "720p", "target_fps": 6.0, "actual_fps": 7.1},
        {"codec": "webm", "resolution": "1080p", "target_fps": 6.0, "actual_fps": 5.8},
    ]

    for test in encoding_tests:
        # Check if performance meets benchmark
        meets_benchmark = test["actual_fps"] >= test["target_fps"]
        tracker.record_assertion(
            meets_benchmark,
            f"{test['codec']} {test['resolution']} encoding performance"
        )

        # Record video processing metrics
        tracker.record_video_processing(
            input_size_mb=60.0 if "1080p" in test["resolution"] else 30.0,
            duration=2.0,
            output_quality=8.0 + (test["actual_fps"] / test["target_fps"])
        )

    metrics = tracker.finalize()
    print(f"✅ Performance simulation completed - Score: {metrics.overall_score:.1f}/10")


if __name__ == "__main__":
    # Run tests using pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))