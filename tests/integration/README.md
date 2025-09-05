# Integration Tests

This directory contains end-to-end integration tests that verify the complete Video Processor system in a Docker environment.

## Overview

The integration tests validate:

- **Complete video processing pipeline** - encoding, thumbnails, sprites
- **Procrastinate worker functionality** - async job processing and queue management  
- **Database migration system** - schema creation and version compatibility
- **Docker containerization** - multi-service orchestration
- **Error handling and edge cases** - real-world failure scenarios

## Test Architecture

### Test Structure

```
tests/integration/
├── conftest.py                           # Pytest fixtures and Docker setup
├── test_video_processing_e2e.py          # Video processing pipeline tests
├── test_procrastinate_worker_e2e.py      # Worker and job queue tests
├── test_database_migration_e2e.py        # Database migration tests
└── README.md                             # This file
```

### Docker Services

The tests use a dedicated Docker Compose configuration (`docker-compose.integration.yml`) with:

- **postgres-integration** - PostgreSQL database on port 5433
- **migrate-integration** - Runs database migrations
- **worker-integration** - Procrastinate background worker  
- **integration-tests** - Test runner container

## Running Integration Tests

### Quick Start

```bash
# Run all integration tests
make test-integration

# Or use the script directly
./scripts/run-integration-tests.sh
```

### Advanced Options

```bash
# Verbose output
./scripts/run-integration-tests.sh --verbose

# Fast mode (skip slow tests)  
./scripts/run-integration-tests.sh --fast

# Run specific test pattern
./scripts/run-integration-tests.sh --test-filter "test_video_processing"

# Keep containers for debugging
./scripts/run-integration-tests.sh --keep

# Clean start
./scripts/run-integration-tests.sh --clean
```

### Manual Docker Setup

```bash
# Start services manually
docker-compose -f docker-compose.integration.yml up -d postgres-integration
docker-compose -f docker-compose.integration.yml run --rm migrate-integration  
docker-compose -f docker-compose.integration.yml up -d worker-integration

# Run tests
docker-compose -f docker-compose.integration.yml run --rm integration-tests

# Cleanup
docker-compose -f docker-compose.integration.yml down -v
```

## Test Categories

### Video Processing Tests (`test_video_processing_e2e.py`)

- **Synchronous processing** - Complete pipeline with multiple formats
- **Configuration validation** - Quality presets and output formats
- **Error handling** - Invalid inputs and edge cases
- **Performance testing** - Processing time validation
- **Concurrent processing** - Multiple simultaneous jobs

### Worker Integration Tests (`test_procrastinate_worker_e2e.py`) 

- **Job submission** - Async task queuing and processing
- **Worker functionality** - Background job execution
- **Error handling** - Failed job scenarios
- **Queue management** - Job status and monitoring
- **Version compatibility** - Procrastinate 2.x/3.x support

### Database Migration Tests (`test_database_migration_e2e.py`)

- **Fresh installation** - Database schema creation
- **Migration idempotency** - Safe re-runs
- **Version compatibility** - 2.x vs 3.x migration paths
- **Production workflows** - Multi-stage migrations
- **Error scenarios** - Invalid configurations

## Test Data

Tests use FFmpeg-generated test videos:
- 10-second test video (640x480, 30fps)
- Created dynamically using `testsrc` filter
- Small size for fast processing

## Dependencies

### System Requirements

- **Docker & Docker Compose** - Container orchestration
- **FFmpeg** - Video processing (system package)
- **PostgreSQL client** - Database testing utilities

### Python Dependencies

```toml
# Added to pyproject.toml [project.optional-dependencies.dev]
"pytest-asyncio>=0.21.0"    # Async test support
"docker>=6.1.0"             # Docker API client
"psycopg2-binary>=2.9.0"    # PostgreSQL adapter
```

## Debugging

### View Logs

```bash
# Show all service logs
docker-compose -f docker-compose.integration.yml logs

# Follow specific service
docker-compose -f docker-compose.integration.yml logs -f worker-integration

# Test logs are saved to test-reports/ directory
```

### Connect to Services

```bash
# Access test database
psql -h localhost -p 5433 -U video_user -d video_processor_integration_test

# Execute commands in containers
docker-compose -f docker-compose.integration.yml exec postgres-integration psql -U video_user

# Access test container
docker-compose -f docker-compose.integration.yml run --rm integration-tests bash
```

### Common Issues

**Port conflicts**: Integration tests use port 5433 to avoid conflicts with main PostgreSQL

**FFmpeg missing**: Install system FFmpeg package: `sudo apt install ffmpeg`

**Docker permissions**: Add user to docker group: `sudo usermod -aG docker $USER`

**Database connection failures**: Ensure PostgreSQL container is healthy before running tests

## CI/CD Integration

### GitHub Actions

The integration tests run automatically on:
- Push to main/develop branches
- Pull requests to main
- Daily scheduled runs (2 AM UTC)

See `.github/workflows/integration-tests.yml` for configuration.

### Test Matrix

Tests run with different configurations:
- Separate test suites (video, worker, database)
- Full integration suite  
- Performance testing (scheduled only)
- Security scanning

## Performance Benchmarks

Expected performance for test environment:
- Video processing: < 10x realtime for test videos
- Job processing: < 60 seconds for simple tasks
- Database migration: < 30 seconds
- Full test suite: < 20 minutes

## Contributing

When adding integration tests:

1. **Use fixtures** - Leverage `conftest.py` fixtures for setup
2. **Clean state** - Use `clean_database` fixture to isolate tests
3. **Descriptive names** - Use clear test method names  
4. **Proper cleanup** - Ensure resources are freed after tests
5. **Error messages** - Provide helpful assertions with context

### Test Guidelines

- Test real scenarios users will encounter
- Include both success and failure paths
- Validate outputs completely (file existence, content, metadata)
- Keep tests fast but comprehensive
- Use meaningful test data and IDs

## Troubleshooting

### Failed Tests

1. Check container logs: `./scripts/run-integration-tests.sh --verbose`
2. Verify Docker services: `docker-compose -f docker-compose.integration.yml ps`
3. Test database connection: `psql -h localhost -p 5433 -U video_user`
4. Check FFmpeg: `ffmpeg -version`

### Resource Issues

- **Out of disk space**: Run `docker system prune -af`
- **Memory issues**: Reduce `WORKER_CONCURRENCY` in docker-compose
- **Network conflicts**: Use `--clean` flag to reset network state

For more help, see the main project README or open an issue.