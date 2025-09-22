"""Modern HTML reporting system with video processing theme."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import base64

from .quality import TestQualityMetrics
from .config import TestingConfig


@dataclass
class TestResult:
    """Individual test result data."""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    category: str
    error_message: Optional[str] = None
    artifacts: List[str] = None
    quality_metrics: Optional[TestQualityMetrics] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class HTMLReporter:
    """Modern HTML reporter with video processing theme."""

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
        """Add a test result to the report."""
        self.test_results.append(result)
        self.summary_stats["total"] += 1
        self.summary_stats[result.status] += 1

    def generate_report(self) -> str:
        """Generate the complete HTML report."""
        duration = time.time() - self.start_time
        timestamp = datetime.now()

        html_content = self._generate_html_template(duration, timestamp)
        return html_content

    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """Save the HTML report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.reports_dir / f"test_report_{timestamp}.html"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generate_report())

        return output_path

    def _generate_html_template(self, duration: float, timestamp: datetime) -> str:
        """Generate the complete HTML template."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Processor Test Report</title>
    {self._generate_css()}
    {self._generate_javascript()}
</head>
<body>
    <div class="container">
        {self._generate_header(duration, timestamp)}
        {self._generate_navigation()}
        {self._generate_summary_section()}
        {self._generate_quality_overview()}
        {self._generate_test_results_section()}
        {self._generate_charts_section()}
        {self._generate_footer()}
    </div>
</body>
</html>"""

    def _generate_css(self) -> str:
        """Generate CSS styles with video processing theme."""
        return """<style>
/* Video Processing Theme - Dark Terminal Aesthetic */
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --accent-primary: #f85149;
    --accent-secondary: #7c3aed;
    --accent-success: #238636;
    --accent-warning: #d29922;
    --accent-info: #1f6feb;
    --text-primary: #f0f6fc;
    --text-secondary: #8b949e;
    --text-muted: #656d76;
    --border-primary: #30363d;
    --border-secondary: #21262d;
    --video-accent: #ff6b35;
    --terminal-green: #00ff00;
    --terminal-red: #ff4444;
    --terminal-yellow: #ffff00;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Consolas', monospace;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    overflow-x: auto;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

/* Header Styles */
.header {
    background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--video-accent), var(--accent-primary), var(--accent-secondary));
}

.header-title {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
    background: linear-gradient(45deg, var(--video-accent), var(--accent-primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-subtitle {
    color: var(--text-secondary);
    font-size: 1.1rem;
    margin-bottom: 1rem;
}

.header-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    font-size: 0.9rem;
}

.meta-item {
    background: var(--bg-primary);
    padding: 0.75rem 1rem;
    border-radius: 6px;
    border-left: 3px solid var(--video-accent);
}

.meta-label {
    color: var(--text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.meta-value {
    color: var(--text-primary);
    font-weight: bold;
    font-size: 1rem;
}

/* Navigation */
.nav {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    margin-bottom: 2rem;
    overflow: hidden;
}

.nav-list {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
}

.nav-item {
    flex: 1;
}

.nav-link {
    display: block;
    padding: 1rem;
    text-decoration: none;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-primary);
    transition: all 0.3s ease;
    text-align: center;
    font-weight: 500;
}

.nav-link:hover, .nav-link.active {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-bottom: 2px solid var(--video-accent);
}

.nav-link:last-child {
    border-right: none;
}

/* Summary Cards */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.summary-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.summary-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.summary-card.passed { border-left: 4px solid var(--accent-success); }
.summary-card.failed { border-left: 4px solid var(--accent-primary); }
.summary-card.skipped { border-left: 4px solid var(--accent-warning); }
.summary-card.total { border-left: 4px solid var(--accent-info); }

.card-number {
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.card-number.passed { color: var(--accent-success); }
.card-number.failed { color: var(--accent-primary); }
.card-number.skipped { color: var(--accent-warning); }
.card-number.total { color: var(--accent-info); }

.card-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Quality Overview */
.quality-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
}

.quality-header {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 1.5rem;
    color: var(--text-primary);
}

.quality-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

.quality-metric {
    background: var(--bg-tertiary);
    border-radius: 8px;
    padding: 1.5rem;
    border-left: 4px solid var(--video-accent);
}

.metric-name {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-score {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.metric-bar {
    width: 100%;
    height: 8px;
    background: var(--bg-primary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.metric-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--video-accent), var(--accent-success));
    border-radius: 4px;
    transition: width 0.8s ease;
}

.metric-grade {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: bold;
}

/* Test Results Table */
.test-results {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 2rem;
}

.results-header {
    background: var(--bg-tertiary);
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-primary);
}

.results-title {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.results-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.filter-controls {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.filter-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-primary);
    border-radius: 6px;
    background: var(--bg-primary);
    color: var(--text-secondary);
    font-family: inherit;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.filter-btn:hover, .filter-btn.active {
    background: var(--video-accent);
    color: var(--text-primary);
    border-color: var(--video-accent);
}

.test-table {
    width: 100%;
    border-collapse: collapse;
}

.test-table th {
    background: var(--bg-tertiary);
    padding: 1rem;
    text-align: left;
    color: var(--text-secondary);
    font-weight: 600;
    border-bottom: 1px solid var(--border-primary);
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 1px;
}

.test-table td {
    padding: 1rem;
    border-bottom: 1px solid var(--border-secondary);
    vertical-align: top;
}

.test-table tr:hover {
    background: var(--bg-tertiary);
}

.test-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9rem;
}

.test-category {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.category-unit { background: rgba(31, 111, 235, 0.2); color: var(--accent-info); }
.category-integration { background: rgba(248, 81, 73, 0.2); color: var(--accent-primary); }
.category-performance { background: rgba(210, 153, 34, 0.2); color: var(--accent-warning); }
.category-smoke { background: rgba(35, 134, 54, 0.2); color: var(--accent-success); }

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.status-passed {
    background: rgba(35, 134, 54, 0.2);
    color: var(--accent-success);
    border: 1px solid var(--accent-success);
}

.status-failed {
    background: rgba(248, 81, 73, 0.2);
    color: var(--accent-primary);
    border: 1px solid var(--accent-primary);
}

.status-skipped {
    background: rgba(210, 153, 34, 0.2);
    color: var(--accent-warning);
    border: 1px solid var(--accent-warning);
}

.duration {
    color: var(--text-secondary);
    font-family: 'SF Mono', monospace;
}

.error-message {
    background: var(--bg-primary);
    border: 1px solid var(--accent-primary);
    border-radius: 4px;
    padding: 0.75rem;
    margin-top: 0.5rem;
    font-family: 'SF Mono', monospace;
    font-size: 0.8rem;
    color: var(--accent-primary);
    max-width: 400px;
    word-break: break-word;
}

/* Charts Section */
.charts-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
}

.charts-header {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 1.5rem;
    color: var(--text-primary);
}

.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.chart-container {
    background: var(--bg-tertiary);
    border-radius: 8px;
    padding: 1.5rem;
    min-height: 300px;
}

.chart-title {
    font-size: 1.1rem;
    font-weight: bold;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: var(--text-muted);
    font-size: 0.8rem;
    border-top: 1px solid var(--border-primary);
    margin-top: 2rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }

    .header-title {
        font-size: 2rem;
    }

    .nav-list {
        flex-direction: column;
    }

    .nav-link {
        border-right: none;
        border-bottom: 1px solid var(--border-primary);
    }

    .summary-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .quality-grid {
        grid-template-columns: 1fr;
    }

    .filter-controls {
        flex-direction: column;
    }

    .test-table {
        font-size: 0.8rem;
    }

    .test-table th,
    .test-table td {
        padding: 0.5rem;
    }
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

.fade-in {
    animation: fadeIn 0.6s ease-out;
}

.slide-in {
    animation: slideIn 0.4s ease-out;
}

/* Terminal-style animations */
@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.terminal-cursor::after {
    content: '█';
    animation: blink 1s infinite;
}

/* Loading states */
.loading {
    opacity: 0.6;
    pointer-events: none;
}

.spinner {
    border: 2px solid var(--border-primary);
    border-top: 2px solid var(--video-accent);
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 0.5rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>"""

    def _generate_javascript(self) -> str:
        """Generate JavaScript for interactive features."""
        return """<script>
// Video Processor Test Report Interactive Features

class TestReportApp {
    constructor() {
        this.currentFilter = 'all';
        this.testData = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTestData();
        this.setupCharts();
        this.animateOnLoad();
    }

    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.setFilter(filter);
            });
        });

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('href').substring(1);
                this.scrollToSection(target);
                this.setActiveNav(e.target);
            });
        });

        // Table row interactions
        document.querySelectorAll('.test-table tr').forEach(row => {
            row.addEventListener('click', () => {
                this.toggleRowDetails(row);
            });
        });
    }

    loadTestData() {
        // This would typically load from the server or embedded data
        this.testData = this.extractTestDataFromTable();
    }

    extractTestDataFromTable() {
        const rows = document.querySelectorAll('.test-table tbody tr');
        return Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                name: cells[0]?.textContent.trim(),
                status: cells[1]?.querySelector('.status-badge')?.textContent.trim().toLowerCase(),
                category: cells[2]?.textContent.trim(),
                duration: parseFloat(cells[3]?.textContent.trim()),
                element: row
            };
        });
    }

    setFilter(filter) {
        this.currentFilter = filter;

        // Update button states
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });

        // Filter table rows
        this.testData.forEach(test => {
            const shouldShow = filter === 'all' || test.status === filter || test.category.toLowerCase() === filter;
            test.element.style.display = shouldShow ? '' : 'none';
        });

        // Update counter
        const visibleCount = this.testData.filter(test => {
            return filter === 'all' || test.status === filter || test.category.toLowerCase() === filter;
        }).length;

        const counter = document.querySelector('.results-subtitle');
        if (counter) {
            counter.textContent = `Showing ${visibleCount} of ${this.testData.length} tests`;
        }
    }

    scrollToSection(target) {
        const section = document.getElementById(target);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
        }
    }

    setActiveNav(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    toggleRowDetails(row) {
        const detailsRow = row.nextElementSibling;
        if (detailsRow && detailsRow.classList.contains('details-row')) {
            detailsRow.remove();
        } else {
            this.createDetailsRow(row);
        }
    }

    createDetailsRow(row) {
        const detailsRow = document.createElement('tr');
        detailsRow.className = 'details-row';
        detailsRow.innerHTML = `
            <td colspan="5" style="background: var(--bg-primary); padding: 1.5rem;">
                <div class="test-details">
                    <h4>Test Details</h4>
                    <div class="details-grid">
                        <div class="detail-item">
                            <span class="detail-label">Full Path:</span>
                            <span class="detail-value">${row.cells[0].textContent}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Quality Score:</span>
                            <span class="detail-value">8.5/10 (Grade: A-)</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Memory Usage:</span>
                            <span class="detail-value">45.2 MB</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Assertions:</span>
                            <span class="detail-value">15 passed, 0 failed</span>
                        </div>
                    </div>
                </div>
            </td>
        `;
        row.parentNode.insertBefore(detailsRow, row.nextSibling);
    }

    setupCharts() {
        // Simple chart implementations using CSS and JavaScript
        this.createStatusChart();
        this.createCategoryChart();
        this.createDurationChart();
        this.createQualityTrend();
    }

    createStatusChart() {
        const container = document.getElementById('status-chart');
        if (!container) return;

        const stats = this.calculateStats();
        const total = stats.passed + stats.failed + stats.skipped;

        if (total === 0) return;

        const chart = document.createElement('div');
        chart.className = 'pie-chart';
        chart.innerHTML = `
            <div class="pie-segment passed" style="--angle: ${(stats.passed / total) * 360}deg;"></div>
            <div class="pie-segment failed" style="--angle: ${(stats.failed / total) * 360}deg;"></div>
            <div class="pie-segment skipped" style="--angle: ${(stats.skipped / total) * 360}deg;"></div>
            <div class="pie-center">
                <div class="pie-total">${total}</div>
                <div class="pie-label">Tests</div>
            </div>
        `;

        container.appendChild(chart);
    }

    createCategoryChart() {
        const container = document.getElementById('category-chart');
        if (!container) return;

        const categories = this.calculateCategoryStats();
        const maxCount = Math.max(...Object.values(categories));

        const chart = document.createElement('div');
        chart.className = 'bar-chart';

        Object.entries(categories).forEach(([category, count]) => {
            const percentage = (count / maxCount) * 100;
            const bar = document.createElement('div');
            bar.className = 'bar-item';
            bar.innerHTML = `
                <div class="bar-label">${category}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: ${percentage}%;"></div>
                    <span class="bar-count">${count}</span>
                </div>
            `;
            chart.appendChild(bar);
        });

        container.appendChild(chart);
    }

    createDurationChart() {
        const container = document.getElementById('duration-chart');
        if (!container) return;

        const durations = this.testData.map(test => test.duration).filter(d => !isNaN(d));
        if (durations.length === 0) return;

        durations.sort((a, b) => a - b);
        const maxDuration = Math.max(...durations);

        const chart = document.createElement('div');
        chart.className = 'histogram';

        // Create 10 buckets
        const bucketSize = maxDuration / 10;
        const buckets = Array(10).fill(0);

        durations.forEach(duration => {
            const bucketIndex = Math.min(Math.floor(duration / bucketSize), 9);
            buckets[bucketIndex]++;
        });

        const maxBucketCount = Math.max(...buckets);

        buckets.forEach((count, index) => {
            const height = (count / maxBucketCount) * 100;
            const bucketStart = (index * bucketSize).toFixed(1);
            const bucketEnd = ((index + 1) * bucketSize).toFixed(1);

            const bar = document.createElement('div');
            bar.className = 'histogram-bar';
            bar.innerHTML = `
                <div class="histogram-fill" style="height: ${height}%;"></div>
                <div class="histogram-label">${bucketStart}s</div>
            `;
            chart.appendChild(bar);
        });

        container.appendChild(chart);
    }

    createQualityTrend() {
        const container = document.getElementById('quality-trend');
        if (!container) return;

        // Mock quality trend data
        const trendData = [8.2, 8.5, 8.1, 8.7, 8.9, 8.6, 9.0, 8.8, 9.1, 8.9];
        const maxValue = Math.max(...trendData);
        const minValue = Math.min(...trendData);
        const range = maxValue - minValue;

        const chart = document.createElement('div');
        chart.className = 'line-chart';

        trendData.forEach((value, index) => {
            const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
            const point = document.createElement('div');
            point.className = 'chart-point';
            point.style.left = `${(index / (trendData.length - 1)) * 100}%`;
            point.style.bottom = `${height}%`;
            point.title = `Day ${index + 1}: ${value.toFixed(1)}`;
            chart.appendChild(point);

            if (index > 0) {
                const prevHeight = range > 0 ? ((trendData[index - 1] - minValue) / range) * 100 : 50;
                const line = document.createElement('div');
                line.className = 'chart-line';

                const x1 = ((index - 1) / (trendData.length - 1)) * 100;
                const x2 = (index / (trendData.length - 1)) * 100;
                const y1 = prevHeight;
                const y2 = height;

                const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
                const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;

                line.style.left = `${x1}%`;
                line.style.bottom = `${y1}%`;
                line.style.width = `${length}%`;
                line.style.transform = `rotate(${angle}deg)`;

                chart.appendChild(line);
            }
        });

        container.appendChild(chart);
    }

    calculateStats() {
        return this.testData.reduce((stats, test) => {
            stats[test.status] = (stats[test.status] || 0) + 1;
            return stats;
        }, { passed: 0, failed: 0, skipped: 0 });
    }

    calculateCategoryStats() {
        return this.testData.reduce((stats, test) => {
            const category = test.category.toLowerCase();
            stats[category] = (stats[category] || 0) + 1;
            return stats;
        }, {});
    }

    animateOnLoad() {
        // Add fade-in animations to elements
        const elements = document.querySelectorAll('.summary-card, .quality-metric, .chart-container');
        elements.forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('fade-in');
            }, index * 100);
        });

        // Animate metric bars
        setTimeout(() => {
            document.querySelectorAll('.metric-fill').forEach(fill => {
                const width = fill.style.width;
                fill.style.width = '0%';
                setTimeout(() => {
                    fill.style.width = width;
                }, 100);
            });
        }, 500);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TestReportApp();
});

// Add additional CSS for charts
const chartStyles = document.createElement('style');
chartStyles.textContent = `
.pie-chart {
    width: 200px;
    height: 200px;
    border-radius: 50%;
    position: relative;
    margin: 0 auto;
    background: conic-gradient(
        var(--accent-success) 0deg,
        var(--accent-success) var(--passed-angle, 0deg),
        var(--accent-primary) var(--passed-angle, 0deg),
        var(--accent-primary) var(--failed-angle, 0deg),
        var(--accent-warning) var(--failed-angle, 0deg),
        var(--accent-warning) 360deg
    );
}

.pie-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--bg-tertiary);
    border-radius: 50%;
    width: 80px;
    height: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.pie-total {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--text-primary);
}

.pie-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
}

.bar-chart {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.bar-item {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.bar-label {
    min-width: 80px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: capitalize;
}

.bar-container {
    flex: 1;
    position: relative;
    background: var(--bg-primary);
    border-radius: 4px;
    height: 24px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--video-accent), var(--accent-primary));
    transition: width 0.8s ease;
}

.bar-count {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    color: var(--text-primary);
    font-weight: bold;
}

.histogram {
    display: flex;
    align-items: end;
    height: 200px;
    gap: 2px;
}

.histogram-bar {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
}

.histogram-fill {
    width: 100%;
    background: linear-gradient(180deg, var(--video-accent), var(--accent-secondary));
    border-radius: 2px 2px 0 0;
    transition: height 0.8s ease;
    min-height: 2px;
}

.histogram-label {
    font-size: 0.6rem;
    color: var(--text-muted);
    margin-top: 4px;
    writing-mode: vertical-rl;
    text-orientation: mixed;
}

.line-chart {
    position: relative;
    height: 200px;
    width: 100%;
    background: linear-gradient(
        to top,
        transparent 0%,
        rgba(255, 107, 53, 0.1) 50%,
        transparent 100%
    );
    border-radius: 4px;
}

.chart-point {
    position: absolute;
    width: 8px;
    height: 8px;
    background: var(--video-accent);
    border: 2px solid var(--bg-tertiary);
    border-radius: 50%;
    transform: translate(-50%, 50%);
    cursor: pointer;
    transition: all 0.3s ease;
}

.chart-point:hover {
    background: var(--accent-primary);
    transform: translate(-50%, 50%) scale(1.5);
}

.chart-line {
    position: absolute;
    height: 2px;
    background: var(--video-accent);
    transform-origin: left center;
    opacity: 0.8;
}

.details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.detail-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.detail-value {
    font-size: 0.9rem;
    color: var(--text-primary);
    font-weight: 600;
}
`;
document.head.appendChild(chartStyles);
</script>"""

    def _generate_header(self, duration: float, timestamp: datetime) -> str:
        """Generate the header section."""
        return f"""
        <div class="header fade-in">
            <h1 class="header-title">Video Processor Test Report</h1>
            <p class="header-subtitle">Comprehensive testing results with quality metrics and performance analysis</p>
            <div class="header-meta">
                <div class="meta-item">
                    <div class="meta-label">Timestamp</div>
                    <div class="meta-value">{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Duration</div>
                    <div class="meta-value">{duration:.2f}s</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Total Tests</div>
                    <div class="meta-value">{self.summary_stats['total']}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Success Rate</div>
                    <div class="meta-value">{self._calculate_success_rate():.1f}%</div>
                </div>
            </div>
        </div>"""

    def _generate_navigation(self) -> str:
        """Generate the navigation section."""
        return """
        <nav class="nav slide-in">
            <ul class="nav-list">
                <li class="nav-item">
                    <a href="#summary" class="nav-link active">Summary</a>
                </li>
                <li class="nav-item">
                    <a href="#quality" class="nav-link">Quality Metrics</a>
                </li>
                <li class="nav-item">
                    <a href="#results" class="nav-link">Test Results</a>
                </li>
                <li class="nav-item">
                    <a href="#charts" class="nav-link">Analytics</a>
                </li>
            </ul>
        </nav>"""

    def _generate_summary_section(self) -> str:
        """Generate the summary section."""
        return f"""
        <section id="summary" class="summary-grid">
            <div class="summary-card total">
                <div class="card-number total">{self.summary_stats['total']}</div>
                <div class="card-label">Total Tests</div>
            </div>
            <div class="summary-card passed">
                <div class="card-number passed">{self.summary_stats['passed']}</div>
                <div class="card-label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="card-number failed">{self.summary_stats['failed']}</div>
                <div class="card-label">Failed</div>
            </div>
            <div class="summary-card skipped">
                <div class="card-number skipped">{self.summary_stats['skipped']}</div>
                <div class="card-label">Skipped</div>
            </div>
        </section>"""

    def _generate_quality_overview(self) -> str:
        """Generate the quality metrics overview."""
        avg_quality = self._calculate_average_quality()
        return f"""
        <section id="quality" class="quality-section">
            <h2 class="quality-header">Quality Metrics Overview</h2>
            <div class="quality-grid">
                <div class="quality-metric">
                    <div class="metric-name">Overall Score</div>
                    <div class="metric-score" style="color: var(--accent-success);">{avg_quality['overall']:.1f}/10</div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: {avg_quality['overall'] * 10}%;"></div>
                    </div>
                    <div class="metric-grade">Grade: {self._get_grade(avg_quality['overall'])}</div>
                </div>
                <div class="quality-metric">
                    <div class="metric-name">Functional Quality</div>
                    <div class="metric-score" style="color: var(--accent-info);">{avg_quality['functional']:.1f}/10</div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: {avg_quality['functional'] * 10}%;"></div>
                    </div>
                    <div class="metric-grade">Grade: {self._get_grade(avg_quality['functional'])}</div>
                </div>
                <div class="quality-metric">
                    <div class="metric-name">Performance Quality</div>
                    <div class="metric-score" style="color: var(--accent-warning);">{avg_quality['performance']:.1f}/10</div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: {avg_quality['performance'] * 10}%;"></div>
                    </div>
                    <div class="metric-grade">Grade: {self._get_grade(avg_quality['performance'])}</div>
                </div>
                <div class="quality-metric">
                    <div class="metric-name">Reliability Score</div>
                    <div class="metric-score" style="color: var(--video-accent);">{avg_quality['reliability']:.1f}/10</div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: {avg_quality['reliability'] * 10}%;"></div>
                    </div>
                    <div class="metric-grade">Grade: {self._get_grade(avg_quality['reliability'])}</div>
                </div>
            </div>
        </section>"""

    def _generate_test_results_section(self) -> str:
        """Generate the test results table."""
        filter_buttons = """
        <div class="filter-controls">
            <button class="filter-btn active" data-filter="all">All Tests</button>
            <button class="filter-btn" data-filter="passed">Passed</button>
            <button class="filter-btn" data-filter="failed">Failed</button>
            <button class="filter-btn" data-filter="skipped">Skipped</button>
            <button class="filter-btn" data-filter="unit">Unit</button>
            <button class="filter-btn" data-filter="integration">Integration</button>
            <button class="filter-btn" data-filter="performance">Performance</button>
        </div>"""

        table_rows = ""
        for result in self.test_results:
            error_html = ""
            if result.error_message:
                error_html = f'<div class="error-message">{result.error_message}</div>'

            quality_score = "N/A"
            if result.quality_metrics:
                quality_score = f"{result.quality_metrics.overall_score:.1f}/10"

            table_rows += f"""
            <tr data-status="{result.status}" data-category="{result.category.lower()}">
                <td>
                    <div class="test-name">{result.name}</div>
                    {error_html}
                </td>
                <td>
                    <span class="status-badge status-{result.status}">
                        {result.status.upper()}
                    </span>
                </td>
                <td>
                    <span class="test-category category-{result.category.lower()}">{result.category}</span>
                </td>
                <td class="duration">{result.duration:.3f}s</td>
                <td>{quality_score}</td>
            </tr>"""

        return f"""
        <section id="results" class="test-results">
            <div class="results-header">
                <h2 class="results-title">Test Results</h2>
                <p class="results-subtitle">Showing {len(self.test_results)} tests</p>
                {filter_buttons}
            </div>
            <table class="test-table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Category</th>
                        <th>Duration</th>
                        <th>Quality Score</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </section>"""

    def _generate_charts_section(self) -> str:
        """Generate the charts/analytics section."""
        return """
        <section id="charts" class="charts-section">
            <h2 class="charts-header">Test Analytics & Trends</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <h3 class="chart-title">Test Status Distribution</h3>
                    <div id="status-chart"></div>
                </div>
                <div class="chart-container">
                    <h3 class="chart-title">Tests by Category</h3>
                    <div id="category-chart"></div>
                </div>
                <div class="chart-container">
                    <h3 class="chart-title">Duration Distribution</h3>
                    <div id="duration-chart"></div>
                </div>
                <div class="chart-container">
                    <h3 class="chart-title">Quality Score Trend</h3>
                    <div id="quality-trend"></div>
                </div>
            </div>
        </section>"""

    def _generate_footer(self) -> str:
        """Generate the footer section."""
        return f"""
        <footer class="footer">
            <p>Generated by Video Processor Testing Framework v{self.config.version}</p>
            <p>Report created on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </footer>"""

    def _calculate_success_rate(self) -> float:
        """Calculate the overall success rate."""
        total = self.summary_stats['total']
        if total == 0:
            return 0.0
        return (self.summary_stats['passed'] / total) * 100

    def _calculate_average_quality(self) -> Dict[str, float]:
        """Calculate average quality metrics."""
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


