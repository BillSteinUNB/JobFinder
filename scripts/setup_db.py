#!/usr/bin/env python3
"""Script to initialize the database schema."""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.metadata_db import MetadataDB
from src.utils.config import get_settings
from src.utils.logger import setup_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize the job database schema",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the database (WARNING: deletes all data!)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for database setup."""
    args = parse_args()

    # Setup logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=level)
    logger = get_logger(__name__)

    settings = get_settings()
    db_path = settings.metadata_db_path

    logger.info("=" * 60)
    logger.info("Database Setup Script")
    logger.info("=" * 60)
    logger.info(f"Database path: {db_path}")

    if args.reset and db_path.exists():
        logger.warning("Resetting database - all data will be deleted!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            logger.info("Reset cancelled.")
            return 0
        db_path.unlink()
        logger.info("Database file deleted.")

    # Initialize database (creates schema if needed)
    db = MetadataDB()
    job_count = db.get_job_count()

    logger.info("=" * 60)
    logger.info("Database Setup Complete!")
    logger.info(f"Database location: {db_path}")
    logger.info(f"Current job count: {job_count}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
