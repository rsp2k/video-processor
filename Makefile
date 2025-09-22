# Video Processor Development Makefile
# Simplifies common development and testing tasks

.PHONY: help install test test-unit test-integration test-all lint format type-check clean docker-build docker-test

# Default target
help:
	@echo "Video Processor Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Development:"
	@echo "  install          Install dependencies with uv"
	@echo "  install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing (Enhanced Framework):"
	@echo "  test-smoke       Run quick smoke tests (fastest)"
	@echo "  test-unit        Run unit tests with enhanced reporting"
	@echo "  test-integration Run integration tests"
	@echo "  test-performance Run performance and benchmark tests"
	@echo "  test-360         Run 360° video processing tests"
	@echo "  test-all         Run comprehensive test suite"
	@echo "  test-pattern     Run tests matching pattern (PATTERN=...)"
	@echo "  test-markers     Run tests with markers (MARKERS=...)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run ruff linting"
	@echo "  format           Format code with ruff"
	@echo "  type-check       Run mypy type checking"
	@echo "  quality          Run all quality checks (lint + format + type-check)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-test      Run tests in Docker environment"
	@echo "  docker-demo      Start demo services"
	@echo "  docker-clean     Clean up Docker containers and volumes"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up build artifacts and cache"
	@echo "  docs             Generate documentation (if applicable)"

# Development setup
install:
	uv sync

install-dev:
	uv sync --dev

# Testing targets - Enhanced with Video Processing Framework
test: test-unit

# Quick smoke tests (fastest)
test-smoke:
	python run_tests.py --smoke

# Unit tests with enhanced reporting
test-unit:
	python run_tests.py --unit

# Integration tests
test-integration:
	python run_tests.py --integration

# Performance tests
test-performance:
	python run_tests.py --performance

# 360° video processing tests
test-360:
	python run_tests.py --360

# All tests with comprehensive reporting
test-all:
	python run_tests.py --all

# Custom test patterns
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_name_pattern"; \
	else \
		python run_tests.py --pattern "$(PATTERN)"; \
	fi

# Test with custom markers
test-markers:
	@if [ -z "$(MARKERS)" ]; then \
		echo "Usage: make test-markers MARKERS='not slow'"; \
	else \
		python run_tests.py --markers "$(MARKERS)"; \
	fi

# Legacy integration test support (maintained for compatibility)
test-integration-legacy:
	./scripts/run-integration-tests.sh

test-integration-verbose:
	./scripts/run-integration-tests.sh --verbose

test-integration-fast:
	./scripts/run-integration-tests.sh --fast

# Code quality
lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy src/

quality: format lint type-check

# Docker operations
docker-build:
	docker-compose build

docker-test:
	docker-compose -f tests/docker/docker-compose.integration.yml build
	./scripts/run-integration-tests.sh --clean

docker-demo:
	docker-compose up -d postgres
	docker-compose run --rm migrate
	docker-compose up -d worker
	docker-compose up demo

docker-clean:
	docker-compose down -v --remove-orphans
	docker-compose -f tests/docker/docker-compose.integration.yml down -v --remove-orphans
	docker system prune -f

# Cleanup
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf test-reports/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# CI/CD simulation
ci-test:
	@echo "Running CI-like test suite..."
	$(MAKE) quality
	$(MAKE) test-unit
	$(MAKE) test-integration

# Development workflow helpers
dev-setup: install-dev
	@echo "Development environment ready!"
	@echo "Run 'make test' to verify installation"

# Quick development cycle
dev: format lint test-unit

# Release preparation
pre-release: clean quality test-all
	@echo "Ready for release! All tests passed and code is properly formatted."

# Documentation (placeholder for future docs)
docs:
	@echo "Documentation generation not yet implemented"

# Show current test coverage
coverage:
	uv run pytest tests/ --cov=src/ --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
	else \
		uv run pytest $(FILE) -v; \
	fi

# Run tests matching a pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_name_pattern"; \
	else \
		uv run pytest -k "$(PATTERN)" -v; \
	fi

# Development server (if web demo exists)
dev-server:
	uv run python examples/web_demo.py

# Database operations (requires running postgres)
db-migrate:
	uv run python -c "import asyncio; from video_processor.tasks.migration import migrate_database; asyncio.run(migrate_database('postgresql://video_user:video_password@localhost:5432/video_processor'))"

# Show project status
status:
	@echo "Project Status:"
	@echo "==============="
	@uv --version
	@echo ""
	@echo "Python packages:"
	@uv pip list | head -10
	@echo ""
	@echo "Docker status:"
	@docker-compose ps || echo "No containers running"