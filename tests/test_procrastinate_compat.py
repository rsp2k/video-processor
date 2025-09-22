"""Tests for Procrastinate compatibility layer."""

import pytest

from video_processor.tasks.compat import (
    FEATURES,
    IS_PROCRASTINATE_3_PLUS,
    PROCRASTINATE_VERSION,
    CompatJobContext,
    create_app_with_connector,
    create_connector,
    get_migration_commands,
    get_procrastinate_version,
    get_version_info,
    get_worker_options_mapping,
    normalize_worker_kwargs,
)


class TestProcrastinateVersionDetection:
    """Test version detection functionality."""

    def test_version_parsing(self):
        """Test version string parsing."""
        version = get_procrastinate_version()
        assert isinstance(version, tuple)
        assert len(version) == 3
        assert all(isinstance(v, int) for v in version)
        assert version[0] >= 2  # Should be at least version 2.x

    def test_version_flags(self):
        """Test version-specific flags."""
        assert isinstance(IS_PROCRASTINATE_3_PLUS, bool)
        assert isinstance(PROCRASTINATE_VERSION, tuple)

        if PROCRASTINATE_VERSION[0] >= 3:
            assert IS_PROCRASTINATE_3_PLUS is True
        else:
            assert IS_PROCRASTINATE_3_PLUS is False

    def test_version_info(self):
        """Test version info structure."""
        info = get_version_info()

        required_keys = {
            "procrastinate_version",
            "version_tuple",
            "is_v3_plus",
            "features",
            "migration_commands",
        }

        assert set(info.keys()) == required_keys
        assert isinstance(info["version_tuple"], tuple)
        assert isinstance(info["is_v3_plus"], bool)
        assert isinstance(info["features"], dict)
        assert isinstance(info["migration_commands"], dict)

    def test_features(self):
        """Test feature flags."""
        assert isinstance(FEATURES, dict)

        expected_features = {
            "graceful_shutdown",
            "job_cancellation",
            "pre_post_migrations",
            "psycopg3_support",
            "improved_performance",
            "schema_compatibility",
            "enhanced_indexing",
        }

        assert set(FEATURES.keys()) == expected_features
        assert all(isinstance(v, bool) for v in FEATURES.values())


class TestConnectorCreation:
    """Test connector creation functionality."""

    def test_connector_class_selection(self):
        """Test that appropriate connector class is selected."""
        from video_processor.tasks.compat import get_connector_class

        connector_class = get_connector_class()
        assert connector_class is not None
        assert hasattr(connector_class, "__name__")

        if IS_PROCRASTINATE_3_PLUS:
            # Should prefer PsycopgConnector in 3.x
            assert connector_class.__name__ in ["PsycopgConnector", "AiopgConnector"]
        else:
            assert connector_class.__name__ == "AiopgConnector"

    def test_connector_creation(self):
        """Test connector creation with various parameters."""
        database_url = "postgresql://test:test@localhost/test"

        # Test basic creation
        connector = create_connector(database_url)
        assert connector is not None

        # Test with additional kwargs
        connector_with_kwargs = create_connector(
            database_url,
            pool_size=5,
            max_pool_size=10,
        )
        assert connector_with_kwargs is not None

    def test_app_creation(self):
        """Test Procrastinate app creation."""
        database_url = "postgresql://test:test@localhost/test"

        app = create_app_with_connector(database_url)
        assert app is not None
        assert hasattr(app, "connector")
        assert app.connector is not None


class TestWorkerOptions:
    """Test worker options compatibility."""

    def test_option_mapping(self):
        """Test worker option mapping between versions."""
        mapping = get_worker_options_mapping()
        assert isinstance(mapping, dict)

        if IS_PROCRASTINATE_3_PLUS:
            expected_mappings = {
                "timeout": "fetch_job_polling_interval",
                "remove_error": "remove_failed",
                "include_error": "include_failed",
            }
            assert mapping == expected_mappings
        else:
            # In 2.x, mappings should be identity
            assert mapping["timeout"] == "timeout"
            assert mapping["remove_error"] == "remove_error"

    def test_kwargs_normalization(self):
        """Test worker kwargs normalization."""
        test_kwargs = {
            "concurrency": 4,
            "timeout": 5,
            "remove_error": True,
            "include_error": False,
            "name": "test-worker",
        }

        normalized = normalize_worker_kwargs(**test_kwargs)

        assert isinstance(normalized, dict)
        assert normalized["concurrency"] == 4
        assert normalized["name"] == "test-worker"

        if IS_PROCRASTINATE_3_PLUS:
            assert "fetch_job_polling_interval" in normalized
            assert "remove_failed" in normalized
            assert "include_failed" in normalized
            assert normalized["fetch_job_polling_interval"] == 5
            assert normalized["remove_failed"] is True
            assert normalized["include_failed"] is False
        else:
            assert normalized["timeout"] == 5
            assert normalized["remove_error"] is True
            assert normalized["include_error"] is False

    def test_kwargs_passthrough(self):
        """Test that unknown kwargs are passed through unchanged."""
        test_kwargs = {
            "custom_option": "value",
            "another_option": 42,
        }

        normalized = normalize_worker_kwargs(**test_kwargs)
        assert normalized == test_kwargs


