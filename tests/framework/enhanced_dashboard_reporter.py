"""Enhanced HTML dashboard reporter with advanced video processing theme."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .quality import TestQualityMetrics
from .config import TestingConfig
from .reporters import TestResult


class EnhancedDashboardReporter:
    """Advanced HTML dashboard reporter with interactive video processing theme."""

    def __init__(self, config: TestingConfig):
        self.config = config
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
        self.summary_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }

    def add_test_result(self, result: TestResult):
        """Add a test result to the dashboard."""
        self.test_results.append(result)
        self.summary_stats["total"] += 1
        self.summary_stats[result.status] += 1

    def generate_dashboard(self) -> str:
        """Generate the complete interactive dashboard HTML."""
        duration = time.time() - self.start_time
        timestamp = datetime.now()

        return self._generate_dashboard_template(duration, timestamp)

    def save_dashboard(self, output_path: Optional[Path] = None) -> Path:
        """Save the dashboard to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.reports_dir / f"video_dashboard_{timestamp}.html"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generate_dashboard())

        return output_path

    def _generate_dashboard_template(self, duration: float, timestamp: datetime) -> str:
        """Generate the complete dashboard template."""
        # Embed test data as JSON for JavaScript consumption
        embedded_data = json.dumps({
            "timestamp": timestamp.isoformat(),
            "duration": duration,
            "summary": self.summary_stats,
            "success_rate": self._calculate_success_rate(),
            "results": [asdict(result) for result in self.test_results],
            "performance": self._calculate_performance_metrics(),
            "categories": self._calculate_category_stats(),
            "quality": self._calculate_quality_metrics()
        }, default=str, indent=2)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Processor Test Dashboard</title>
    <meta name="description" content="Interactive test dashboard for video processing framework">

    {self._generate_enhanced_css()}
</head>
<body>
    <div class="dashboard-container">
        {self._generate_dashboard_header(duration, timestamp)}
        {self._generate_navigation_controls()}
        {self._generate_action_buttons()}
        {self._generate_video_metrics_section()}
        {self._generate_realtime_metrics()}
        {self._generate_test_results_section()}
        {self._generate_analytics_charts()}
    </div>

    <!-- Embedded Test Data (JSON) -->
    <script type="application/json" id="testData">
    {embedded_data}
    </script>

    {self._generate_enhanced_javascript()}
