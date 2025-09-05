"""Tests for Procrastinate migration utilities."""

import pytest

from video_processor.tasks.migration import ProcrastinateMigrationHelper, create_migration_script
from video_processor.tasks.compat import IS_PROCRASTINATE_3_PLUS


class TestProcrastinateMigrationHelper:
    """Test migration helper functionality."""

    def test_migration_helper_creation(self):
        """Test migration helper initialization."""
        database_url = "postgresql://test:test@localhost/test"
        helper = ProcrastinateMigrationHelper(database_url)
        
        assert helper.database_url == database_url
        assert helper.version_info is not None
        assert "procrastinate_version" in helper.version_info

    def test_migration_steps_generation(self):
        """Test migration steps generation."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        steps = helper.get_migration_steps()
        
        assert isinstance(steps, list)
        assert len(steps) > 0
        
        if IS_PROCRASTINATE_3_PLUS:
            # Should have pre/post migration steps
            assert len(steps) >= 7  # Pre, deploy, post, verify
            assert any("pre-migration" in step.lower() for step in steps)
            assert any("post-migration" in step.lower() for step in steps)
        else:
            # Should have single migration step
            assert len(steps) >= 2  # Migrate, verify
            assert any("migration" in step.lower() for step in steps)

    def test_print_migration_plan(self, capsys):
        """Test migration plan printing."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        helper.print_migration_plan()
        
        captured = capsys.readouterr()
        assert "Procrastinate Migration Plan" in captured.out
        assert "Version Info:" in captured.out
        assert "Current Version:" in captured.out

    def test_migration_command_structure(self):
        """Test that migration commands have correct structure."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        
        # Test method availability
        assert hasattr(helper, 'apply_pre_migration')
        assert hasattr(helper, 'apply_post_migration')
        assert hasattr(helper, 'apply_legacy_migration')
        assert hasattr(helper, 'check_schema')
        assert hasattr(helper, 'run_migration_command')

    def test_migration_command_validation(self):
        """Test migration command validation without actually running."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        
        # Test that methods return appropriate responses for invalid DB
        if IS_PROCRASTINATE_3_PLUS:
            # Pre-migration should be available
            assert hasattr(helper, 'apply_pre_migration')
            assert hasattr(helper, 'apply_post_migration')
        else:
            # Legacy migration should be available
            assert hasattr(helper, 'apply_legacy_migration')


class TestMigrationScriptGeneration:
    """Test migration script generation."""

    def test_script_generation(self):
        """Test that migration script is generated correctly."""
        script_content = create_migration_script()
        
        assert isinstance(script_content, str)
        assert len(script_content) > 0
        
        # Check for essential script components
        assert "#!/usr/bin/env python3" in script_content
        assert "Procrastinate migration script" in script_content
        assert "migrate_database" in script_content
        assert "asyncio" in script_content
        
        # Check for command line argument handling
        assert "--pre" in script_content or "--post" in script_content

    def test_script_has_proper_structure(self):
        """Test that generated script has proper Python structure."""
        script_content = create_migration_script()
        
        # Should have proper Python script structure
        lines = script_content.split('\n')
        
        # Check shebang
        assert lines[0] == "#!/usr/bin/env python3"
        
        # Check for main function
        assert 'def main():' in script_content
        
        # Check for asyncio usage
        assert 'asyncio.run(main())' in script_content


class TestMigrationWorkflow:
    """Test complete migration workflow scenarios."""

    def test_version_aware_migration_selection(self):
        """Test that correct migration path is selected based on version."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        
        if IS_PROCRASTINATE_3_PLUS:
            # 3.x should use pre/post migrations
            steps = helper.get_migration_steps()
            step_text = ' '.join(steps).lower()
            assert 'pre-migration' in step_text
            assert 'post-migration' in step_text
        else:
            # 2.x should use legacy migration
            steps = helper.get_migration_steps()
            step_text = ' '.join(steps).lower()
            assert 'migration' in step_text
            assert 'pre-migration' not in step_text

    def test_migration_helper_consistency(self):
        """Test that migration helper provides consistent information."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        
        # Version info should be consistent
        version_info = helper.version_info
        steps = helper.get_migration_steps()
        
        assert version_info["is_v3_plus"] == IS_PROCRASTINATE_3_PLUS
        
        # Steps should match version
        if version_info["is_v3_plus"]:
            assert len(steps) > 4  # Should have multiple steps for 3.x
        else:
            assert len(steps) >= 2  # Should have basic steps for 2.x


@pytest.mark.asyncio
class TestAsyncMigration:
    """Test async migration functionality."""

    async def test_migrate_database_function_exists(self):
        """Test that async migration function exists and is callable."""
        from video_processor.tasks.migration import migrate_database
        
        # Function should exist and be async
        assert callable(migrate_database)
        
        # Should handle invalid database gracefully (don't actually run)
        # Just test that it exists and has the right signature
        import inspect
        sig = inspect.signature(migrate_database)
        
        expected_params = ['database_url', 'pre_migration_only', 'post_migration_only']
        actual_params = list(sig.parameters.keys())
        
        for param in expected_params:
            assert param in actual_params


class TestRegressionPrevention:
    """Tests to prevent regressions in migration functionality."""

    def test_migration_helper_backwards_compatibility(self):
        """Ensure migration helper maintains backwards compatibility."""
        helper = ProcrastinateMigrationHelper("postgresql://fake/db")
        
        # Essential methods should always exist
        required_methods = [
            'get_migration_steps',
            'print_migration_plan',
            'run_migration_command',
            'check_schema',
        ]
        
        for method in required_methods:
            assert hasattr(helper, method)
            assert callable(getattr(helper, method))

    def test_version_detection_stability(self):
        """Test that version detection is stable and predictable."""
        from video_processor.tasks.compat import get_version_info, PROCRASTINATE_VERSION
        
        info1 = get_version_info()
        info2 = get_version_info()
        
        # Should return consistent results
        assert info1 == info2
        assert info1["version_tuple"] == PROCRASTINATE_VERSION

    def test_feature_flags_consistency(self):
        """Test that feature flags are consistent with version."""
        from video_processor.tasks.compat import FEATURES, IS_PROCRASTINATE_3_PLUS
        
        # 3.x features should only be available in 3.x
        v3_features = [
            "graceful_shutdown", 
            "job_cancellation", 
            "pre_post_migrations",
            "psycopg3_support"
        ]
        
        for feature in v3_features:
            if IS_PROCRASTINATE_3_PLUS:
                assert FEATURES[feature] is True, f"{feature} should be True in 3.x"
            else:
                assert FEATURES[feature] is False, f"{feature} should be False in 2.x"