class TestMigrationCommands:
    """Test migration command generation."""

    def test_migration_commands_structure(self):
        """Test migration command structure."""
        commands = get_migration_commands()
        assert isinstance(commands, dict)

        if IS_PROCRASTINATE_3_PLUS:
            expected_keys = {"pre_migrate", "post_migrate", "check"}
            assert set(commands.keys()) == expected_keys

            assert "procrastinate schema --apply --mode=pre" in commands["pre_migrate"]
            assert (
                "procrastinate schema --apply --mode=post" in commands["post_migrate"]
            )
        else:
            expected_keys = {"migrate", "check"}
            assert set(commands.keys()) == expected_keys

            assert "procrastinate schema --apply" == commands["migrate"]

        assert "procrastinate schema --check" == commands["check"]


class TestJobContextCompat:
    """Test job context compatibility wrapper."""

    def test_compat_context_creation(self):
        """Test creation of compatibility context."""

        # Create a mock context object
        class MockContext:
            def __init__(self):
                self.job = "mock_job"
                self.task = "mock_task"

            def should_abort(self):
                return False

            async def should_abort_async(self):
                return False

        mock_context = MockContext()
        compat_context = CompatJobContext(mock_context)

        assert compat_context is not None
        assert compat_context.job == "mock_job"
        assert compat_context.task == "mock_task"

    def test_should_abort_methods(self):
        """Test should_abort method compatibility."""

        class MockContext:
            def should_abort(self):
                return True

            async def should_abort_async(self):
                return True

        mock_context = MockContext()
        compat_context = CompatJobContext(mock_context)

        # Test synchronous method
        assert compat_context.should_abort() is True

    @pytest.mark.asyncio
    async def test_should_abort_async(self):
        """Test async should_abort method."""

        class MockContext:
            def should_abort(self):
                return True

            async def should_abort_async(self):
                return True

        mock_context = MockContext()
        compat_context = CompatJobContext(mock_context)

        # Test asynchronous method
        result = await compat_context.should_abort_async()
        assert result is True

    def test_attribute_delegation(self):
        """Test that unknown attributes are delegated to wrapped context."""

        class MockContext:
            def __init__(self):
                self.custom_attr = "custom_value"

            def custom_method(self):
                return "custom_result"

        mock_context = MockContext()
        compat_context = CompatJobContext(mock_context)

        assert compat_context.custom_attr == "custom_value"
        assert compat_context.custom_method() == "custom_result"


class TestIntegration:
    """Integration tests for compatibility features."""

    def test_full_compatibility_workflow(self):
        """Test complete compatibility workflow."""
        # Get version info
        version_info = get_version_info()
        assert version_info["is_v3_plus"] == IS_PROCRASTINATE_3_PLUS

        # Test worker options
        worker_kwargs = normalize_worker_kwargs(
            concurrency=2,
            timeout=10,
            remove_error=False,
        )
        assert "concurrency" in worker_kwargs

        # Test migration commands
        migration_commands = get_migration_commands()
        assert "check" in migration_commands

        if IS_PROCRASTINATE_3_PLUS:
            assert "pre_migrate" in migration_commands
            assert "post_migrate" in migration_commands
        else:
            assert "migrate" in migration_commands

    def test_version_specific_behavior(self):
        """Test that version-specific behavior is consistent."""
        version_info = get_version_info()

        if version_info["is_v3_plus"]:
            # Test 3.x specific features
            assert FEATURES["graceful_shutdown"] is True
            assert FEATURES["job_cancellation"] is True
            assert FEATURES["pre_post_migrations"] is True
        else:
            # Test 2.x behavior
            assert FEATURES["graceful_shutdown"] is False
            assert FEATURES["job_cancellation"] is False
            assert FEATURES["pre_post_migrations"] is False