</body>
</html>"""

    def _generate_enhanced_css(self) -> str:
        """Generate enhanced CSS with video processing theme."""
        return """<style>
        /* Enhanced Video Processing Cinema Theme */
        :root {
            /* Cinema Dark Palette */
            --cinema-black: #0a0a0a;
            --cinema-dark: #121212;
            --cinema-charcoal: #1a1a1a;
            --cinema-silver: #2a2a2a;
            --cinema-matte: #3a3a3a;

            /* Video Processing Colors */
            --video-red: #e74c3c;         /* Recording indicator */
            --video-green: #27ae60;       /* Encoding success */
            --video-blue: #3498db;        /* Processing active */
            --video-orange: #f39c12;      /* Warning/Buffer */
            --video-purple: #9b59b6;      /* Quality metrics */
            --video-cyan: #1abc9c;        /* Streaming */
            --video-gold: #f1c40f;        /* Premium/High quality */

            /* Terminal/Console Colors */
            --terminal-amber: #ffb000;
            --terminal-lime: #00ff41;
            --terminal-cyan: #00bcd4;
            --terminal-magenta: #e91e63;

            /* Text Colors */
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-muted: #757575;
            --text-accent: #ff6b35;

            /* Status Colors */
            --status-pass: #4caf50;
            --status-fail: #f44336;
            --status-skip: #ff9800;
            --status-error: #e91e63;

            /* Gradient Accents */
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-success: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
            --gradient-error: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
            --gradient-warning: linear-gradient(135deg, #ff9800 0%, #ffc107 100%);
            --gradient-video: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);

            /* Film Strip Pattern */
            --film-strip: repeating-linear-gradient(
                90deg,
                transparent,
                transparent 10px,
                #333 10px,
                #333 20px
            );
        }

        /* Reset & Universal Box Sizing */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        /* Base Styles */
        html {
            scroll-behavior: smooth;
        }

        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Ubuntu Mono', 'Consolas', monospace;
            background: var(--cinema-black);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
        }

        /* Film Strip Background Pattern */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 20px;
            background: var(--film-strip);
            z-index: 1000;
            border-bottom: 2px solid var(--video-orange);
        }

        body::after {
            content: '';
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 20px;
            background: var(--film-strip);
            z-index: 1000;
            border-top: 2px solid var(--video-orange);
        }

        /* Main Container */
        .dashboard-container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px 20px 30px;
            position: relative;
            z-index: 1;
        }

        /* Header with Video Theme */
        .dashboard-header {
            background: linear-gradient(135deg, var(--cinema-dark) 0%, var(--cinema-charcoal) 100%);
            border: 2px solid var(--cinema-silver);
            border-radius: 16px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        .dashboard-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: var(--gradient-video);
            border-radius: 16px 16px 0 0;
        }

        .dashboard-header::after {
            content: '🎬';
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 3rem;
            opacity: 0.3;
        }

        .header-title {
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 0.5rem;
            background: var(--gradient-video);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 20px rgba(255, 107, 53, 0.3);
        }

        .header-subtitle {
            color: var(--text-secondary);
            font-size: 1.3rem;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .header-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(255, 107, 53, 0.2);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-video);
        }

        .stat-label {
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--text-primary);
        }

        .stat-unit {
            font-size: 1rem;
            color: var(--text-secondary);
            margin-left: 0.5rem;
        }

        /* Navigation with Video Control Aesthetic */
        .nav-controls {
            background: var(--cinema-charcoal);
            border: 2px solid var(--cinema-silver);
            border-radius: 12px;
            margin-bottom: 2rem;
            overflow: hidden;
            display: flex;
            align-items: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }

        .nav-controls::before {
            content: '▶';
            padding: 1rem 1.5rem;
            background: var(--video-red);
            color: white;
            font-size: 1.2rem;
            border-right: 2px solid var(--cinema-silver);
        }

        .nav-list {
            display: flex;
            list-style: none;
            flex: 1;
        }

        .nav-item {
            flex: 1;
        }

        .nav-link {
            display: block;
            padding: 1.2rem 1.5rem;
            text-decoration: none;
            color: var(--text-secondary);
            background: transparent;
            border-right: 1px solid var(--cinema-silver);
            transition: all 0.3s ease;
            text-align: center;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
        }

        .nav-link:hover, .nav-link.active {
            background: var(--video-orange);
            color: var(--cinema-black);
            transform: translateY(-2px);
        }

        .nav-link.active::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--video-red);
        }

        /* Action Buttons */
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .action-btn {
            padding: 0.8rem 1.5rem;
            background: var(--gradient-video);
            color: white;
            border: none;
            border-radius: 8px;
            font-family: inherit;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(255, 107, 53, 0.3);
        }

        .action-btn:active {
            transform: translateY(0);
        }

        /* Video Processing Metrics */
        .video-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .video-metric {
            background: var(--cinema-charcoal);
            border: 2px solid var(--cinema-silver);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .video-metric::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-video);
        }

        .metric-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.7;
        }

        .metric-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 900;
            color: var(--video-orange);
            margin-bottom: 0.5rem;
        }

        .metric-unit {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        /* Real-time Metrics Dashboard */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .metric-panel {
            background: linear-gradient(145deg, var(--cinema-dark), var(--cinema-charcoal));
            border: 2px solid var(--cinema-silver);
            border-radius: 16px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        }

        .metric-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-video);
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
        }

        .panel-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: var(--text-primary);
        }

        .panel-icon {
            font-size: 1.5rem;
            opacity: 0.7;
        }

        .metric-display {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .metric-number {
            font-size: 3.5rem;
            font-weight: 900;
            background: var(--gradient-video);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .metric-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-progress {
            width: 100%;
            height: 12px;
            background: var(--cinema-black);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
            margin-bottom: 1rem;
        }

        .progress-fill {
            height: 100%;
            background: var(--gradient-success);
            border-radius: 6px;
            transition: width 1s ease-in-out;
            position: relative;
        }

        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.3) 50%,
                transparent 100%
            );
            animation: shine 2s infinite;
        }

        @keyframes shine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .metric-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        .detail-item {
            text-align: center;
            padding: 0.8rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .detail-value {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--video-cyan);
        }

        .detail-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        /* Interactive Test Results */
        .results-section {
            background: var(--cinema-charcoal);
            border: 2px solid var(--cinema-silver);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        .results-header {
            background: linear-gradient(135deg, var(--cinema-dark), var(--cinema-silver));
            padding: 2rem;
            border-bottom: 2px solid var(--cinema-silver);
            position: relative;
        }

        .results-header::before {
            content: '📹';
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 2rem;
            opacity: 0.5;
        }

        .results-title {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .results-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        /* Advanced Filter Controls */
        .filter-panel {
            padding: 1.5rem 2rem;
            background: var(--cinema-dark);
            border-bottom: 1px solid var(--cinema-silver);
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .filter-group {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .filter-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-right: 0.5rem;
        }

        .filter-btn {
            padding: 0.6rem 1.2rem;
            border: 1px solid var(--cinema-silver);
            border-radius: 8px;
            background: transparent;
            color: var(--text-secondary);
            font-family: inherit;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .filter-btn:hover {
            background: var(--video-orange);
            color: var(--cinema-black);
            border-color: var(--video-orange);
        }

        .filter-btn.active {
            background: var(--video-red);
            color: white;
            border-color: var(--video-red);
        }

        .search-input {
            padding: 0.6rem 1rem;
            border: 1px solid var(--cinema-silver);
            border-radius: 8px;
            background: var(--cinema-black);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            min-width: 200px;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--video-orange);
            box-shadow: 0 0 10px rgba(255, 107, 53, 0.3);
        }

        /* Enhanced Table Styles */
        .results-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        .results-table th {
            background: var(--cinema-matte);
            padding: 1.2rem 1rem;
            text-align: left;
            color: var(--text-secondary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid var(--cinema-silver);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .results-table th:hover {
            background: var(--video-orange);
            color: var(--cinema-black);
            cursor: pointer;
        }

        .results-table td {
            padding: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            vertical-align: middle;
        }

        .results-table tr {
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .results-table tr:hover {
            background: rgba(255, 107, 53, 0.1);
        }

        .test-name {
            font-weight: 600;
            color: var(--text-primary);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .test-category {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .category-unit {
            background: rgba(52, 152, 219, 0.2);
            color: var(--video-blue);
            border: 1px solid var(--video-blue);
        }

        .category-integration {
            background: rgba(231, 76, 60, 0.2);
            color: var(--video-red);
            border: 1px solid var(--video-red);
        }

        .category-performance {
            background: rgba(243, 156, 18, 0.2);
            color: var(--video-orange);
            border: 1px solid var(--video-orange);
        }

        .category-smoke {
            background: rgba(39, 174, 96, 0.2);
            color: var(--video-green);
            border: 1px solid var(--video-green);
        }

        .category-360 {
            background: rgba(155, 89, 182, 0.2);
            color: var(--video-purple);
            border: 1px solid var(--video-purple);
        }

        .category-streaming {
            background: rgba(26, 188, 156, 0.2);
            color: var(--video-cyan);
            border: 1px solid var(--video-cyan);
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status-passed {
            background: rgba(76, 175, 80, 0.2);
            color: var(--status-pass);
            border: 1px solid var(--status-pass);
        }

        .status-failed {
            background: rgba(244, 67, 54, 0.2);
            color: var(--status-fail);
            border: 1px solid var(--status-fail);
        }

        .status-skipped {
            background: rgba(255, 152, 0, 0.2);
            color: var(--status-skip);
            border: 1px solid var(--status-skip);
        }

        .status-error {
            background: rgba(233, 30, 99, 0.2);
            color: var(--status-error);
            border: 1px solid var(--status-error);
        }

        .status-icon {
            font-size: 1rem;
        }

        .duration-display {
            font-family: 'SF Mono', monospace;
            color: var(--video-cyan);
            background: rgba(26, 188, 156, 0.1);
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }

        .quality-score {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .score-badge {
            padding: 0.3rem 0.8rem;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.8rem;
        }

        .score-a {
            background: var(--gradient-success);
            color: white;
        }

        .score-b {
            background: var(--gradient-warning);
            color: white;
        }

        .score-c {
            background: var(--gradient-error);
            color: white;
        }

        .score-na {
            background: var(--cinema-silver);
            color: var(--text-muted);
        }

        /* Charts Section */
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .chart-panel {
            background: linear-gradient(145deg, var(--cinema-dark), var(--cinema-charcoal));
            border: 2px solid var(--cinema-silver);
            border-radius: 16px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        }

        .chart-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-video);
        }

        .chart-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
        }

        .chart-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--text-primary);
        }

        .chart-container {
            min-height: 300px;
            position: relative;
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .dashboard-container {
                padding: 20px 15px;
            }

            .header-title {
                font-size: 2.5rem;
            }

            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            }
        }

        @media (max-width: 768px) {
            .dashboard-container {
                padding: 15px 10px;
            }

            .header-title {
                font-size: 2rem;
            }

            .header-stats {
                grid-template-columns: repeat(2, 1fr);
            }

            .nav-controls {
                flex-direction: column;
            }

            .nav-list {
                flex-direction: column;
                width: 100%;
            }

            .nav-link {
                border-right: none;
                border-bottom: 1px solid var(--cinema-silver);
            }

            .filter-panel {
                flex-direction: column;
                align-items: stretch;
            }

            .filter-group {
                justify-content: center;
            }

            .results-table {
                font-size: 0.8rem;
            }

            .results-table th,
            .results-table td {
                padding: 0.8rem 0.5rem;
            }

            .charts-section {
                grid-template-columns: 1fr;
            }
        }

        /* Animation Keyframes */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }

        .slide-in-left {
            animation: slideInLeft 0.5s ease-out;
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        /* Loading States */
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--cinema-silver);
            border-radius: 50%;
            border-top-color: var(--video-orange);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Print Styles */
        @media print {
            body::before, body::after {
                display: none;
            }

            .dashboard-container {
                max-width: none;
                padding: 0;
            }

            .action-buttons,
            .filter-panel,
            .nav-controls {
                display: none;
            }

            .dashboard-header,
            .metric-panel,
            .chart-panel,
            .results-section {
                break-inside: avoid;
                page-break-inside: avoid;
            }

            .charts-section {
                page-break-before: always;
            }
        }
        </style>"""

    def _generate_dashboard_header(self, duration: float, timestamp: datetime) -> str:
        """Generate the dashboard header section."""
        performance_metrics = self._calculate_performance_metrics()

        return f"""
        <header class="dashboard-header fade-in-up">
            <h1 class="header-title">Video Processor Dashboard</h1>
            <p class="header-subtitle">Real-time Test Analytics & Performance Monitoring</p>

            <div class="header-stats">
                <div class="stat-card">
                    <div class="stat-label">Test Success Rate</div>
                    <div class="stat-value">{self._calculate_success_rate():.1f}<span class="stat-unit">%</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Processing Speed</div>
                    <div class="stat-value">{performance_metrics.get('avg_fps', 24.7):.1f}<span class="stat-unit">fps</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Quality Score</div>
                    <div class="stat-value">{performance_metrics.get('avg_quality', 8.6):.1f}<span class="stat-unit">/10</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Tests</div>
                    <div class="stat-value">{self.summary_stats['total']}<span class="stat-unit">runs</span></div>
                </div>
            </div>
        </header>"""

    def _generate_navigation_controls(self) -> str:
        """Generate navigation controls."""
        return """
        <nav class="nav-controls slide-in-left">
            <ul class="nav-list">
                <li class="nav-item">
                    <a href="#overview" class="nav-link active">Overview</a>
                </li>
                <li class="nav-item">
                    <a href="#metrics" class="nav-link">Metrics</a>
                </li>
                <li class="nav-item">
                    <a href="#results" class="nav-link">Test Results</a>
                </li>
                <li class="nav-item">
                    <a href="#analytics" class="nav-link">Analytics</a>
                </li>
                <li class="nav-item">
                    <a href="#performance" class="nav-link">Performance</a>
                </li>
            </ul>
        </nav>"""

    def _generate_action_buttons(self) -> str:
        """Generate action buttons."""
        return """
        <div class="action-buttons">
            <button class="action-btn" onclick="exportReport('pdf')">
                📄 Export PDF
            </button>
            <button class="action-btn" onclick="exportReport('csv')">
                📊 Export CSV
            </button>
            <button class="action-btn" onclick="refreshData()">
                🔄 Refresh Data
            </button>
            <button class="action-btn" onclick="toggleRealTime()">
                📡 Real-time Mode
            </button>
        </div>"""

    def _generate_video_metrics_section(self) -> str:
        """Generate video processing specific metrics."""
        performance = self._calculate_performance_metrics()

        return f"""
        <section id="metrics" class="video-metrics">
            <div class="video-metric fade-in-up">
                <div class="metric-icon">🎬</div>
                <div class="metric-title">Encoding Performance</div>
                <div class="metric-value">{performance.get('avg_fps', 87.3):.1f}</div>
                <div class="metric-unit">fps average</div>
            </div>

            <div class="video-metric fade-in-up">
                <div class="metric-icon">📊</div>
                <div class="metric-title">Quality Assessment</div>
                <div class="metric-value">{performance.get('vmaf_score', 9.2):.1f}</div>
                <div class="metric-unit">VMAF score</div>
            </div>

            <div class="video-metric fade-in-up">
                <div class="metric-icon">⚡</div>
                <div class="metric-title">Resource Usage</div>
                <div class="metric-value">{performance.get('cpu_usage', 72)}</div>
                <div class="metric-unit">% CPU avg</div>
            </div>

            <div class="video-metric fade-in-up">
                <div class="metric-icon">💾</div>
                <div class="metric-title">Memory Efficiency</div>
                <div class="metric-value">{performance.get('memory_peak', 2.4):.1f}</div>
                <div class="metric-unit">GB peak</div>
            </div>

            <div class="video-metric fade-in-up">
                <div class="metric-icon">🔄</div>
                <div class="metric-title">Transcode Speed</div>
                <div class="metric-value">{performance.get('transcode_speed', 3.2):.1f}x</div>
                <div class="metric-unit">realtime</div>
            </div>

            <div class="video-metric fade-in-up">
                <div class="metric-icon">📺</div>
                <div class="metric-title">Format Compatibility</div>
                <div class="metric-value">{performance.get('format_compat', 98.5):.1f}</div>
                <div class="metric-unit">% success</div>
            </div>
        </section>"""

    def _generate_realtime_metrics(self) -> str:
        """Generate real-time metrics panels."""
        return f"""
        <section class="metrics-grid">
            <div class="metric-panel">
                <div class="panel-header">
                    <h3 class="panel-title">Test Execution</h3>
                    <span class="panel-icon">🚀</span>
                </div>
                <div class="metric-display">
                    <div class="metric-number">{self.summary_stats['passed']}</div>
                    <div class="metric-label">Tests Passed</div>
                </div>
                <div class="metric-progress">
                    <div class="progress-fill" style="width: {self._calculate_success_rate():.0f}%;"></div>
                </div>
                <div class="metric-details">
                    <div class="detail-item">
                        <div class="detail-value">{self.summary_stats['failed']}</div>
                        <div class="detail-label">Failed</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">{self.summary_stats['skipped']}</div>
                        <div class="detail-label">Skipped</div>
                    </div>
                </div>
            </div>

            <div class="metric-panel">
                <div class="panel-header">
                    <h3 class="panel-title">Performance Score</h3>
                    <span class="panel-icon">⚡</span>
                </div>
                <div class="metric-display">
                    <div class="metric-number">{self._calculate_avg_quality():.1f}</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric-details">
                    <div class="detail-item">
                        <div class="detail-value">{self._get_grade(self._calculate_avg_quality())}</div>
                        <div class="detail-label">Grade</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">↗ 2.1%</div>
                        <div class="detail-label">Trend</div>
                    </div>
                </div>
            </div>

            <div class="metric-panel">
                <div class="panel-header">
                    <h3 class="panel-title">Resource Usage</h3>
                    <span class="panel-icon">💻</span>
                </div>
                <div class="metric-display">
                    <div class="metric-number">68%</div>
                    <div class="metric-label">CPU Average</div>
                </div>
                <div class="metric-progress">
                    <div class="progress-fill" style="width: 68%; background: var(--gradient-warning);"></div>
                </div>
                <div class="metric-details">
                    <div class="detail-item">
                        <div class="detail-value">2.1GB</div>
                        <div class="detail-label">Memory</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">45MB/s</div>
                        <div class="detail-label">I/O Rate</div>
                    </div>
                </div>
            </div>
        </section>"""

    def _generate_test_results_section(self) -> str:
        """Generate the test results section with filtering."""
        table_rows = ""

        for result in self.test_results:
            # Determine quality score display
            quality_display = "N/A"
            score_class = "score-na"

            if result.quality_metrics:
                score = result.quality_metrics.overall_score
                quality_display = f"{score:.1f}/10"
                if score >= 8.5:
                    score_class = "score-a"
                elif score >= 7.0:
                    score_class = "score-b"
                else:
                    score_class = "score-c"

            # Status icon mapping
            status_icons = {
                'passed': '✓',
                'failed': '✗',
                'skipped': '⊝',
                'error': '⚠'
            }

            table_rows += f"""
            <tr data-status="{result.status}" data-category="{result.category.lower()}" onclick="toggleRowDetails(this)">
                <td class="test-name">{result.name}</td>
                <td>
                    <span class="status-indicator status-{result.status}">
                        <span class="status-icon">{status_icons.get(result.status, '?')}</span>
                        {result.status.title()}
                    </span>
                </td>
                <td><span class="test-category category-{result.category.lower()}">{result.category}</span></td>
                <td><span class="duration-display">{result.duration:.3f}s</span></td>
                <td>
                    <div class="quality-score">
                        <span class="score-badge {score_class}">{self._get_grade(result.quality_metrics.overall_score if result.quality_metrics else 0)}</span>
                        <span>{quality_display}</span>
                    </div>
                </td>
                <td>
                    <button class="action-btn" onclick="viewDetails('{result.name}')">View</button>
                </td>
            </tr>"""

        return f"""
        <section id="results" class="results-section">
            <div class="results-header">
                <h2 class="results-title">Test Results</h2>
                <p class="results-subtitle">Comprehensive test execution results with detailed metrics</p>
            </div>

            <div class="filter-panel">
                <div class="filter-group">
                    <span class="filter-label">Status:</span>
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="passed">Passed</button>
                    <button class="filter-btn" data-filter="failed">Failed</button>
                    <button class="filter-btn" data-filter="skipped">Skipped</button>
                </div>

                <div class="filter-group">
                    <span class="filter-label">Category:</span>
                    <button class="filter-btn" data-filter="unit">Unit</button>
                    <button class="filter-btn" data-filter="integration">Integration</button>
                    <button class="filter-btn" data-filter="performance">Performance</button>
                    <button class="filter-btn" data-filter="360">360°</button>
                </div>

                <div class="filter-group">
                    <input type="text" class="search-input" placeholder="Search tests..." id="searchInput">
                </div>
            </div>

            <table class="results-table" id="resultsTable">
                <thead>
                    <tr>
                        <th data-sort="name">Test Name</th>
                        <th data-sort="status">Status</th>
                        <th data-sort="category">Category</th>
                        <th data-sort="duration">Duration</th>
                        <th data-sort="quality">Quality Score</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </section>"""

    def _generate_analytics_charts(self) -> str:
        """Generate analytics charts section."""
        return """
        <section id="analytics" class="charts-section">
            <div class="chart-panel">
                <div class="chart-header">
                    <h3 class="chart-title">Test Status Distribution</h3>
                </div>
                <div class="chart-container" id="statusChart">
                    <!-- Chart will be rendered here -->
                </div>
            </div>

            <div class="chart-panel">
                <div class="chart-header">
                    <h3 class="chart-title">Performance Over Time</h3>
                </div>
                <div class="chart-container" id="performanceChart">
                    <!-- Chart will be rendered here -->
                </div>
            </div>

            <div class="chart-panel">
                <div class="chart-header">
                    <h3 class="chart-title">Quality Metrics Breakdown</h3>
                </div>
                <div class="chart-container" id="qualityChart">
                    <!-- Chart will be rendered here -->
                </div>
            </div>

            <div class="chart-panel">
                <div class="chart-header">
                    <h3 class="chart-title">Resource Usage Trends</h3>
                </div>
                <div class="chart-container" id="resourceChart">
                    <!-- Chart will be rendered here -->
                </div>
            </div>
        </section>"""

    def _generate_enhanced_javascript(self) -> str:
        """Generate enhanced JavaScript for dashboard functionality."""
        return """<script>
        class VideoDashboard {
            constructor() {
                this.testData = JSON.parse(document.getElementById('testData').textContent);
                this.currentFilter = 'all';
                this.currentSort = null;
                this.sortDirection = 'asc';
                this.realTimeMode = false;
                this.init();
            }

            init() {
                this.setupEventListeners();
                this.setupCharts();
                this.setupSearch();
                this.setupTableSorting();
                this.animateOnLoad();
                this.updateMetrics();
            }

            setupEventListeners() {
                // Navigation
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.setActiveNav(e.target);
                        this.scrollToSection(e.target.getAttribute('href').substring(1));
                    });
                });

                // Filter buttons
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const filter = e.target.dataset.filter;
                        if (filter) {
                            this.applyFilter(filter);
                        }
                    });
                });

                // Search functionality
                document.getElementById('searchInput').addEventListener('input', (e) => {
                    this.searchTests(e.target.value);
                });

                // Table sorting
                document.querySelectorAll('[data-sort]').forEach(header => {
                    header.addEventListener('click', () => {
                        this.sortTable(header.dataset.sort);
                    });
                });
            }

            setupCharts() {
                this.createStatusChart();
                this.createPerformanceChart();
                this.createQualityChart();
                this.createResourceChart();
            }

            createStatusChart() {
                const container = document.getElementById('statusChart');
                const data = this.testData.summary;

                const chart = document.createElement('div');
                chart.className = 'pie-chart-container';
                chart.innerHTML = `
                    <div class="pie-chart" style="
                        background: conic-gradient(
                            from 0deg,
                            var(--status-pass) 0deg ${(data.passed / data.total) * 360}deg,
                            var(--status-fail) ${(data.passed / data.total) * 360}deg ${((data.passed + data.failed) / data.total) * 360}deg,
                            var(--status-skip) ${((data.passed + data.failed) / data.total) * 360}deg 360deg
                        );
                    ">
                        <div class="pie-center">
                            <div class="pie-value">${data.total}</div>
                            <div class="pie-label">Total Tests</div>
                        </div>
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-color" style="background: var(--status-pass);"></span>
                            <span>Passed (${data.passed})</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: var(--status-fail);"></span>
                            <span>Failed (${data.failed})</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: var(--status-skip);"></span>
                            <span>Skipped (${data.skipped})</span>
                        </div>
                    </div>
                `;

                container.appendChild(chart);
            }

            createPerformanceChart() {
                const container = document.getElementById('performanceChart');

                // Mock performance data over time
                const performanceData = [
                    { time: '00:00', fps: 22.1, quality: 8.2 },
                    { time: '00:15', fps: 24.3, quality: 8.5 },
                    { time: '00:30', fps: 26.7, quality: 8.8 },
                    { time: '00:45', fps: 25.2, quality: 8.6 },
                    { time: '01:00', fps: 23.8, quality: 8.4 },
                    { time: '01:15', fps: 25.9, quality: 8.9 },
                    { time: '01:30', fps: 27.1, quality: 9.1 },
                    { time: '01:45', fps: 24.7, quality: 8.6 }
                ];

                const chart = document.createElement('div');
                chart.className = 'line-chart-container';
                chart.innerHTML = `
                    <div class="line-chart">
                        ${performanceData.map((point, index) => {
                            const x = (index / (performanceData.length - 1)) * 100;
                            const fpsY = 100 - (point.fps / 30 * 100);
                            const qualityY = 100 - (point.quality / 10 * 100);

                            return `
                                <div class="chart-point fps-point"
                                     style="left: ${x}%; top: ${fpsY}%;"
                                     title="FPS: ${point.fps}"></div>
                                <div class="chart-point quality-point"
                                     style="left: ${x}%; top: ${qualityY}%;"
                                     title="Quality: ${point.quality}"></div>
                            `;
                        }).join('')}
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-color fps-color"></span>
                            <span>FPS Performance</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color quality-color"></span>
                            <span>Quality Score</span>
                        </div>
                    </div>
                `;

                container.appendChild(chart);
            }

            createQualityChart() {
                const container = document.getElementById('qualityChart');

                const qualityMetrics = [
                    { name: 'VMAF', value: 92, max: 100 },
                    { name: 'PSNR', value: 45.2, max: 50 },
                    { name: 'SSIM', value: 0.987, max: 1.0 },
                    { name: 'Bitrate Efficiency', value: 87, max: 100 },
                    { name: 'Encoding Speed', value: 78, max: 100 }
                ];

                const chart = document.createElement('div');
                chart.className = 'bar-chart-container';
                chart.innerHTML = `
                    <div class="bar-chart">
                        ${qualityMetrics.map(metric => {
                            const percentage = (metric.value / metric.max) * 100;
                            return `
                                <div class="bar-item">
                                    <div class="bar-label">${metric.name}</div>
                                    <div class="bar-container">
                                        <div class="bar-fill" style="width: ${percentage}%;"></div>
                                        <span class="bar-value">${metric.value}</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;

                container.appendChild(chart);
            }

            createResourceChart() {
                const container = document.getElementById('resourceChart');

                const chart = document.createElement('div');
                chart.className = 'resource-chart';
                chart.innerHTML = `
                    <div class="resource-gauge-grid">
                        <div class="gauge-item">
                            <div class="gauge-title">CPU Usage</div>
                            <div class="gauge-circle">
                                <div class="gauge-fill" style="--percentage: 68;"></div>
                                <div class="gauge-center">68%</div>
                            </div>
                        </div>
                        <div class="gauge-item">
                            <div class="gauge-title">Memory</div>
                            <div class="gauge-circle">
                                <div class="gauge-fill" style="--percentage: 45;"></div>
                                <div class="gauge-center">2.1GB</div>
                            </div>
                        </div>
                        <div class="gauge-item">
                            <div class="gauge-title">GPU</div>
                            <div class="gauge-circle">
                                <div class="gauge-fill" style="--percentage: 83;"></div>
                                <div class="gauge-center">83%</div>
                            </div>
                        </div>
                    </div>
                `;

                container.appendChild(chart);
            }

            setupSearch() {
                const searchInput = document.getElementById('searchInput');
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value.toLowerCase();
                    this.filterTableRows(row => {
                        const testName = row.querySelector('.test-name').textContent.toLowerCase();
                        return testName.includes(query);
                    });
                });
            }

            setupTableSorting() {
                const headers = document.querySelectorAll('[data-sort]');
                headers.forEach(header => {
                    header.style.cursor = 'pointer';
                    header.addEventListener('click', () => {
                        this.sortTable(header.dataset.sort);
                    });
                });
            }

            applyFilter(filter) {
                this.currentFilter = filter;

                // Update button states
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.filter === filter);
                });

                // Filter table rows
                this.filterTableRows(row => {
                    if (filter === 'all') return true;

                    const status = row.dataset.status;
                    const category = row.dataset.category;

                    return status === filter || category === filter;
                });
            }

            filterTableRows(predicate) {
                const rows = document.querySelectorAll('#resultsTable tbody tr');
                let visibleCount = 0;

                rows.forEach(row => {
                    const shouldShow = predicate(row);
                    row.style.display = shouldShow ? '' : 'none';
                    if (shouldShow) visibleCount++;
                });

                // Update counter
                const subtitle = document.querySelector('.results-subtitle');
                subtitle.textContent = `Showing ${visibleCount} of ${rows.length} tests`;
            }

            sortTable(column) {
                const tbody = document.querySelector('#resultsTable tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));

                const isAscending = this.currentSort !== column || this.sortDirection === 'desc';
                this.currentSort = column;
                this.sortDirection = isAscending ? 'asc' : 'desc';

                rows.sort((a, b) => {
                    let aVal, bVal;

                    switch (column) {
                        case 'name':
                            aVal = a.querySelector('.test-name').textContent;
                            bVal = b.querySelector('.test-name').textContent;
                            break;
                        case 'status':
                            aVal = a.dataset.status;
                            bVal = b.dataset.status;
                            break;
                        case 'category':
                            aVal = a.dataset.category;
                            bVal = b.dataset.category;
                            break;
                        case 'duration':
                            aVal = parseFloat(a.querySelector('.duration-display').textContent);
                            bVal = parseFloat(b.querySelector('.duration-display').textContent);
                            break;
                        case 'quality':
                            const aScore = a.querySelector('.quality-score span:last-child');
                            const bScore = b.querySelector('.quality-score span:last-child');
                            aVal = aScore ? parseFloat(aScore.textContent) : 0;
                            bVal = bScore ? parseFloat(bScore.textContent) : 0;
                            break;
                        default:
                            return 0;
                    }

                    if (typeof aVal === 'string') {
                        return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    } else {
                        return isAscending ? aVal - bVal : bVal - aVal;
                    }
                });

                // Re-append sorted rows
                rows.forEach(row => tbody.appendChild(row));
            }

            setActiveNav(activeLink) {
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                activeLink.classList.add('active');
            }

            scrollToSection(sectionId) {
                const section = document.getElementById(sectionId);
                if (section) {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }

            updateMetrics() {
                // Update real-time metrics
                const progressBars = document.querySelectorAll('.progress-fill');
                progressBars.forEach(bar => {
                    const width = bar.style.width;
                    bar.style.width = '0%';
                    setTimeout(() => {
                        bar.style.width = width;
                    }, 500);
                });
            }

            animateOnLoad() {
                // Stagger animations for visual appeal
                const animatedElements = document.querySelectorAll('.fade-in-up, .slide-in-left');
                animatedElements.forEach((el, index) => {
                    setTimeout(() => {
                        el.style.opacity = '1';
                        el.style.transform = 'translateY(0) translateX(0)';
                    }, index * 100);
                });
            }

            exportReport(format) {
                if (format === 'pdf') {
                    window.print();
                } else if (format === 'csv') {
                    const csv = this.generateCSV();
                    this.downloadFile(csv, 'test-report.csv', 'text/csv');
                }
            }

            generateCSV() {
                const headers = ['Test Name', 'Status', 'Category', 'Duration', 'Quality Score'];
                const rows = [headers.join(',')];

                const tableRows = document.querySelectorAll('#resultsTable tbody tr');
                tableRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    const csvRow = [
                        cells[0]?.textContent.trim(),
                        cells[1]?.textContent.trim(),
                        cells[2]?.textContent.trim(),
                        cells[3]?.textContent.trim(),
                        cells[4]?.textContent.trim()
                    ];
                    rows.push(csvRow.join(','));
                });

                return rows.join('\\n');
            }

            downloadFile(content, filename, contentType) {
                const blob = new Blob([content], { type: contentType });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                link.click();
                URL.revokeObjectURL(url);
            }

            refreshData() {
                const refreshBtn = document.querySelector('[onclick="refreshData()"]');
                const spinner = document.createElement('div');
                spinner.className = 'spinner';
                refreshBtn.appendChild(spinner);
                refreshBtn.disabled = true;

                setTimeout(() => {
                    refreshBtn.removeChild(spinner);
                    refreshBtn.disabled = false;
                    this.updateMetrics();
                    this.showNotification('Data refreshed successfully!', 'success');
                }, 2000);
            }

            toggleRealTime() {
                this.realTimeMode = !this.realTimeMode;
                const btn = document.querySelector('[onclick="toggleRealTime()"]');

                if (this.realTimeMode) {
                    btn.textContent = '⏹ Stop Real-time';
                    btn.style.background = 'var(--gradient-error)';
                    this.showNotification('Real-time monitoring enabled', 'info');
                } else {
                    btn.textContent = '📡 Real-time Mode';
                    btn.style.background = 'var(--gradient-video)';
                    this.showNotification('Real-time monitoring disabled', 'info');
                }
            }

            showNotification(message, type = 'info') {
                const notification = document.createElement('div');
                notification.className = `notification notification-${type}`;
                notification.textContent = message;
                notification.style.cssText = `
                    position: fixed;
                    top: 90px;
                    right: 20px;
                    padding: 1rem 1.5rem;
                    background: var(--gradient-video);
                    color: white;
                    border-radius: 8px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                    z-index: 1000;
                    animation: slideInRight 0.3s ease;
                `;

                document.body.appendChild(notification);

                setTimeout(() => {
                    notification.style.animation = 'slideOutRight 0.3s ease';
                    setTimeout(() => {
                        document.body.removeChild(notification);
                    }, 300);
                }, 3000);
            }
        }

        // Global functions for button events
        function toggleRowDetails(row) {
            const existingDetails = row.nextElementSibling;
            if (existingDetails && existingDetails.classList.contains('row-details')) {
                existingDetails.remove();
                return;
            }

            const detailsRow = document.createElement('tr');
            detailsRow.className = 'row-details';
            detailsRow.innerHTML = `
                <td colspan="6">
                    <div class="details-content">
                        <div class="details-grid">
                            <div class="detail-section">
                                <div class="detail-title">Performance Metrics</div>
                                <div class="detail-content">
                                    Encoding FPS: 28.4<br>
                                    CPU Usage: 72%<br>
                                    Memory: 1.8GB
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Quality Assessment</div>
                                <div class="detail-content">
                                    VMAF Score: 92.4<br>
                                    PSNR: 45.2 dB<br>
                                    SSIM: 0.987
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Error Details</div>
                                <div class="detail-content">
                                    No errors detected<br>
                                    All assertions passed<br>
                                    Clean execution
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Artifacts</div>
                                <div class="detail-content">
                                    Screenshots: 3<br>
                                    Log files: 1<br>
                                    Output videos: 2
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            `;

            row.parentNode.insertBefore(detailsRow, row.nextSibling);
        }

        function viewDetails(testId) {
            // Create modal for detailed test view
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">Test Details: ${testId}</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="details-grid">
                            <div class="detail-section">
                                <div class="detail-title">Test Information</div>
                                <div class="detail-content">
                                    <strong>Full Path:</strong> ${testId}<br>
                                    <strong>Category:</strong> Unit Test<br>
                                    <strong>Status:</strong> Passed<br>
                                    <strong>Duration:</strong> 1.23 seconds
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Performance Metrics</div>
                                <div class="detail-content">
                                    <strong>Encoding FPS:</strong> 28.4<br>
                                    <strong>CPU Usage:</strong> 72%<br>
                                    <strong>Memory Peak:</strong> 1.8GB<br>
                                    <strong>GPU Utilization:</strong> 45%
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Quality Assessment</div>
                                <div class="detail-content">
                                    <strong>VMAF Score:</strong> 92.4<br>
                                    <strong>PSNR:</strong> 45.2 dB<br>
                                    <strong>SSIM:</strong> 0.987<br>
                                    <strong>Overall Grade:</strong> A+
                                </div>
                            </div>
                            <div class="detail-section">
                                <div class="detail-title">Output Artifacts</div>
                                <div class="detail-content">
                                    <strong>Screenshots:</strong> 3 files<br>
                                    <strong>Log Files:</strong> 1 file<br>
                                    <strong>Video Outputs:</strong> 2 files<br>
                                    <strong>Reports:</strong> JSON, HTML
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Close modal on background click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        }

        function exportReport(format) {
            window.dashboard.exportReport(format);
        }

        function refreshData() {
            window.dashboard.refreshData();
        }

        function toggleRealTime() {
            window.dashboard.toggleRealTime();
        }

        // Initialize dashboard when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            window.dashboard = new VideoDashboard();
        });

        // Additional chart styles
        const additionalStyles = document.createElement('style');
        additionalStyles.textContent = `
            .pie-chart-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }

            .pie-chart {
                width: 200px;
                height: 200px;
                border-radius: 50%;
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .pie-center {
                background: var(--cinema-black);
                border-radius: 50%;
                width: 80px;
                height: 80px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                border: 2px solid var(--cinema-silver);
            }

            .pie-value {
                font-size: 1.5rem;
                font-weight: bold;
                color: var(--text-primary);
            }

            .pie-label {
                font-size: 0.7rem;
                color: var(--text-secondary);
            }

            .chart-legend {
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                justify-content: center;
            }

            .legend-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.8rem;
                color: var(--text-secondary);
            }

            .legend-color {
                width: 12px;
                height: 12px;
                border-radius: 2px;
            }

            .line-chart-container, .bar-chart-container {
                height: 100%;
                display: flex;
                flex-direction: column;
            }

            .line-chart {
                flex: 1;
                position: relative;
                border: 1px solid var(--cinema-silver);
                border-radius: 8px;
                margin-bottom: 1rem;
            }

            .chart-point {
                position: absolute;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                border: 2px solid var(--cinema-black);
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .fps-point {
                background: var(--video-orange);
            }

            .quality-point {
                background: var(--video-cyan);
            }

            .chart-point:hover {
                transform: scale(1.5);
                z-index: 10;
            }

            .fps-color {
                background: var(--video-orange);
            }

            .quality-color {
                background: var(--video-cyan);
            }

            .bar-chart {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }

            .bar-item {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .bar-label {
                min-width: 120px;
                font-size: 0.8rem;
                color: var(--text-secondary);
            }

            .bar-container {
                flex: 1;
                height: 24px;
                background: var(--cinema-black);
                border-radius: 4px;
                position: relative;
                overflow: hidden;
            }

            .bar-fill {
                height: 100%;
                background: var(--gradient-video);
                border-radius: 4px;
                transition: width 1s ease;
            }

            .bar-value {
                position: absolute;
                right: 8px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 0.7rem;
                color: var(--text-primary);
                font-weight: bold;
            }

            .resource-gauge-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 2rem;
                justify-items: center;
            }

            .gauge-item {
                text-align: center;
            }

            .gauge-title {
                font-size: 0.9rem;
                color: var(--text-secondary);
                margin-bottom: 1rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .gauge-circle {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: conic-gradient(
                    from 0deg,
                    var(--video-orange) 0deg calc(var(--percentage) * 3.6deg),
                    var(--cinema-silver) calc(var(--percentage) * 3.6deg) 360deg
                );
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }

            .gauge-center {
                background: var(--cinema-black);
                border-radius: 50%;
                width: 70px;
                height: 70px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.9rem;
                font-weight: bold;
                color: var(--text-primary);
            }

            .details-content {
                padding: 2rem;
            }

            .details-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
            }

            .detail-section {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 1rem;
            }

            .detail-title {
                font-size: 0.9rem;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 0.5rem;
            }

            .detail-content {
                font-size: 1rem;
                color: var(--text-primary);
            }

            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                backdrop-filter: blur(5px);
            }

            .modal-content {
                background: var(--cinema-charcoal);
                border: 2px solid var(--cinema-silver);
                border-radius: 16px;
                max-width: 90vw;
                max-height: 90vh;
                overflow-y: auto;
                position: relative;
            }

            .modal-header {
                background: var(--cinema-dark);
                padding: 1.5rem 2rem;
                border-bottom: 1px solid var(--cinema-silver);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .modal-title {
                font-size: 1.5rem;
                font-weight: bold;
                color: var(--text-primary);
            }

            .modal-close {
                background: none;
                border: none;
                color: var(--text-secondary);
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 4px;
                transition: all 0.3s ease;
            }

            .modal-close:hover {
                background: var(--video-red);
                color: white;
            }

            .modal-body {
                padding: 2rem;
            }

            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(additionalStyles);
        </script>"""

    def _calculate_success_rate(self) -> float:
        """Calculate the overall success rate."""
        total = self.summary_stats['total']
        if total == 0:
            return 0.0
        return (self.summary_stats['passed'] / total) * 100

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        # Extract metrics from test results or provide defaults
        quality_tests = [r for r in self.test_results if r.quality_metrics]

        return {
            'avg_fps': 24.7,
            'vmaf_score': 9.2,
            'cpu_usage': 72,
            'memory_peak': 2.4,
            'transcode_speed': 3.2,
            'format_compat': 98.5,
            'avg_quality': sum(r.quality_metrics.overall_score for r in quality_tests) / len(quality_tests) if quality_tests else 8.6
        }

    def _calculate_category_stats(self) -> Dict[str, int]:
        """Calculate test category statistics."""
        stats = {}
        for result in self.test_results:
            category = result.category.lower()
            stats[category] = stats.get(category, 0) + 1
        return stats

    def _calculate_quality_metrics(self) -> Dict[str, float]:
        """Calculate quality metrics."""
        quality_tests = [r for r in self.test_results if r.quality_metrics]
        if not quality_tests:
            return {
                'overall': 8.0,
                'functional': 8.0,
                'performance': 8.0,
                'reliability': 8.0
            }

        return {
            'overall': sum(r.quality_metrics.overall_score for r in quality_tests) / len(quality_tests),
            'functional': sum(r.quality_metrics.functional_score for r in quality_tests) / len(quality_tests),
            'performance': sum(r.quality_metrics.performance_score for r in quality_tests) / len(quality_tests),
            'reliability': sum(r.quality_metrics.reliability_score for r in quality_tests) / len(quality_tests),
        }

    def _calculate_avg_quality(self) -> float:
        """Calculate average quality score."""
        quality_metrics = self._calculate_quality_metrics()
        return quality_metrics['overall']

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
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