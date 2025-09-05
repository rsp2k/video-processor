#!/bin/bash

# Integration Test Runner Script
# Runs comprehensive end-to-end tests in Docker environment

set -euo pipefail

# Configuration
PROJECT_NAME="video-processor-integration"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Video Processor Integration Test Runner

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Run tests with verbose output
    -f, --fast          Run tests with minimal setup (skip some slow tests)
    -c, --clean         Clean up containers and volumes before running
    -k, --keep          Keep containers running after tests (for debugging)
    --test-filter       Pytest filter expression (e.g. "test_video_processing")
    --timeout           Timeout for tests in seconds (default: 300)

EXAMPLES:
    $0                                  # Run all integration tests
    $0 -v                              # Verbose output
    $0 -c                              # Clean start
    $0 --test-filter "test_worker"     # Run only worker tests
    $0 -k                              # Keep containers for debugging

EOF
}

# Parse command line arguments
VERBOSE=false
CLEAN=false
KEEP_CONTAINERS=false
FAST_MODE=false
TEST_FILTER=""
TIMEOUT=300

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fast)
            FAST_MODE=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -k|--keep)
            KEEP_CONTAINERS=true
            shift
            ;;
        --test-filter)
            TEST_FILTER="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "All dependencies available"
}

# Cleanup function
cleanup() {
    if [ "$KEEP_CONTAINERS" = false ]; then
        log_info "Cleaning up containers and volumes..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" down -v --remove-orphans || true
        log_success "Cleanup completed"
    else
        log_warning "Keeping containers running for debugging"
        log_info "To manually cleanup later, run:"
        log_info "  docker-compose -f docker-compose.integration.yml -p $PROJECT_NAME down -v"
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main test execution
run_integration_tests() {
    cd "$PROJECT_ROOT"
    
    log_info "Starting integration tests for Video Processor"
    log_info "Project: $PROJECT_NAME"
    log_info "Timeout: ${TIMEOUT}s"
    
    # Clean up if requested
    if [ "$CLEAN" = true ]; then
        log_info "Performing clean start..."
        docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" down -v --remove-orphans || true
    fi
    
    # Build pytest arguments
    PYTEST_ARGS="-v --tb=short --durations=10"
    
    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -s"
    fi
    
    if [ "$FAST_MODE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
    fi
    
    if [ -n "$TEST_FILTER" ]; then
        PYTEST_ARGS="$PYTEST_ARGS -k '$TEST_FILTER'"
    fi
    
    # Set environment variables
    export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
    export PYTEST_ARGS="$PYTEST_ARGS"
    
    log_info "Building containers..."
    docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" build
    
    log_info "Starting services..."
    docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" up -d postgres-integration
    
    log_info "Waiting for database to be ready..."
    timeout 30 bash -c 'until docker-compose -f docker-compose.integration.yml -p '"$PROJECT_NAME"' exec -T postgres-integration pg_isready -U video_user; do sleep 1; done'
    
    log_info "Running database migration..."
    docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" run --rm migrate-integration
    
    log_info "Starting worker..."
    docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" up -d worker-integration
    
    log_info "Running integration tests..."
    log_info "Test command: pytest $PYTEST_ARGS"
    
    # Run the tests with timeout
    if timeout "$TIMEOUT" docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" run --rm integration-tests; then
        log_success "All integration tests passed! ✅"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "Tests timed out after ${TIMEOUT} seconds"
        else
            log_error "Integration tests failed with exit code $exit_code"
        fi
        
        # Show logs for debugging
        log_warning "Showing service logs for debugging..."
        docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" logs --tail=50
        
        return $exit_code
    fi
}

# Generate test report
generate_report() {
    log_info "Generating test report..."
    
    # Get container logs
    local log_dir="$PROJECT_ROOT/test-reports"
    mkdir -p "$log_dir"
    
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.integration.yml -p "$PROJECT_NAME" logs > "$log_dir/integration-test-logs.txt" 2>&1 || true
    
    log_success "Test logs saved to: $log_dir/integration-test-logs.txt"
}

# Main execution
main() {
    log_info "Video Processor Integration Test Runner"
    log_info "========================================"
    
    check_dependencies
    
    # Run tests
    if run_integration_tests; then
        log_success "Integration tests completed successfully!"
        generate_report
        exit 0
    else
        log_error "Integration tests failed!"
        generate_report
        exit 1
    fi
}

# Run main function
main "$@"