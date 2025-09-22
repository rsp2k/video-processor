"""
End-to-end integration tests for Procrastinate worker functionality in Docker environment.

These tests verify:
- Job submission and processing through Procrastinate
- Worker container functionality
- Database job queue integration
- Async task processing
- Error handling and retries
"""

import asyncio
import time
from pathlib import Path
from typing import Any

import psycopg2
import pytest

from video_processor.tasks.compat import get_version_info


class TestProcrastinateWorkerE2E:
    """End-to-end tests for Procrastinate worker integration."""

    @pytest.mark.asyncio
    async def test_async_video_processing_job_submission(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        procrastinate_app,
        clean_database: None,
    ):
        """Test submitting and tracking async video processing jobs."""
        print("\n📤 Testing async video processing job submission")

        # Prepare job parameters
        output_dir = temp_video_dir / "async_job_output"
        config_dict = {
            "base_path": str(output_dir),
            "output_formats": ["mp4"],
            "quality_preset": "low",
            "generate_thumbnails": True,
            "generate_sprites": False,
            "storage_backend": "local",
        }

        # Submit job to queue
        job = await procrastinate_app.tasks.process_video_async.defer_async(
            input_path=str(test_video_file),
            output_dir="async_test",
            config_dict=config_dict,
        )

        # Verify job was queued
        assert job.id is not None
        print(f"✅ Job submitted with ID: {job.id}")

        # Wait for job to be processed (worker should pick it up)
        max_wait = 60  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check job status in database
            job_status = await self._get_job_status(procrastinate_app, job.id)
            print(f"   Job status: {job_status}")

            if job_status in ["succeeded", "failed"]:
                break

            await asyncio.sleep(2)
        else:
            pytest.fail(f"Job {job.id} did not complete within {max_wait} seconds")

        # Verify job completed successfully
        final_status = await self._get_job_status(procrastinate_app, job.id)
        assert final_status == "succeeded", f"Job failed with status: {final_status}"

        print(f"✅ Async job completed successfully in {time.time() - start_time:.2f}s")

    @pytest.mark.asyncio
    async def test_thumbnail_generation_job(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        procrastinate_app,
        clean_database: None,
    ):
        """Test thumbnail generation as separate async job."""
        print("\n🖼️ Testing async thumbnail generation job")

        output_dir = temp_video_dir / "thumbnail_job_output"
        output_dir.mkdir(exist_ok=True)

        # Submit thumbnail job
        job = await procrastinate_app.tasks.generate_thumbnail_async.defer_async(
            video_path=str(test_video_file),
            output_dir=str(output_dir),
            timestamp=5,
            video_id="thumb_test_123",
        )

        print(f"✅ Thumbnail job submitted with ID: {job.id}")

        # Wait for completion
        await self._wait_for_job_completion(procrastinate_app, job.id)

        # Verify thumbnail was created
        expected_thumbnail = output_dir / "thumb_test_123_thumb_5.png"
        assert expected_thumbnail.exists(), f"Thumbnail not found: {expected_thumbnail}"
        assert expected_thumbnail.stat().st_size > 0, "Thumbnail file is empty"

        print("✅ Thumbnail generation job completed successfully")

    @pytest.mark.asyncio
    async def test_job_error_handling(
        self,
        docker_compose_project: str,
        temp_video_dir: Path,
        procrastinate_app,
        clean_database: None,
    ):
        """Test error handling for invalid job parameters."""
        print("\n🚫 Testing job error handling")

        # Submit job with invalid video path
        invalid_path = str(temp_video_dir / "does_not_exist.mp4")
        config_dict = {
            "base_path": str(temp_video_dir / "error_test"),
            "output_formats": ["mp4"],
            "quality_preset": "low",
        }

        job = await procrastinate_app.tasks.process_video_async.defer_async(
            input_path=invalid_path, output_dir="error_test", config_dict=config_dict
        )

        print(f"✅ Error job submitted with ID: {job.id}")

        # Wait for job to fail
        await self._wait_for_job_completion(
            procrastinate_app, job.id, expected_status="failed"
        )

        # Verify job failed appropriately
        final_status = await self._get_job_status(procrastinate_app, job.id)
        assert final_status == "failed", f"Expected job to fail, got: {final_status}"

        print("✅ Error handling test completed")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_jobs(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        procrastinate_app,
        clean_database: None,
    ):
        """Test processing multiple jobs concurrently."""
        print("\n🔄 Testing multiple concurrent jobs")

        num_jobs = 3
        jobs = []

        # Submit multiple jobs
        for i in range(num_jobs):
            output_dir = temp_video_dir / f"concurrent_job_{i}"
            config_dict = {
                "base_path": str(output_dir),
                "output_formats": ["mp4"],
                "quality_preset": "low",
                "generate_thumbnails": False,
                "generate_sprites": False,
            }

            job = await procrastinate_app.tasks.process_video_async.defer_async(
                input_path=str(test_video_file),
                output_dir=f"concurrent_job_{i}",
                config_dict=config_dict,
            )
            jobs.append(job)
            print(f"   Job {i + 1} submitted: {job.id}")

        # Wait for all jobs to complete
        start_time = time.time()
        for i, job in enumerate(jobs):
            await self._wait_for_job_completion(procrastinate_app, job.id)
            print(f"   ✅ Job {i + 1} completed")

        total_time = time.time() - start_time
        print(f"✅ All {num_jobs} jobs completed in {total_time:.2f}s")

    @pytest.mark.asyncio
    async def test_worker_version_compatibility(
        self,
        docker_compose_project: str,
        procrastinate_app,
        postgres_connection: dict[str, Any],
        clean_database: None,
    ):
        """Test that worker is using correct Procrastinate version."""
        print("\n🔍 Testing worker version compatibility")

        # Get version info from our compatibility layer
        version_info = get_version_info()
        print(f"   Procrastinate version: {version_info['procrastinate_version']}")
        print(f"   Features: {list(version_info['features'].keys())}")

        # Verify database schema is compatible
        with psycopg2.connect(**postgres_connection) as conn:
            with conn.cursor() as cursor:
                # Check that Procrastinate tables exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'procrastinate_%'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]

                print(f"   Database tables: {tables}")

                # Verify core tables exist
                required_tables = ["procrastinate_jobs", "procrastinate_events"]
                for table in required_tables:
                    assert table in tables, f"Required table missing: {table}"

        print("✅ Worker version compatibility verified")

    async def _get_job_status(self, app, job_id: int) -> str:
        """Get current job status from database."""
        # Use the app's connector to query job status
        async with app.open_async() as app_context:
            async with app_context.connector.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT status FROM procrastinate_jobs WHERE id = %s", [job_id]
                    )
                    row = await cursor.fetchone()
                    return row[0] if row else "not_found"

    async def _wait_for_job_completion(
        self, app, job_id: int, timeout: int = 60, expected_status: str = "succeeded"
    ) -> None:
        """Wait for job to reach completion status."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._get_job_status(app, job_id)

            if status == expected_status:
                return
            elif status == "failed" and expected_status == "succeeded":
                raise AssertionError(f"Job {job_id} failed unexpectedly")
            elif status in ["succeeded", "failed"] and status != expected_status:
                raise AssertionError(
                    f"Job {job_id} completed with status '{status}', expected '{expected_status}'"
                )

            await asyncio.sleep(2)

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


class TestProcrastinateQueueManagement:
    """Tests for job queue management and monitoring."""

    @pytest.mark.asyncio
    async def test_job_queue_status(
        self,
        docker_compose_project: str,
        procrastinate_app,
        postgres_connection: dict[str, Any],
        clean_database: None,
    ):
        """Test job queue status monitoring."""
        print("\n📊 Testing job queue status monitoring")

        # Check initial queue state (should be empty)
        queue_stats = await self._get_queue_statistics(postgres_connection)
        print(f"   Initial queue stats: {queue_stats}")

        assert queue_stats["total_jobs"] == 0
        assert queue_stats["todo"] == 0
        assert queue_stats["doing"] == 0
        assert queue_stats["succeeded"] == 0
        assert queue_stats["failed"] == 0

        print("✅ Queue status monitoring working")

    @pytest.mark.asyncio
    async def test_job_cleanup(
        self,
        docker_compose_project: str,
        test_video_file: Path,
        temp_video_dir: Path,
        procrastinate_app,
        postgres_connection: dict[str, Any],
        clean_database: None,
    ):
        """Test job cleanup and retention."""
        print("\n🧹 Testing job cleanup functionality")

        # Submit a job
        config_dict = {
            "base_path": str(temp_video_dir / "cleanup_test"),
            "output_formats": ["mp4"],
            "quality_preset": "low",
        }

        job = await procrastinate_app.tasks.process_video_async.defer_async(
            input_path=str(test_video_file),
            output_dir="cleanup_test",
            config_dict=config_dict,
        )

        # Wait for completion
        await TestProcrastinateWorkerE2E()._wait_for_job_completion(
            procrastinate_app, job.id
        )

        # Verify job record exists
        stats_after = await self._get_queue_statistics(postgres_connection)
        assert stats_after["succeeded"] >= 1

        print("✅ Job cleanup test completed")

    async def _get_queue_statistics(
        self, postgres_connection: dict[str, Any]
    ) -> dict[str, int]:
        """Get job queue statistics."""
        with psycopg2.connect(**postgres_connection) as conn:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(*) FILTER (WHERE status = 'todo') as todo,
                        COUNT(*) FILTER (WHERE status = 'doing') as doing,
                        COUNT(*) FILTER (WHERE status = 'succeeded') as succeeded,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed
                    FROM procrastinate_jobs;
                """)
                row = cursor.fetchone()
                return {
                    "total_jobs": row[0],
                    "todo": row[1],
                    "doing": row[2],
                    "succeeded": row[3],
                    "failed": row[4],
                }
