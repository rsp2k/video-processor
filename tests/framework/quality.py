"""Quality metrics calculation and assessment for video processing tests."""

import time
import psutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timedelta


@dataclass
class QualityScore:
    """Individual quality score component."""
    name: str
    score: float  # 0-10 scale
    weight: float  # 0-1 scale
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestQualityMetrics:
    """Comprehensive quality metrics for a test run."""
    test_name: str
    timestamp: datetime
    duration: float
    success: bool

    # Individual scores
    functional_score: float = 0.0
    performance_score: float = 0.0
    reliability_score: float = 0.0
    maintainability_score: float = 0.0

    # Resource usage
    peak_memory_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_io_mb: float = 0.0

    # Test-specific metrics
    assertions_passed: int = 0
    assertions_total: int = 0
    error_count: int = 0
    warning_count: int = 0

    # Video processing specific
    videos_processed: int = 0
    encoding_fps: float = 0.0
    output_quality_score: float = 0.0

    @property
    def overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        scores = [
            QualityScore("Functional", self.functional_score, 0.40),
            QualityScore("Performance", self.performance_score, 0.25),
            QualityScore("Reliability", self.reliability_score, 0.20),
            QualityScore("Maintainability", self.maintainability_score, 0.15),
        ]

        weighted_sum = sum(score.score * score.weight for score in scores)
        return min(10.0, max(0.0, weighted_sum))

    @property
    def grade(self) -> str:
        """Get letter grade based on overall score."""
        score = self.overall_score
        if score >= 9.0:
            return "A+"
        elif score >= 8.5:
            return "A"
        elif score >= 8.0:
            return "A-"
        elif score >= 7.5:
            return "B+"
        elif score >= 7.0:
            return "B"
        elif score >= 6.5:
            return "B-"
        elif score >= 6.0:
            return "C+"
        elif score >= 5.5:
            return "C"
        elif score >= 5.0:
            return "C-"
        elif score >= 4.0:
            return "D"
        else:
            return "F"


