"""
Pytest configuration and fixtures for Docker integration tests.
"""

import asyncio
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import docker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from video_processor.tasks.compat import get_version_info


@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Docker client for managing containers and services."""
    return docker.from_env()


@pytest.fixture(scope="session") 
def temp_video_dir() -> Generator[Path, None, None]:
    """Temporary directory for test video files."""
    with tempfile.TemporaryDirectory(prefix="video_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def test_video_file(temp_video_dir: Path) -> Path:
    """Create a test video file for processing."""
    video_file = temp_video_dir / "test_input.mp4"
    
    # Create a simple test video using FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=10:size=640x480:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        str(video_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        assert video_file.exists(), "Test video file was not created"
        return video_file
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.skip(f"FFmpeg not available or failed: {e}")


@pytest.fixture(scope="session")
def docker_compose_project(docker_client: docker.DockerClient) -> Generator[str, None, None]:
    """Start Docker Compose services for testing."""
    project_root = Path(__file__).parent.parent.parent
    project_name = "video-processor-integration-test"
    
    # Environment variables for test database
    test_env = os.environ.copy()
    test_env.update({
        "COMPOSE_PROJECT_NAME": project_name,
        "POSTGRES_DB": "video_processor_integration_test",
        "DATABASE_URL": "postgresql://video_user:video_password@postgres:5432/video_processor_integration_test",
        "PROCRASTINATE_DATABASE_URL": "postgresql://video_user:video_password@postgres:5432/video_processor_integration_test"
    })
    
    # Start services
    print(f"\n🐳 Starting Docker Compose services for integration tests...")
    
    # First, ensure we're in a clean state
    subprocess.run([
        "docker-compose", "-p", project_name, "down", "-v", "--remove-orphans"
    ], cwd=project_root, env=test_env, capture_output=True)
    
    try:
        # Start core services (postgres first)
        subprocess.run([
            "docker-compose", "-p", project_name, "up", "-d", "postgres"
        ], cwd=project_root, env=test_env, check=True)
        
        # Wait for postgres to be healthy
        _wait_for_postgres_health(docker_client, project_name)
        
        # Run database migration
        subprocess.run([
            "docker-compose", "-p", project_name, "run", "--rm", "migrate"
        ], cwd=project_root, env=test_env, check=True)
        
        # Start worker service
        subprocess.run([
            "docker-compose", "-p", project_name, "up", "-d", "worker"
        ], cwd=project_root, env=test_env, check=True)
        
        # Wait a moment for services to fully start
        time.sleep(5)
        
        print("✅ Docker Compose services started successfully")
        yield project_name
        
    finally:
        print("\n🧹 Cleaning up Docker Compose services...")
        subprocess.run([
            "docker-compose", "-p", project_name, "down", "-v", "--remove-orphans"
        ], cwd=project_root, env=test_env, capture_output=True)
        print("✅ Cleanup completed")


def _wait_for_postgres_health(client: docker.DockerClient, project_name: str, timeout: int = 30) -> None:
    """Wait for PostgreSQL container to be healthy."""
    container_name = f"{project_name}-postgres-1"
    
    print(f"⏳ Waiting for PostgreSQL container {container_name} to be healthy...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            container = client.containers.get(container_name)
            health = container.attrs["State"]["Health"]["Status"]
            if health == "healthy":
                print("✅ PostgreSQL is healthy")
                return
            print(f"   Health status: {health}")
        except docker.errors.NotFound:
            print(f"   Container {container_name} not found yet...")
        except KeyError:
            print("   No health check status available yet...")
        
        time.sleep(2)
    
    raise TimeoutError(f"PostgreSQL container did not become healthy within {timeout} seconds")


@pytest.fixture(scope="session")
def postgres_connection(docker_compose_project: str) -> Generator[Dict[str, Any], None, None]:
    """PostgreSQL connection parameters for testing."""
    conn_params = {
        "host": "localhost",
        "port": 5432,
        "user": "video_user", 
        "password": "video_password",
        "database": "video_processor_integration_test"
    }
    
    # Test connection
    print("🔌 Testing PostgreSQL connection...")
    max_retries = 10
    for i in range(max_retries):
        try:
            with psycopg2.connect(**conn_params) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    print(f"✅ Connected to PostgreSQL: {version}")
                    break
        except psycopg2.OperationalError as e:
            if i == max_retries - 1:
                raise ConnectionError(f"Could not connect to PostgreSQL after {max_retries} attempts: {e}")
            print(f"   Attempt {i+1}/{max_retries} failed, retrying in 2s...")
            time.sleep(2)
    
    yield conn_params


@pytest.fixture
def procrastinate_app(postgres_connection: Dict[str, Any]):
    """Set up Procrastinate app for testing."""
    from video_processor.tasks import setup_procrastinate
    
    db_url = (
        f"postgresql://{postgres_connection['user']}:"
        f"{postgres_connection['password']}@"
        f"{postgres_connection['host']}:{postgres_connection['port']}/"
        f"{postgres_connection['database']}"
    )
    
    app = setup_procrastinate(db_url)
    print(f"✅ Procrastinate app initialized with {get_version_info()['procrastinate_version']}")
    return app


@pytest.fixture
def clean_database(postgres_connection: Dict[str, Any]):
    """Ensure clean database state for each test."""
    print("🧹 Cleaning database state for test...")
    
    with psycopg2.connect(**postgres_connection) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            # Clean up any existing jobs
            cursor.execute("""
                DELETE FROM procrastinate_jobs WHERE 1=1;
                DELETE FROM procrastinate_events WHERE 1=1;
            """)
    
    yield
    
    # Cleanup after test
    with psycopg2.connect(**postgres_connection) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM procrastinate_jobs WHERE 1=1;
                DELETE FROM procrastinate_events WHERE 1=1;
            """)


# Async event loop fixture for async tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()