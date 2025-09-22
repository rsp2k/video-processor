# Video Processor Testing Framework

A comprehensive, modern testing framework specifically designed for video processing applications with beautiful HTML reports, quality metrics, and advanced categorization.

## 🎯 Overview

This testing framework provides:

- **Advanced Test Categorization**: Automatic organization by type (unit, integration, performance, 360°, AI, streaming)
- **Quality Metrics Tracking**: Comprehensive scoring system for test quality assessment
- **Beautiful HTML Reports**: Modern, responsive reports with video processing themes
- **Parallel Execution**: Smart parallel test execution with resource management
- **Fixture Library**: Extensive fixtures for video processing scenarios
- **Custom Assertions**: Video-specific assertions for quality, performance, and output validation

## 🚀 Quick Start

### Installation

```bash
# Install with enhanced testing dependencies
uv sync --dev
```

### Running Tests

```bash
# Quick smoke tests (fastest)
make test-smoke
# or
python run_tests.py --smoke

# Unit tests with quality tracking
make test-unit
# or
python run_tests.py --unit

# All tests with comprehensive reporting
make test-all
# or
python run_tests.py --all
```

### Basic Test Example

```python
import pytest

@pytest.mark.unit
def test_video_encoding(enhanced_processor, quality_tracker, video_assert):
    """Test video encoding with quality tracking."""
    # Your test logic here
    result = enhanced_processor.encode_video(input_path, output_path)

    # Record quality metrics
    quality_tracker.record_assertion(result.success, "Encoding completed")
    quality_tracker.record_video_processing(
        input_size_mb=50.0,
        duration=2.5,
        output_quality=8.5
    )

    # Use custom assertions
    video_assert.assert_video_quality(result.quality_score, 7.0)
    video_assert.assert_encoding_performance(result.fps, 10.0)
```

## 📊 Test Categories

### Automatic Categorization

Tests are automatically categorized based on:

- **File Location**: `/unit/`, `/integration/`, etc.
- **Test Names**: Containing keywords like `performance`, `360`, `ai`
- **Markers**: Explicit `@pytest.mark.category` decorators

### Available Categories

| Category | Marker | Description |
|----------|--------|-------------|
| Unit | `@pytest.mark.unit` | Individual component tests |
| Integration | `@pytest.mark.integration` | Cross-component tests |
| Performance | `@pytest.mark.performance` | Benchmark and performance tests |
| Smoke | `@pytest.mark.smoke` | Quick validation tests |
| 360° Video | `@pytest.mark.video_360` | 360° video processing tests |
| AI Analysis | `@pytest.mark.ai_analysis` | AI-powered analysis tests |
| Streaming | `@pytest.mark.streaming` | Adaptive bitrate and streaming tests |

### Running Specific Categories

```bash
# Run only unit tests
python run_tests.py --category unit

# Run multiple categories
python run_tests.py --category unit integration

# Run performance tests with no parallel execution
python run_tests.py --performance --no-parallel

# Run tests with custom markers
python run_tests.py --markers "not slow and not gpu"
```

## 🧪 Fixtures Library

### Enhanced Core Fixtures

```python
def test_with_enhanced_fixtures(
    enhanced_temp_dir,      # Structured temp directory
    video_config,           # Test-optimized processor config
    enhanced_processor,     # Processor with test settings
    quality_tracker        # Quality metrics tracking
):
    # Test implementation
    pass
```

### Video Scenario Fixtures

```python
def test_video_scenarios(test_video_scenarios):
    """Pre-defined video test scenarios."""
    standard_hd = test_video_scenarios["standard_hd"]
    assert standard_hd["resolution"] == "1920x1080"
    assert standard_hd["quality_threshold"] == 8.0
```

### Performance Benchmarks

```python
def test_performance(performance_benchmarks):
    """Performance thresholds for different operations."""
    h264_720p_fps = performance_benchmarks["encoding"]["h264_720p"]
    assert encoding_fps >= h264_720p_fps
```

### Specialized Fixtures

```python
# 360° video processing
def test_360_video(video_360_fixtures):
    equirect = video_360_fixtures["equirectangular"]
    cubemap = video_360_fixtures["cubemap"]

# AI analysis
def test_ai_features(ai_analysis_fixtures):
    scene_detection = ai_analysis_fixtures["scene_detection"]
    object_tracking = ai_analysis_fixtures["object_tracking"]

# Streaming
def test_streaming(streaming_fixtures):
    adaptive = streaming_fixtures["adaptive_streams"]
    live = streaming_fixtures["live_streaming"]
```

## 📈 Quality Metrics

### Automatic Tracking

The framework automatically tracks:

- **Functional Quality**: Assertion pass rates, error handling
- **Performance Quality**: Execution time, memory usage
- **Reliability Quality**: Error frequency, consistency
- **Maintainability Quality**: Test complexity, documentation

### Manual Recording

```python
def test_with_quality_tracking(quality_tracker):
    # Record assertions
    quality_tracker.record_assertion(True, "Basic validation passed")
    quality_tracker.record_assertion(False, "Expected edge case failure")

    # Record warnings and errors
    quality_tracker.record_warning("Non-critical issue detected")
    quality_tracker.record_error("Critical error occurred")

    # Record video processing metrics
    quality_tracker.record_video_processing(
        input_size_mb=50.0,
        duration=2.5,
        output_quality=8.7
    )
```

### Quality Scores

