#!/usr/bin/env python3
"""Comprehensive job collection script."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection.adzuna_client import AdzunaClient, AdzunaClientError
from src.db.metadata_db import MetadataDB
from src.utils.config import get_settings
from src.utils.logger import setup_logging, get_logger

QUERIES = [
    "python developer", "software engineer", "data scientist",
    "machine learning engineer", "backend developer", "frontend developer",
    "full stack developer", "web developer", "devops engineer", "cloud engineer",
    "data engineer", "AI engineer", "java developer", "javascript developer",
    "react developer", "node.js developer", "golang developer", "rust developer",
    "kubernetes engineer", "site reliability engineer",
]

LOCATIONS = [None, "remote", "new york", "san francisco", "seattle", "boston", "austin", "los angeles", "chicago", "denver"]

def parse_args():
    parser = argparse.ArgumentParser(description="Collect jobs from Adzuna API", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--jobs-per-query", type=int, default=50, help="Max jobs per query")
    parser.add_argument("-d", "--max-days", type=int, default=60, help="Max age in days")
    parser.add_argument("-c", "--country", type=str, default="us", help="Country code")
    parser.add_argument("--queries-only", action="store_true", help="Skip location variations")
    parser.add_argument("--target", type=int, default=1000, help="Target job count")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()

def main():
    args = parse_args()
    import logging
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = get_logger(__name__)
    settings = get_settings()
    if not settings.is_adzuna_configured:
        logger.error("Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env")
        return 1
    logger.info("=" * 70)
    logger.info(f"Collecting jobs - Target: {args.target}")
    logger.info("=" * 70)
    client = AdzunaClient(country=args.country)
    db = MetadataDB()
    logger.info(f"Existing jobs: {db.get_job_count()}")
    total_inserted = 0
    locations = [None] if args.queries_only else LOCATIONS
    for query in QUERIES:
        if total_inserted >= args.target:
            break
        for location in locations:
            if total_inserted >= args.target:
                break
            loc_str = location or "any"
            logger.info(f"Collecting: '{query}' in '{loc_str}'...")
            try:
                jobs = client.search(what=query, where=location, max_days_old=args.max_days, max_results=args.jobs_per_query)
                if jobs:
                    inserted, dups = db.insert_jobs(jobs)
                    total_inserted += inserted
                    logger.info(f"  +{inserted} ({dups} dups), Total: {total_inserted}")
            except Exception as e:
                logger.warning(f"  Error: {e}")
    logger.info("=" * 70)
    logger.info(f"Done! Total jobs in DB: {db.get_job_count()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
