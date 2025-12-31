#!/usr/bin/env python3
"""Script to collect jobs from the Adzuna API and store them in the database."""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection.adzuna_client import AdzunaClient, AdzunaClientError
from src.db.metadata_db import MetadataDB
from src.utils.config import get_settings
from src.utils.logger import setup_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect job postings from Adzuna API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default="python developer",
        help="Search keywords (e.g., 'data scientist', 'python developer')",
    )
    parser.add_argument(
        "-l", "--location",
        type=str,
        default=None,
        help="Location to search (e.g., 'new york', 'remote')",
    )
    parser.add_argument(
        "-c", "--country",
        type=str,
        default="us",
        help="Country code (us, gb, ca, au, de, etc.)",
    )
    parser.add_argument(
        "-n", "--max-results",
        type=int,
        default=100,
        help="Maximum number of jobs to fetch",
    )
    parser.add_argument(
        "-d", "--max-days",
        type=int,
        default=7,
        help="Maximum age of job postings in days",
    )
    parser.add_argument(
        "--full-time",
        action="store_true",
        help="Only fetch full-time positions",
    )
    parser.add_argument(
        "--permanent",
        action="store_true",
        help="Only fetch permanent positions",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for job collection."""
    args = parse_args()

    # Setup logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=level)
    logger = get_logger(__name__)

    # Check configuration
    settings = get_settings()
    if not settings.is_adzuna_configured:
        logger.error(
            "Adzuna API credentials not configured. "
            "Please set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env file."
        )
        return 1

    logger.info("=" * 60)
    logger.info("Job Collection Script")
    logger.info("=" * 60)
    logger.info(f"Query: {args.query}")
    logger.info(f"Location: {args.location or 'Any'}")
    logger.info(f"Country: {args.country}")
    logger.info(f"Max results: {args.max_results}")
    logger.info(f"Max days old: {args.max_days}")
    logger.info("=" * 60)

    try:
        # Initialize client and database
        client = AdzunaClient(country=args.country)
        db = MetadataDB()

        # Get existing job count
        existing_count = db.get_job_count()
        logger.info(f"Existing jobs in database: {existing_count}")

        # Fetch jobs
        logger.info("Fetching jobs from Adzuna API...")
        jobs = client.search(
            what=args.query,
            where=args.location,
            max_days_old=args.max_days,
            max_results=args.max_results,
            full_time=args.full_time if args.full_time else None,
            permanent=args.permanent if args.permanent else None,
        )

        if not jobs:
            logger.warning("No jobs found matching the criteria.")
            return 0

        # Store jobs
        logger.info(f"Storing {len(jobs)} jobs in database...")
        inserted, duplicates = db.insert_jobs(jobs)

        # Final report
        new_total = db.get_job_count()
        logger.info("=" * 60)
        logger.info("Collection Complete!")
        logger.info(f"Jobs fetched: {len(jobs)}")
        logger.info(f"New jobs inserted: {inserted}")
        logger.info(f"Duplicates skipped: {duplicates}")
        logger.info(f"Total jobs in database: {new_total}")
        logger.info("=" * 60)

        return 0

    except AdzunaClientError as e:
        logger.error(f"Adzuna API error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
