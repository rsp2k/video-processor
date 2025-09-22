#!/usr/bin/env python3
"""
Worker compatibility module for Procrastinate 2.x and 3.x.

Provides a unified worker interface that works across different Procrastinate versions.
"""

import asyncio
import logging
import os
import sys

from .compat import (
    IS_PROCRASTINATE_3_PLUS,
    create_app_with_connector,
    get_version_info,
    map_worker_options,
)

logger = logging.getLogger(__name__)


def setup_worker_app(database_url: str, connector_kwargs: dict | None = None):
    """Set up Procrastinate app for worker usage."""
    connector_kwargs = connector_kwargs or {}

    # Create app with proper connector
    app = create_app_with_connector(database_url, **connector_kwargs)

    # Import tasks to register them
    from . import procrastinate_tasks  # noqa: F401

    logger.info(f"Worker app setup complete. {get_version_info()}")
    return app


async def run_worker_async(
    database_url: str,
    queues: list[str] | None = None,
    concurrency: int = 1,
    **worker_kwargs,
):
    """Run Procrastinate worker with version compatibility."""
    logger.info(
        f"Starting Procrastinate worker (v{get_version_info()['procrastinate_version']})"
    )

    # Set up the app
    app = setup_worker_app(database_url)

    # Map worker options for compatibility
    mapped_options = map_worker_options(worker_kwargs)

    # Default queues
    if queues is None:
        queues = ["video_processing", "thumbnail_generation", "default"]

    logger.info(f"Worker config: queues={queues}, concurrency={concurrency}")
    logger.info(f"Worker options: {mapped_options}")

    try:
        if IS_PROCRASTINATE_3_PLUS:
            # Procrastinate 3.x worker
            async with app.open_async() as app_context:
                worker = app_context.make_worker(
                    queues=queues,
                    concurrency=concurrency,
                    **mapped_options,
                )
                await worker.async_run()
        else:
            # Procrastinate 2.x worker
            worker = app.make_worker(
                queues=queues,
                concurrency=concurrency,
                **mapped_options,
            )
            await worker.async_run()

    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


def run_worker_sync(
    database_url: str,
    queues: list[str] | None = None,
    concurrency: int = 1,
    **worker_kwargs,
):
    """Synchronous wrapper for running the worker."""
    try:
        asyncio.run(
            run_worker_async(
                database_url=database_url,
                queues=queues,
                concurrency=concurrency,
                **worker_kwargs,
            )
        )
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
        sys.exit(0)


def main():
    """Main entry point for worker CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Procrastinate Worker")
    parser.add_argument("command", choices=["worker"], help="Command to run")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("PROCRASTINATE_DATABASE_URL"),
        help="Database URL",
    )
    parser.add_argument(
        "--queues",
        nargs="*",
        default=["video_processing", "thumbnail_generation", "default"],
        help="Queue names to process",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.environ.get("WORKER_CONCURRENCY", "1")),
        help="Worker concurrency",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("WORKER_TIMEOUT", "300")),
        help="Worker timeout (maps to fetch_job_polling_interval in 3.x)",
    )

    args = parser.parse_args()

    if not args.database_url:
        logger.error(
            "Database URL is required (--database-url or PROCRASTINATE_DATABASE_URL)"
        )
        sys.exit(1)

    logger.info(f"Starting {args.command} with database: {args.database_url}")

    if args.command == "worker":
        run_worker_sync(
            database_url=args.database_url,
            queues=args.queues,
            concurrency=args.concurrency,
            timeout=args.timeout,
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
