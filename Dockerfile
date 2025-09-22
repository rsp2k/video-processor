# Video Processor Dockerfile with uv caching optimization
# Based on uv Docker integration best practices
# https://docs.astral.sh/uv/guides/integration/docker/

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create app directory
WORKDIR /app

# Create user for running the application
RUN groupadd -r app && useradd -r -g app app

# Change to app user for dependency installation
USER app

# Copy dependency files first for better caching
COPY --chown=app:app pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
# This layer will be cached if dependencies don't change
ENV UV_SYSTEM_PYTHON=1
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=app:app . .

# Install the application
RUN uv pip install -e .

# Production stage
FROM base as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from video_processor import VideoProcessor; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "video_processor.tasks.procrastinate_tasks"]

# Development stage with dev dependencies
FROM base as development

# Install development dependencies
RUN uv sync --frozen

# Install pre-commit hooks
RUN uv run pre-commit install || true

# Set development environment
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# Default command for development
CMD ["bash"]

# Worker stage for Procrastinate workers  
FROM production as worker

# Set worker-specific environment
ENV PROCRASTINATE_WORKER=1

# Command to run Procrastinate worker
CMD ["python", "-m", "video_processor.tasks.worker_compatibility", "worker"]

# Migration stage for database migrations
FROM production as migration

# Command to run migrations
CMD ["python", "-m", "video_processor.tasks.migration"]