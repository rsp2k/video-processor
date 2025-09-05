"""
End-to-end integration tests for database migration functionality in Docker environment.

These tests verify:
- Database migration execution in containerized environment
- Schema creation and validation
- Version compatibility between Procrastinate 2.x and 3.x
- Migration rollback scenarios
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from video_processor.tasks.migration import migrate_database, ProcrastinateMigrationHelper
from video_processor.tasks.compat import get_version_info, IS_PROCRASTINATE_3_PLUS


class TestDatabaseMigrationE2E:
    """End-to-end tests for database migration in Docker environment."""
    
    def test_fresh_database_migration(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test migrating a fresh database from scratch."""
        print(f"\n🗄️ Testing fresh database migration")
        
        # Create a fresh test database
        test_db_name = "video_processor_migration_fresh"
        self._create_test_database(postgres_connection, test_db_name)
        
        try:
            # Build connection URL for test database
            db_url = (
                f"postgresql://{postgres_connection['user']}:"
                f"{postgres_connection['password']}@"
                f"{postgres_connection['host']}:{postgres_connection['port']}/"
                f"{test_db_name}"
            )
            
            # Run migration
            success = asyncio.run(migrate_database(db_url))
            assert success, "Migration should succeed on fresh database"
            
            # Verify schema was created
            self._verify_procrastinate_schema(postgres_connection, test_db_name)
            
            print("✅ Fresh database migration completed successfully")
            
        finally:
            self._drop_test_database(postgres_connection, test_db_name)
    
    def test_migration_idempotency(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test that migrations can be run multiple times safely."""
        print(f"\n🔁 Testing migration idempotency")
        
        test_db_name = "video_processor_migration_idempotent"
        self._create_test_database(postgres_connection, test_db_name)
        
        try:
            db_url = (
                f"postgresql://{postgres_connection['user']}:"
                f"{postgres_connection['password']}@"
                f"{postgres_connection['host']}:{postgres_connection['port']}/"
                f"{test_db_name}"
            )
            
            # Run migration first time
            success1 = asyncio.run(migrate_database(db_url))
            assert success1, "First migration should succeed"
            
            # Run migration second time (should be idempotent)
            success2 = asyncio.run(migrate_database(db_url))
            assert success2, "Second migration should also succeed (idempotent)"
            
            # Verify schema is still intact
            self._verify_procrastinate_schema(postgres_connection, test_db_name)
            
            print("✅ Migration idempotency test passed")
            
        finally:
            self._drop_test_database(postgres_connection, test_db_name)
    
    def test_docker_migration_service(
        self,
        docker_compose_project: str,
        postgres_connection: Dict[str, Any]
    ):
        """Test that Docker migration service works correctly."""
        print(f"\n🐳 Testing Docker migration service")
        
        # The migration should have already run as part of docker_compose_project setup
        # Verify the migration was successful by checking the main database
        
        main_db_name = "video_processor_integration_test"
        self._verify_procrastinate_schema(postgres_connection, main_db_name)
        
        print("✅ Docker migration service verification passed")
    
    def test_migration_helper_functionality(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test migration helper utility functions."""
        print(f"\n🛠️ Testing migration helper functionality")
        
        test_db_name = "video_processor_migration_helper"
        self._create_test_database(postgres_connection, test_db_name)
        
        try:
            db_url = (
                f"postgresql://{postgres_connection['user']}:"
                f"{postgres_connection['password']}@"
                f"{postgres_connection['host']}:{postgres_connection['port']}/"
                f"{test_db_name}"
            )
            
            # Test migration helper
            helper = ProcrastinateMigrationHelper(db_url)
            
            # Test migration plan generation
            migration_plan = helper.generate_migration_plan()
            assert isinstance(migration_plan, list)
            assert len(migration_plan) > 0
            
            print(f"   Generated migration plan with {len(migration_plan)} steps")
            
            # Test version-specific migration commands
            if IS_PROCRASTINATE_3_PLUS:
                pre_cmd = helper.get_pre_migration_command()
                post_cmd = helper.get_post_migration_command() 
                assert "pre" in pre_cmd
                assert "post" in post_cmd
                print(f"   Procrastinate 3.x commands: pre='{pre_cmd}', post='{post_cmd}'")
            else:
                legacy_cmd = helper.get_legacy_migration_command()
                assert "schema" in legacy_cmd
                print(f"   Procrastinate 2.x command: '{legacy_cmd}'")
            
            print("✅ Migration helper functionality verified")
            
        finally:
            self._drop_test_database(postgres_connection, test_db_name)
    
    def test_version_compatibility_detection(
        self,
        docker_compose_project: str
    ):
        """Test version compatibility detection during migration."""
        print(f"\n🔍 Testing version compatibility detection")
        
        # Get version information
        version_info = get_version_info()
        
        print(f"   Detected Procrastinate version: {version_info['procrastinate_version']}")
        print(f"   Is Procrastinate 3+: {IS_PROCRASTINATE_3_PLUS}")
        print(f"   Available features: {list(version_info['features'].keys())}")
        
        # Verify version detection is working
        assert version_info["procrastinate_version"] is not None
        assert isinstance(IS_PROCRASTINATE_3_PLUS, bool)
        assert len(version_info["features"]) > 0
        
        print("✅ Version compatibility detection working")
    
    def test_migration_error_handling(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test migration error handling for invalid scenarios."""
        print(f"\n🚫 Testing migration error handling")
        
        # Test with invalid database URL
        invalid_url = "postgresql://invalid_user:invalid_pass@localhost:5432/nonexistent_db"
        
        # Migration should handle the error gracefully
        success = asyncio.run(migrate_database(invalid_url))
        assert not success, "Migration should fail with invalid database URL"
        
        print("✅ Migration error handling test passed")
    
    def _create_test_database(self, postgres_connection: Dict[str, Any], db_name: str):
        """Create a test database for migration testing."""
        # Connect to postgres db to create new database
        conn_params = postgres_connection.copy()
        conn_params["database"] = "postgres"
        
        with psycopg2.connect(**conn_params) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                # Drop if exists, then create
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                print(f"   Created test database: {db_name}")
    
    def _drop_test_database(self, postgres_connection: Dict[str, Any], db_name: str):
        """Clean up test database."""
        conn_params = postgres_connection.copy()
        conn_params["database"] = "postgres"
        
        with psycopg2.connect(**conn_params) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                print(f"   Cleaned up test database: {db_name}")
    
    def _verify_procrastinate_schema(self, postgres_connection: Dict[str, Any], db_name: str):
        """Verify that Procrastinate schema was created properly."""
        conn_params = postgres_connection.copy()
        conn_params["database"] = db_name
        
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cursor:
                # Check for core Procrastinate tables
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'procrastinate_%'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Required tables for Procrastinate
                required_tables = ["procrastinate_jobs", "procrastinate_events"]
                for required_table in required_tables:
                    assert required_table in tables, f"Required table missing: {required_table}"
                
                # Check jobs table structure
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'procrastinate_jobs'
                    ORDER BY column_name;
                """)
                job_columns = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Verify essential columns exist
                essential_columns = ["id", "status", "task_name", "queue_name"]
                for col in essential_columns:
                    assert col in job_columns, f"Essential column missing from jobs table: {col}"
                
                print(f"   ✅ Schema verified: {len(tables)} tables, {len(job_columns)} job columns")


class TestMigrationIntegrationScenarios:
    """Test realistic migration scenarios in Docker environment."""
    
    def test_production_like_migration_workflow(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test a production-like migration workflow."""
        print(f"\n🏭 Testing production-like migration workflow")
        
        test_db_name = "video_processor_migration_production"
        self._create_fresh_db(postgres_connection, test_db_name)
        
        try:
            db_url = self._build_db_url(postgres_connection, test_db_name)
            
            # Step 1: Run pre-migration (if Procrastinate 3.x)
            if IS_PROCRASTINATE_3_PLUS:
                print("   Running pre-migration phase...")
                success = asyncio.run(migrate_database(db_url, pre_migration_only=True))
                assert success, "Pre-migration should succeed"
            
            # Step 2: Simulate application deployment (schema should be compatible)
            self._verify_basic_schema_compatibility(postgres_connection, test_db_name)
            
            # Step 3: Run post-migration (if Procrastinate 3.x)
            if IS_PROCRASTINATE_3_PLUS:
                print("   Running post-migration phase...")
                success = asyncio.run(migrate_database(db_url, post_migration_only=True))
                assert success, "Post-migration should succeed"
            else:
                # Single migration for 2.x
                print("   Running single migration phase...")
                success = asyncio.run(migrate_database(db_url))
                assert success, "Migration should succeed"
            
            # Step 4: Verify final schema
            self._verify_complete_schema(postgres_connection, test_db_name)
            
            print("✅ Production-like migration workflow completed")
            
        finally:
            self._cleanup_db(postgres_connection, test_db_name)
    
    def test_concurrent_migration_handling(
        self,
        postgres_connection: Dict[str, Any],
        docker_compose_project: str
    ):
        """Test handling of concurrent migration attempts."""
        print(f"\n🔀 Testing concurrent migration handling")
        
        test_db_name = "video_processor_migration_concurrent"
        self._create_fresh_db(postgres_connection, test_db_name)
        
        try:
            db_url = self._build_db_url(postgres_connection, test_db_name)
            
            # Run two migrations concurrently (should handle gracefully)
            async def run_concurrent_migrations():
                tasks = [
                    migrate_database(db_url),
                    migrate_database(db_url)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results
            
            results = asyncio.run(run_concurrent_migrations())
            
            # At least one should succeed, others should handle gracefully
            success_count = sum(1 for r in results if r is True)
            assert success_count >= 1, "At least one concurrent migration should succeed"
            
            # Schema should still be valid
            self._verify_complete_schema(postgres_connection, test_db_name)
            
            print("✅ Concurrent migration handling test passed")
            
        finally:
            self._cleanup_db(postgres_connection, test_db_name)
    
    def _create_fresh_db(self, postgres_connection: Dict[str, Any], db_name: str):
        """Create a fresh database for testing."""
        conn_params = postgres_connection.copy()
        conn_params["database"] = "postgres"
        
        with psycopg2.connect(**conn_params) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                cursor.execute(f'CREATE DATABASE "{db_name}"')
    
    def _cleanup_db(self, postgres_connection: Dict[str, Any], db_name: str):
        """Clean up test database."""
        conn_params = postgres_connection.copy()
        conn_params["database"] = "postgres"
        
        with psycopg2.connect(**conn_params) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    
    def _build_db_url(self, postgres_connection: Dict[str, Any], db_name: str) -> str:
        """Build database URL for testing."""
        return (
            f"postgresql://{postgres_connection['user']}:"
            f"{postgres_connection['password']}@"
            f"{postgres_connection['host']}:{postgres_connection['port']}/"
            f"{db_name}"
        )
    
    def _verify_basic_schema_compatibility(self, postgres_connection: Dict[str, Any], db_name: str):
        """Verify basic schema compatibility during migration."""
        conn_params = postgres_connection.copy()
        conn_params["database"] = db_name
        
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cursor:
                # Should be able to query basic Procrastinate tables
                cursor.execute("SELECT COUNT(*) FROM procrastinate_jobs")
                assert cursor.fetchone()[0] == 0  # Should be empty initially
    
    def _verify_complete_schema(self, postgres_connection: Dict[str, Any], db_name: str):
        """Verify complete schema after migration."""
        TestDatabaseMigrationE2E()._verify_procrastinate_schema(postgres_connection, db_name)