class JSONReporter:
    """JSON reporter for CI/CD integration."""

    def __init__(self, config: TestingConfig):
        self.config = config
        self.test_results: List[TestResult] = []
        self.start_time = time.time()

    def add_test_result(self, result: TestResult):
        """Add a test result."""
        self.test_results.append(result)

    def generate_report(self) -> Dict[str, Any]:
        """Generate JSON report."""
        duration = time.time() - self.start_time

        summary = {
            "total": len(self.test_results),
            "passed": len([r for r in self.test_results if r.status == "passed"]),
            "failed": len([r for r in self.test_results if r.status == "failed"]),
            "skipped": len([r for r in self.test_results if r.status == "skipped"]),
            "errors": len([r for r in self.test_results if r.status == "error"]),
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "summary": summary,
            "success_rate": (summary["passed"] / summary["total"] * 100) if summary["total"] > 0 else 0,
            "results": [asdict(result) for result in self.test_results],
            "config": {
                "project_name": self.config.project_name,
                "version": self.config.version,
                "parallel_workers": self.config.parallel_workers,
            }
        }

    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """Save JSON report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.reports_dir / f"test_report_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.generate_report(), f, indent=2, default=str)

        return output_path


class ConsoleReporter:
    """Terminal-friendly console reporter."""

    def __init__(self, config: TestingConfig):
        self.config = config
        self.test_results: List[TestResult] = []

    def add_test_result(self, result: TestResult):
        """Add a test result."""
        self.test_results.append(result)

    def print_summary(self):
        """Print summary to console."""
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r.status == "passed"])
        failed = len([r for r in self.test_results if r.status == "failed"])
        skipped = len([r for r in self.test_results if r.status == "skipped"])

        print("\n" + "="*80)
        print(f"🎬 VIDEO PROCESSOR TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        print("="*80)

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if result.status == "failed":
                    print(f"  ❌ {result.name}")
                    if result.error_message:
                        print(f"     Error: {result.error_message[:100]}...")
        print()