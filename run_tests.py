#!/usr/bin/env python3
"""
Comprehensive test runner for Video Processor project.

This script provides a unified interface for running different types of tests
with proper categorization, parallel execution, and beautiful reporting.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


class VideoProcessorTestRunner:
    """Advanced test runner with categorization and reporting."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.reports_dir = self.project_root / "test-reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_tests(
        self,
        categories: Optional[List[str]] = None,
        parallel: bool = True,
        workers: int = 4,
        coverage: bool = True,
        html_report: bool = True,
        verbose: bool = False,
        fail_fast: bool = False,
        timeout: int = 300,
        pattern: Optional[str] = None,
        markers: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run tests with specified configuration.

        Args:
            categories: List of test categories to run (unit, integration, etc.)
            parallel: Enable parallel execution
            workers: Number of parallel workers
            coverage: Enable coverage reporting
            html_report: Generate HTML report
            verbose: Verbose output
            fail_fast: Stop on first failure
            timeout: Test timeout in seconds
            pattern: Test name pattern to match
            markers: Pytest marker expression

        Returns:
            Dict containing test results and metrics
        """
        print("🎬 Video Processor Test Runner")
        print("=" * 60)

        # Build pytest command
        cmd = self._build_pytest_command(
            categories=categories,
            parallel=parallel,
            workers=workers,
            coverage=coverage,
            html_report=html_report,
            verbose=verbose,
            fail_fast=fail_fast,
            timeout=timeout,
            pattern=pattern,
            markers=markers,
        )

        print(f"Command: {' '.join(cmd)}")
        print("=" * 60)

        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,  # Show output in real-time
                text=True,
            )
            duration = time.time() - start_time

            # Parse results
            results = self._parse_test_results(result.returncode, duration)

            # Print summary
            self._print_summary(results)

            return results

        except KeyboardInterrupt:
            print("\n❌ Tests interrupted by user")
            return {"success": False, "interrupted": True}
        except Exception as e:
            print(f"\n❌ Error running tests: {e}")
            return {"success": False, "error": str(e)}

    def _build_pytest_command(
        self,
        categories: Optional[List[str]] = None,
        parallel: bool = True,
        workers: int = 4,
        coverage: bool = True,
        html_report: bool = True,
        verbose: bool = False,
        fail_fast: bool = False,
        timeout: int = 300,
        pattern: Optional[str] = None,
        markers: Optional[str] = None,
    ) -> List[str]:
        """Build the pytest command with all options."""
        cmd = ["uv", "run", "pytest"]

        # Test discovery and filtering
        if categories:
            # Convert categories to marker expressions
            category_markers = []
            for category in categories:
                if category == "unit":
                    category_markers.append("unit")
                elif category == "integration":
                    category_markers.append("integration")
                elif category == "performance":
                    category_markers.append("performance")
                elif category == "smoke":
                    category_markers.append("smoke")
                elif category == "360":
                    category_markers.append("video_360")
                elif category == "ai":
                    category_markers.append("ai_analysis")
                elif category == "streaming":
                    category_markers.append("streaming")

            if category_markers:
                marker_expr = " or ".join(category_markers)
                cmd.extend(["-m", marker_expr])

        # Pattern matching
        if pattern:
            cmd.extend(["-k", pattern])

        # Additional markers
        if markers:
            if "-m" in cmd:
                # Combine with existing markers
                existing_idx = cmd.index("-m") + 1
                cmd[existing_idx] = f"({cmd[existing_idx]}) and ({markers})"
            else:
                cmd.extend(["-m", markers])

        # Parallel execution
        if parallel and workers > 1:
            cmd.extend(["-n", str(workers)])

        # Coverage
        if coverage:
            cmd.extend([
                "--cov=src/",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=json",
                f"--cov-fail-under=80",
            ])

        # Output options
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if fail_fast:
            cmd.extend(["--maxfail=1"])

        # Timeout
        cmd.extend([f"--timeout={timeout}"])

        # Report generation
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if html_report:
            html_path = self.reports_dir / f"pytest_report_{timestamp}.html"
            cmd.extend([f"--html={html_path}", "--self-contained-html"])

        # JSON report
        json_path = self.reports_dir / f"pytest_report_{timestamp}.json"
        cmd.extend([f"--json-report", f"--json-report-file={json_path}"])

        # Additional options
        cmd.extend([
            "--tb=short",
            "--durations=10",
            "--color=yes",
        ])

        return cmd

    def _parse_test_results(self, return_code: int, duration: float) -> Dict[str, Any]:
        """Parse test results from return code and other sources."""
        # Look for the most recent JSON report
        json_reports = list(self.reports_dir.glob("pytest_report_*.json"))
        if json_reports:
            latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_report, 'r') as f:
                    json_data = json.load(f)

                return {
                    "success": return_code == 0,
                    "duration": duration,
                    "total": json_data.get("summary", {}).get("total", 0),
                    "passed": json_data.get("summary", {}).get("passed", 0),
                    "failed": json_data.get("summary", {}).get("failed", 0),
                    "skipped": json_data.get("summary", {}).get("skipped", 0),
                    "error": json_data.get("summary", {}).get("error", 0),
                    "return_code": return_code,
                    "json_report": str(latest_report),
                }
            except Exception as e:
                print(f"Warning: Could not parse JSON report: {e}")

        # Fallback to simple return code analysis
        return {
            "success": return_code == 0,
            "duration": duration,
            "return_code": return_code,
        }

    def _print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🎬 TEST EXECUTION SUMMARY")
        print("=" * 60)

        if results.get("success"):
            print("✅ Tests PASSED")
        else:
            print("❌ Tests FAILED")

        print(f"⏱️  Duration: {results.get('duration', 0):.2f}s")

        if "total" in results:
            total = results["total"]
            passed = results["passed"]
            failed = results["failed"]
            skipped = results["skipped"]

            print(f"📊 Total Tests: {total}")
            print(f"   ✅ Passed: {passed}")
            print(f"   ❌ Failed: {failed}")
            print(f"   ⏭️  Skipped: {skipped}")

            if total > 0:
                success_rate = (passed / total) * 100
                print(f"   📈 Success Rate: {success_rate:.1f}%")

        # Report locations
        html_reports = list(self.reports_dir.glob("*.html"))
        if html_reports:
            latest_html = max(html_reports, key=lambda p: p.stat().st_mtime)
            print(f"📋 HTML Report: {latest_html}")

        if "json_report" in results:
            print(f"📄 JSON Report: {results['json_report']}")

        print("=" * 60)

    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run quick smoke tests."""
        print("🔥 Running Smoke Tests...")
        return self.run_tests(
            categories=["smoke"],
            parallel=True,
            workers=2,
            coverage=False,
            verbose=False,
            timeout=60,
        )

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage."""
        print("🧪 Running Unit Tests...")
        return self.run_tests(
            categories=["unit"],
            parallel=True,
            workers=4,
            coverage=True,
            verbose=False,
        )

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔧 Running Integration Tests...")
        return self.run_tests(
            categories=["integration"],
            parallel=False,  # Integration tests often need isolation
            workers=1,
            coverage=True,
            verbose=True,
            timeout=600,  # Longer timeout for integration tests
        )

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        print("🏃 Running Performance Tests...")
        return self.run_tests(
            categories=["performance"],
            parallel=False,  # Performance tests need isolation
            workers=1,
            coverage=False,
            verbose=True,
            timeout=900,  # Even longer timeout for performance tests
        )

    def run_360_tests(self) -> Dict[str, Any]:
        """Run 360° video processing tests."""
        print("🌐 Running 360° Video Tests...")
        return self.run_tests(
            categories=["360"],
            parallel=True,
            workers=2,
            coverage=True,
            verbose=True,
            timeout=600,
        )

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("🎯 Running Complete Test Suite...")
        return self.run_tests(
            parallel=True,
            workers=4,
            coverage=True,
            verbose=False,
            timeout=1200,  # 20 minutes total
        )

    def list_available_tests(self):
        """List all available tests with categories."""
        print("📋 Available Test Categories:")
        print("=" * 40)

        categories = {
            "smoke": "Quick smoke tests",
            "unit": "Unit tests for individual components",
            "integration": "Integration tests across components",
            "performance": "Performance and benchmark tests",
            "360": "360° video processing tests",
            "ai": "AI-powered video analysis tests",
            "streaming": "Streaming and adaptive bitrate tests",
        }

        for category, description in categories.items():
            print(f"  {category:12} - {description}")

        print("\nUsage Examples:")
        print("  python run_tests.py --category unit")
        print("  python run_tests.py --category unit integration")
        print("  python run_tests.py --smoke")
        print("  python run_tests.py --all")
        print("  python run_tests.py --pattern 'test_encoder'")
        print("  python run_tests.py --markers 'not slow'")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Video Processor Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --smoke                    # Quick smoke tests
  python run_tests.py --category unit            # Unit tests only
  python run_tests.py --category unit integration # Multiple categories
  python run_tests.py --all                      # All tests
  python run_tests.py --pattern 'test_encoder'   # Pattern matching
  python run_tests.py --markers 'not slow'       # Marker filtering
  python run_tests.py --no-parallel              # Disable parallel execution
  python run_tests.py --workers 8                # Use 8 parallel workers
        """)

    # Predefined test suites
    suite_group = parser.add_mutually_exclusive_group()
    suite_group.add_argument("--smoke", action="store_true", help="Run smoke tests")
    suite_group.add_argument("--unit", action="store_true", help="Run unit tests")
    suite_group.add_argument("--integration", action="store_true", help="Run integration tests")
    suite_group.add_argument("--performance", action="store_true", help="Run performance tests")
    suite_group.add_argument("--video-360", action="store_true", dest="video_360", help="Run 360° video tests")
    suite_group.add_argument("--all", action="store_true", help="Run all tests")

    # Custom configuration
    parser.add_argument("--category", nargs="+", choices=["unit", "integration", "performance", "smoke", "360", "ai", "streaming"], help="Test categories to run")
    parser.add_argument("--pattern", help="Test name pattern to match")
    parser.add_argument("--markers", help="Pytest marker expression")

    # Execution options
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--no-html", action="store_true", help="Disable HTML report generation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")

    # Information
    parser.add_argument("--list", action="store_true", help="List available test categories")

    args = parser.parse_args()

    runner = VideoProcessorTestRunner()

    # Handle list command
    if args.list:
        runner.list_available_tests()
        return

    # Handle predefined suites
    if args.smoke:
        results = runner.run_smoke_tests()
    elif args.unit:
        results = runner.run_unit_tests()
    elif args.integration:
        results = runner.run_integration_tests()
    elif args.performance:
        results = runner.run_performance_tests()
    elif args.video_360:
        results = runner.run_360_tests()
    elif args.all:
        results = runner.run_all_tests()
    else:
        # Custom configuration
        results = runner.run_tests(
            categories=args.category,
            parallel=not args.no_parallel,
            workers=args.workers,
            coverage=not args.no_coverage,
            html_report=not args.no_html,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            timeout=args.timeout,
            pattern=args.pattern,
            markers=args.markers,
        )

    # Exit with appropriate code
    sys.exit(0 if results.get("success", False) else 1)


if __name__ == "__main__":
    main()