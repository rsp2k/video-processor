"""
Procrastinate migration utilities for upgrading from 2.x to 3.x.

This module provides utilities to help with database migrations and
version compatibility during the upgrade process.
"""

import logging
import subprocess
import sys

from .compat import (
    IS_PROCRASTINATE_3_PLUS,
    get_migration_commands,
    get_version_info,
)

logger = logging.getLogger(__name__)


class ProcrastinateMigrationHelper:
    """Helper class for managing Procrastinate migrations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.version_info = get_version_info()

    def get_migration_steps(self) -> list[str]:
        """Get the migration steps for the current version."""
        commands = get_migration_commands()

        if IS_PROCRASTINATE_3_PLUS:
            return [
                "1. Apply pre-migrations before deploying new code",
                f"   Command: {commands['pre_migrate']}",
                "2. Deploy new application code",
                "3. Apply post-migrations after deployment",
                f"   Command: {commands['post_migrate']}",
                "4. Verify schema is current",
                f"   Command: {commands['check']}",
            ]
        else:
            return [
                "1. Apply database migrations",
                f"   Command: {commands['migrate']}",
                "2. Verify schema is current",
                f"   Command: {commands['check']}",
            ]

    def print_migration_plan(self) -> None:
        """Print the migration plan for the current version."""
        print(
            f"Procrastinate Migration Plan (v{self.version_info['procrastinate_version']})"
        )
        print("=" * 60)

        for step in self.get_migration_steps():
            print(step)

        print("\nVersion Info:")
        print(f"  Current Version: {self.version_info['procrastinate_version']}")
        print(f"  Is 3.x+: {self.version_info['is_v3_plus']}")
        print(f"  Features Available: {list(self.version_info['features'].keys())}")

    def run_migration_command(self, command: str) -> bool:
        """
        Run a migration command.

        Args:
            command: The command to run

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Running migration command: {command}")

            # Set environment variable for database URL
            env = {"PROCRASTINATE_DATABASE_URL": self.database_url}

            result = subprocess.run(
                command.split(),
                env={**dict(sys.environ), **env},
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")

            logger.info("Migration command completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Migration command failed: {e}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False

    def apply_pre_migration(self) -> bool:
        """Apply pre-migration for Procrastinate 3.x."""
        if not IS_PROCRASTINATE_3_PLUS:
            logger.warning("Pre-migration only applicable to Procrastinate 3.x+")
            return True

        commands = get_migration_commands()
        return self.run_migration_command(commands["pre_migrate"])

    def apply_post_migration(self) -> bool:
        """Apply post-migration for Procrastinate 3.x."""
        if not IS_PROCRASTINATE_3_PLUS:
            logger.warning("Post-migration only applicable to Procrastinate 3.x+")
            return True

        commands = get_migration_commands()
        return self.run_migration_command(commands["post_migrate"])

    def apply_legacy_migration(self) -> bool:
        """Apply legacy migration for Procrastinate 2.x."""
        if IS_PROCRASTINATE_3_PLUS:
            logger.warning("Legacy migration only applicable to Procrastinate 2.x")
            return True

        commands = get_migration_commands()
        return self.run_migration_command(commands["migrate"])

    def check_schema(self) -> bool:
        """Check if the database schema is current."""
        commands = get_migration_commands()
        return self.run_migration_command(commands["check"])


async def migrate_database(
    database_url: str,
    pre_migration_only: bool = False,
    post_migration_only: bool = False,
) -> bool:
    """
    Migrate the Procrastinate database schema.

    Args:
        database_url: Database connection string
        pre_migration_only: Only apply pre-migration (for 3.x)
        post_migration_only: Only apply post-migration (for 3.x)

    Returns:
        True if successful, False otherwise
    """
    helper = ProcrastinateMigrationHelper(database_url)

    logger.info("Starting Procrastinate database migration")
    helper.print_migration_plan()

    try:
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x migration process
            if pre_migration_only:
                success = helper.apply_pre_migration()
            elif post_migration_only:
                success = helper.apply_post_migration()
            else:
                # Apply both pre and post migrations
                logger.warning(
                    "Applying both pre and post migrations. "
                    "In production, these should be run separately!"
                )
                success = helper.apply_pre_migration() and helper.apply_post_migration()
        else:
            # Procrastinate 2.x migration process
            success = helper.apply_legacy_migration()

        if success:
            # Verify schema is current
            success = helper.check_schema()

        if success:
            logger.info("Database migration completed successfully")
        else:
            logger.error("Database migration failed")

        return success

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False


def create_migration_script() -> str:
    """Create a migration script for the current environment."""
    version_info = get_version_info()

    script = f"""#!/usr/bin/env python3
\"\"\"
Procrastinate migration script for version {version_info["procrastinate_version"]}

This script helps migrate your Procrastinate database schema.
\"\"\"

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_processor.tasks.migration import migrate_database


async def main():
    database_url = os.environ.get(
        'PROCRASTINATE_DATABASE_URL',
        'postgresql://localhost/procrastinate_dev'
    )
    
    print(f"Migrating database: {{database_url}}")
    
    # Parse command line arguments
    pre_only = '--pre' in sys.argv
    post_only = '--post' in sys.argv
    
    success = await migrate_database(
        database_url=database_url,
        pre_migration_only=pre_only,
        post_migration_only=post_only,
    )
    
    if not success:
        print("Migration failed!")
        sys.exit(1)
    
    print("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
"""

    return script


if __name__ == "__main__":
    # Generate migration script when run directly
    script_content = create_migration_script()

    with open("migrate_procrastinate.py", "w") as f:
        f.write(script_content)

    print("Generated migration script: migrate_procrastinate.py")
    print("Run with: python migrate_procrastinate.py [--pre|--post]")