- **0-10 Scale**: All quality metrics use 0-10 scoring
- **Letter Grades**: A+ (9.0+) to F (< 4.0)
- **Weighted Overall**: Combines all metrics with appropriate weights
- **Historical Tracking**: SQLite database for trend analysis

## 🎨 HTML Reports

### Features

- **Video Processing Theme**: Dark terminal aesthetic with video-focused styling
- **Interactive Dashboard**: Filterable results, expandable details
- **Quality Visualization**: Metrics charts and trend graphs
- **Responsive Design**: Works on desktop and mobile
- **Real-time Filtering**: Filter by category, status, or custom criteria

### Report Generation

```bash
# Generate HTML report (default)
python run_tests.py --unit

# Disable HTML report
python run_tests.py --unit --no-html

# Custom report location via environment
export TEST_REPORTS_DIR=/custom/path
python run_tests.py --all
```

### Report Contents

1. **Executive Summary**: Pass rates, duration, quality scores
2. **Quality Metrics**: Detailed breakdown with visualizations
3. **Test Results Table**: Sortable, filterable results
4. **Analytics Charts**: Status distribution, category breakdown, trends
5. **Artifacts**: Links to screenshots, logs, generated files

## 🔧 Custom Assertions

### Video Quality Assertions

```python
def test_video_output(video_assert):
    # Quality threshold testing
    video_assert.assert_video_quality(8.5, min_threshold=7.0)

    # Performance validation
    video_assert.assert_encoding_performance(fps=15.0, min_fps=10.0)

    # File size validation
    video_assert.assert_file_size_reasonable(45.0, max_size_mb=100.0)

    # Duration preservation
    video_assert.assert_duration_preserved(
        input_duration=10.0,
        output_duration=10.1,
        tolerance=0.1
    )
```

## ⚡ Parallel Execution

### Configuration

```bash
# Auto-detect CPU cores
python run_tests.py --unit -n auto

# Specific worker count
python run_tests.py --unit --workers 8

# Disable parallel execution
python run_tests.py --unit --no-parallel
```

### Best Practices

- **Unit Tests**: Safe for parallel execution
- **Integration Tests**: Often need isolation (--no-parallel)
- **Performance Tests**: Require isolation for accurate measurements
- **Resource-Intensive Tests**: Limit workers to prevent resource exhaustion

## 🐳 Docker Integration

### Running in Docker

```bash
# Build test environment
make docker-build

# Run tests in Docker
make docker-test

# Integration tests with Docker
make test-integration
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Video Processor Tests
  run: |
    uv sync --dev
    python run_tests.py --all --no-parallel

- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: test-reports/
```

## 📝 Configuration

### Environment Variables

```bash
# Test execution
TEST_PARALLEL_WORKERS=4          # Number of parallel workers
TEST_TIMEOUT=300                 # Test timeout in seconds
TEST_FAIL_FAST=true             # Stop on first failure

# Reporting
TEST_REPORTS_DIR=./test-reports  # Report output directory
MIN_COVERAGE=80.0               # Minimum coverage percentage

# CI/CD
CI=true                         # Enable CI mode (shorter output)
```

### pyproject.toml Configuration

The framework integrates with your existing `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "-v",
    "--strict-markers",
    "-p", "tests.framework.pytest_plugin",
]

markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests across components",
    "performance: Performance and benchmark tests",
    # ... more markers
]
```

## 🔍 Advanced Usage

### Custom Test Runners

```python
from tests.framework import TestingConfig, HTMLReporter

# Custom configuration
config = TestingConfig(
    parallel_workers=8,
    theme="custom-dark",
    enable_test_history=True
)

# Custom reporter
reporter = HTMLReporter(config)
```

### Integration with Existing Tests

The framework is designed to be backward compatible:

```python
# Existing test - no changes needed
def test_existing_functionality(temp_dir, processor):
    # Your existing test code
    pass

# Enhanced test - use new features
@pytest.mark.unit
def test_with_enhancements(enhanced_processor, quality_tracker):
    # Enhanced test with quality tracking
    pass
```

### Database Tracking

```python
from tests.framework.quality import TestHistoryDatabase

# Query test history
db = TestHistoryDatabase()
history = db.get_test_history("test_encoding", days=30)
trends = db.get_quality_trends(days=30)
```

## 🛠️ Troubleshooting

### Common Issues

**Tests not running with framework**
```bash
# Ensure plugin is loaded
pytest --trace-config | grep "video_processor_plugin"
```

**Import errors**
```bash
# Verify installation
uv sync --dev
python -c "from tests.framework import HTMLReporter; print('OK')"
```

**Reports not generating**
```bash
# Check permissions and paths
ls -la test-reports/
mkdir -p test-reports
```

### Debug Mode

```bash
# Verbose output with debug info
python run_tests.py --unit --verbose

# Show framework configuration
python -c "from tests.framework.config import config; print(config)"
```

## 📚 Examples

See `tests/framework/demo_test.py` for comprehensive examples of all framework features.

## 🤝 Contributing

1. **Add New Fixtures**: Extend `tests/framework/fixtures.py`
2. **Enhance Reports**: Modify `tests/framework/reporters.py`
3. **Custom Assertions**: Add to `VideoAssertions` class
4. **Quality Metrics**: Extend `tests/framework/quality.py`

## 📄 License

Part of the Video Processor project. See main project LICENSE for details.