"""
Procrastinate version compatibility layer.

This module provides compatibility between Procrastinate 2.x and 3.x versions,
allowing the codebase to work with both versions during the migration period.
"""

from typing import Any

import procrastinate


def get_procrastinate_version() -> tuple[int, int, int]:
    """Get the current Procrastinate version."""
    version_str = procrastinate.__version__
    # Handle version strings like "3.0.0", "3.0.0a1", etc.
    version_parts = version_str.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1])
    # Handle patch versions with alpha/beta suffixes
    patch_str = version_parts[2] if len(version_parts) > 2 else "0"
    patch = int(''.join(c for c in patch_str if c.isdigit()) or "0")
    return (major, minor, patch)


# Check Procrastinate version for compatibility
PROCRASTINATE_VERSION = get_procrastinate_version()
IS_PROCRASTINATE_3_PLUS = PROCRASTINATE_VERSION[0] >= 3


def get_connector_class():
    """Get the appropriate connector class based on Procrastinate version."""
    if IS_PROCRASTINATE_3_PLUS:
        # Procrastinate 3.x
        try:
            from procrastinate import PsycopgConnector
            return PsycopgConnector
        except ImportError:
            # Fall back to AiopgConnector if PsycopgConnector not available
            from procrastinate import AiopgConnector
            return AiopgConnector
    else:
        # Procrastinate 2.x
        from procrastinate import AiopgConnector
        return AiopgConnector


def create_connector(database_url: str, **kwargs):
    """Create a database connector compatible with the current Procrastinate version."""
    connector_class = get_connector_class()

    if IS_PROCRASTINATE_3_PLUS:
        # Procrastinate 3.x uses different parameter names
        if connector_class.__name__ == "PsycopgConnector":
            # PsycopgConnector uses 'conninfo' parameter (preferred in 3.5.x)
            # Default to better pool settings for 3.5.2
            default_kwargs = {
                "pool_size": 10,
                "max_pool_size": 20,
            }
            default_kwargs.update(kwargs)
            return connector_class(conninfo=database_url, **default_kwargs)
        else:
            # AiopgConnector fallback
            return connector_class(conninfo=database_url, **kwargs)
    else:
        # Procrastinate 2.x (legacy support)
        return connector_class(conninfo=database_url, **kwargs)


def create_app_with_connector(database_url: str, **connector_kwargs) -> procrastinate.App:
    """Create a Procrastinate App with the appropriate connector."""
    connector = create_connector(database_url, **connector_kwargs)
    return procrastinate.App(connector=connector)


class CompatJobContext:
    """
    Job context compatibility wrapper to handle differences between versions.
    """

    def __init__(self, job_context):
        self._context = job_context
        self._version = PROCRASTINATE_VERSION

    def should_abort(self) -> bool:
        """Check if the job should abort (compatible across versions)."""
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x
            return self._context.should_abort()
        else:
            # Procrastinate 2.x
            if hasattr(self._context, 'should_abort'):
                return self._context.should_abort()
            else:
                # Fallback for older versions
                return False

    async def should_abort_async(self) -> bool:
        """Check if the job should abort asynchronously."""
        if IS_PROCRASTINATE_3_PLUS:
            # In 3.x, should_abort() works for both sync and async
            return self.should_abort()
        else:
            # Procrastinate 2.x
            if hasattr(self._context, 'should_abort_async'):
                return await self._context.should_abort_async()
            else:
                return self.should_abort()

    @property
    def job(self):
        """Access the job object."""
        return self._context.job

    @property
    def task(self):
        """Access the task object."""
        return self._context.task

    def __getattr__(self, name):
        """Delegate other attributes to the wrapped context."""
        return getattr(self._context, name)


def get_migration_commands() -> dict[str, str]:
    """Get migration commands for the current Procrastinate version."""
    if IS_PROCRASTINATE_3_PLUS:
        return {
            "pre_migrate": "procrastinate schema --apply --mode=pre",
            "post_migrate": "procrastinate schema --apply --mode=post",
            "check": "procrastinate schema --check",
        }
    else:
        return {
            "migrate": "procrastinate schema --apply",
            "check": "procrastinate schema --check",
        }


def get_worker_options_mapping() -> dict[str, str]:
    """Get mapping of worker options between versions."""
    if IS_PROCRASTINATE_3_PLUS:
        return {
            "timeout": "fetch_job_polling_interval",  # Renamed in 3.x
            "remove_error": "remove_failed",          # Renamed in 3.x
            "include_error": "include_failed",        # Renamed in 3.x
        }
    else:
        return {
            "timeout": "timeout",
            "remove_error": "remove_error",
            "include_error": "include_error",
        }


def normalize_worker_kwargs(**kwargs) -> dict[str, Any]:
    """Normalize worker keyword arguments for the current version."""
    mapping = get_worker_options_mapping()
    normalized = {}

    for key, value in kwargs.items():
        # Map old names to new names if needed
        normalized_key = mapping.get(key, key)
        normalized[normalized_key] = value

    return normalized


# Version-specific feature flags
FEATURES = {
    "graceful_shutdown": IS_PROCRASTINATE_3_PLUS,
    "job_cancellation": IS_PROCRASTINATE_3_PLUS,
    "pre_post_migrations": IS_PROCRASTINATE_3_PLUS,
    "psycopg3_support": IS_PROCRASTINATE_3_PLUS,
    "improved_performance": PROCRASTINATE_VERSION >= (3, 5, 0),  # Performance improvements in 3.5+
    "schema_compatibility": PROCRASTINATE_VERSION >= (3, 5, 2),  # Better schema support in 3.5.2
    "enhanced_indexing": PROCRASTINATE_VERSION >= (3, 5, 0),     # Improved indexes in 3.5+
}


def get_version_info() -> dict[str, Any]:
    """Get version and feature information."""
    return {
        "procrastinate_version": procrastinate.__version__,
        "version_tuple": PROCRASTINATE_VERSION,
        "is_v3_plus": IS_PROCRASTINATE_3_PLUS,
        "features": FEATURES,
        "migration_commands": get_migration_commands(),
    }
