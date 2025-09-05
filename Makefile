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
	@echo "Testing:"
	@echo "  test             Run unit tests only"
	@echo "  test-unit        Run unit tests with coverage"
	@echo "  test-integration Run Docker integration tests"
	@echo "  test-all         Run all tests (unit + integration)"
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

# Testing targets
test: test-unit

test-unit:
	uv run pytest tests/ -x -v --tb=short --cov=src/ --cov-report=html --cov-report=term

test-integration:
	./scripts/run-integration-tests.sh

test-integration-verbose:
	./scripts/run-integration-tests.sh --verbose

test-integration-fast:
	./scripts/run-integration-tests.sh --fast

test-all: test-unit test-integration

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
	docker-compose -f docker-compose.integration.yml build
	./scripts/run-integration-tests.sh --clean

docker-demo:
	docker-compose up -d postgres
	docker-compose run --rm migrate
	docker-compose up -d worker
	docker-compose up demo

docker-clean:
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.integration.yml down -v --remove-orphans
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