class QualityMetricsCalculator:
    """Calculate comprehensive quality metrics for test runs."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used / 1024 / 1024
        self.process = psutil.Process()

        # Tracking data
        self.assertions_passed = 0
        self.assertions_total = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.videos_processed = 0
        self.encoding_metrics: List[Dict[str, float]] = []

    def record_assertion(self, passed: bool, message: str = ""):
        """Record a test assertion result."""
        self.assertions_total += 1
        if passed:
            self.assertions_passed += 1
        else:
            self.errors.append(f"Assertion failed: {message}")

    def record_error(self, error: str):
        """Record an error occurrence."""
        self.errors.append(error)

    def record_warning(self, warning: str):
        """Record a warning."""
        self.warnings.append(warning)

    def record_video_processing(self, input_size_mb: float, duration: float, output_quality: float = 8.0):
        """Record video processing metrics."""
        self.videos_processed += 1
        encoding_fps = input_size_mb / max(duration, 0.001)  # Avoid division by zero
        self.encoding_metrics.append({
            "input_size_mb": input_size_mb,
            "duration": duration,
            "encoding_fps": encoding_fps,
            "output_quality": output_quality
        })

    def calculate_functional_score(self) -> float:
        """Calculate functional quality score (0-10)."""
        if self.assertions_total == 0:
            return 0.0

        # Base score from assertion pass rate
        pass_rate = self.assertions_passed / self.assertions_total
        base_score = pass_rate * 10

        # Bonus for comprehensive testing
        if self.assertions_total >= 20:
            base_score = min(10.0, base_score + 0.5)
        elif self.assertions_total >= 10:
            base_score = min(10.0, base_score + 0.25)

        # Penalty for errors
        error_penalty = min(3.0, len(self.errors) * 0.5)
        final_score = max(0.0, base_score - error_penalty)

        return final_score

    def calculate_performance_score(self) -> float:
        """Calculate performance quality score (0-10)."""
        duration = time.time() - self.start_time
        current_memory = psutil.virtual_memory().used / 1024 / 1024
        memory_usage = current_memory - self.start_memory

        # Base score starts at 10
        score = 10.0

        # Duration penalty (tests should be fast)
        if duration > 30:  # 30 seconds
            score -= min(3.0, (duration - 30) / 10)

        # Memory usage penalty
        if memory_usage > 100:  # 100MB
            score -= min(2.0, (memory_usage - 100) / 100)

        # Bonus for video processing efficiency
        if self.encoding_metrics:
            avg_fps = sum(m["encoding_fps"] for m in self.encoding_metrics) / len(self.encoding_metrics)
            if avg_fps > 10:  # Good encoding speed
                score = min(10.0, score + 0.5)

        return max(0.0, score)

    def calculate_reliability_score(self) -> float:
        """Calculate reliability quality score (0-10)."""
        score = 10.0

        # Error penalty
        error_penalty = min(5.0, len(self.errors) * 1.0)
        score -= error_penalty

        # Warning penalty (less severe)
        warning_penalty = min(2.0, len(self.warnings) * 0.2)
        score -= warning_penalty

        # Bonus for error-free execution
        if len(self.errors) == 0:
            score = min(10.0, score + 0.5)

        return max(0.0, score)

    def calculate_maintainability_score(self) -> float:
        """Calculate maintainability quality score (0-10)."""
        # This would typically analyze code complexity, documentation, etc.
        # For now, we'll use heuristics based on test structure

        score = 8.0  # Default good score

        # Bonus for good assertion coverage
        if self.assertions_total >= 15:
            score = min(10.0, score + 1.0)
        elif self.assertions_total >= 10:
            score = min(10.0, score + 0.5)
        elif self.assertions_total < 5:
            score -= 1.0

        # Penalty for excessive errors (indicates poor test design)
        if len(self.errors) > 5:
            score -= 1.0

        return max(0.0, score)

    def finalize(self) -> TestQualityMetrics:
        """Calculate final quality metrics."""
        duration = time.time() - self.start_time
        current_memory = psutil.virtual_memory().used / 1024 / 1024
        memory_usage = max(0, current_memory - self.start_memory)

        # CPU usage (approximate)
        try:
            cpu_usage = self.process.cpu_percent()
        except:
            cpu_usage = 0.0

        # Average encoding metrics
        avg_encoding_fps = 0.0
        avg_output_quality = 8.0
        if self.encoding_metrics:
            avg_encoding_fps = sum(m["encoding_fps"] for m in self.encoding_metrics) / len(self.encoding_metrics)
            avg_output_quality = sum(m["output_quality"] for m in self.encoding_metrics) / len(self.encoding_metrics)

        return TestQualityMetrics(
            test_name=self.test_name,
            timestamp=datetime.now(),
            duration=duration,
            success=len(self.errors) == 0,
            functional_score=self.calculate_functional_score(),
            performance_score=self.calculate_performance_score(),
            reliability_score=self.calculate_reliability_score(),
            maintainability_score=self.calculate_maintainability_score(),
            peak_memory_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            assertions_passed=self.assertions_passed,
            assertions_total=self.assertions_total,
            error_count=len(self.errors),
            warning_count=len(self.warnings),
            videos_processed=self.videos_processed,
            encoding_fps=avg_encoding_fps,
            output_quality_score=avg_output_quality,
        )


class TestHistoryDatabase:
    """Manage test history and metrics tracking."""

    def __init__(self, db_path: Path = Path("test-history.db")):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the test history database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                duration REAL NOT NULL,
                success BOOLEAN NOT NULL,
                overall_score REAL NOT NULL,
                functional_score REAL NOT NULL,
                performance_score REAL NOT NULL,
                reliability_score REAL NOT NULL,
                maintainability_score REAL NOT NULL,
                peak_memory_mb REAL NOT NULL,
                cpu_usage_percent REAL NOT NULL,
                assertions_passed INTEGER NOT NULL,
                assertions_total INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                warning_count INTEGER NOT NULL,
                videos_processed INTEGER NOT NULL,
                encoding_fps REAL NOT NULL,
                output_quality_score REAL NOT NULL,
                metadata_json TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_name_timestamp
            ON test_runs(test_name, timestamp DESC)
        """)

        conn.commit()
        conn.close()

    def save_metrics(self, metrics: TestQualityMetrics, metadata: Optional[Dict[str, Any]] = None):
        """Save test metrics to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO test_runs (
                test_name, timestamp, duration, success, overall_score,
                functional_score, performance_score, reliability_score, maintainability_score,
                peak_memory_mb, cpu_usage_percent, assertions_passed, assertions_total,
                error_count, warning_count, videos_processed, encoding_fps,
                output_quality_score, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.test_name,
            metrics.timestamp.isoformat(),
            metrics.duration,
            metrics.success,
            metrics.overall_score,
            metrics.functional_score,
            metrics.performance_score,
            metrics.reliability_score,
            metrics.maintainability_score,
            metrics.peak_memory_mb,
            metrics.cpu_usage_percent,
            metrics.assertions_passed,
            metrics.assertions_total,
            metrics.error_count,
            metrics.warning_count,
            metrics.videos_processed,
            metrics.encoding_fps,
            metrics.output_quality_score,
            json.dumps(metadata or {})
        ))

        conn.commit()
        conn.close()

    def get_test_history(self, test_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics for a test."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT * FROM test_runs
            WHERE test_name = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (test_name, since_date.isoformat()))

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_quality_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """Get quality score trends over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT DATE(timestamp) as date,
                   AVG(overall_score) as avg_score,
                   AVG(functional_score) as avg_functional,
                   AVG(performance_score) as avg_performance,
                   AVG(reliability_score) as avg_reliability
            FROM test_runs
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (since_date.isoformat(),))

        results = cursor.fetchall()
        conn.close()

        if not results:
            return {}

        return {
            "dates": [row[0] for row in results],
            "overall": [row[1] for row in results],
            "functional": [row[2] for row in results],
            "performance": [row[3] for row in results],
            "reliability": [row[4] for row in results],
        }