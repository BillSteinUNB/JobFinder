#!/usr/bin/env python3
"""Script to build/rebuild the vector index from jobs in the metadata database."""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection.schema import Job
from src.db.metadata_db import MetadataDB
from src.db.vector_db import VectorDB, build_job_metadata_for_chroma
from src.matching.embeddings import EmbeddingManager
from src.processing.text_cleaner import build_job_document, clean_job_text, is_text_too_short
from src.utils.logger import setup_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build vector index from jobs in metadata database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--batch-size-jobs",
        type=int,
        default=500,
        help="Number of jobs to process per batch from database",
    )
    parser.add_argument(
        "--batch-size-embed",
        type=int,
        default=64,
        help="Batch size for embedding generation",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Filter by source (e.g., 'adzuna')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of jobs to process",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing collection and rebuild from scratch",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def process_jobs_batch(
    jobs: list[Job],
    embedder: EmbeddingManager,
    batch_size_embed: int,
) -> tuple[list[str], list[str], list[list[float]], list[dict], int]:
    """
    Process a batch of jobs: clean, build documents, embed.

    Returns:
        Tuple of (ids, documents, embeddings, metadatas, skipped_count)
    """
    ids = []
    documents = []
    metadatas = []
    skipped = 0

    for job in jobs:
        # Clean the description
        clean_result = clean_job_text(job.description)

        # Build the document
        doc = build_job_document(
            title=job.title,
            company=job.company,
            location=job.location,
            description=clean_result.text,
        )

        # Skip if too short
        if is_text_too_short(doc, min_chars=100):
            skipped += 1
            continue

        ids.append(job.id)
        documents.append(doc)
        metadatas.append(build_job_metadata_for_chroma(job))

    # Generate embeddings for valid documents
    if documents:
        embeddings_array = embedder.embed_texts(
            documents,
            batch_size=batch_size_embed,
            show_progress=False,
        )
        embeddings = [emb.tolist() for emb in embeddings_array]
    else:
        embeddings = []

    return ids, documents, embeddings, metadatas, skipped


def main() -> int:
    """Main entry point for vector index building."""
    args = parse_args()

    # Setup logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=level)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Vector Index Builder")
    logger.info("=" * 60)

    start_time = time.time()

    # Initialize components
    logger.info("Initializing components...")
    mdb = MetadataDB()
    embedder = EmbeddingManager()

    # Get embedding config (this loads the model)
    embed_config = embedder.config()
    logger.info(f"Embedding config: {embed_config}")

    # Initialize vector database
    vdb = VectorDB(embedding_version=embed_config.version_id)

    # Handle rebuild
    if args.rebuild:
        logger.warning("Rebuild requested - deleting existing collection")
        vdb.delete_collection()
        vdb = VectorDB(embedding_version=embed_config.version_id)

    # Get existing indexed IDs
    existing_ids = vdb.get_all_ids()
    logger.info(f"Existing vectors in index: {len(existing_ids)}")

    # Get total job count
    total_jobs = mdb.get_job_count(source=args.source)
    logger.info(f"Total jobs in metadata DB: {total_jobs}")

    if total_jobs == 0:
        logger.warning("No jobs found in metadata database. Run collect_jobs.py first.")
        return 0

    # Process jobs in batches
    batch_size = args.batch_size_jobs
    limit = args.limit or total_jobs
    offset = 0

    total_indexed = 0
    total_skipped = 0
    total_already_indexed = 0

    while offset < limit:
        # Fetch batch from database
        jobs = mdb.get_all_jobs(
            limit=min(batch_size, limit - offset),
            offset=offset,
            source=args.source,
        )

        if not jobs:
            break

        # Filter out already indexed jobs (unless rebuilding)
        if not args.rebuild:
            jobs_to_process = [j for j in jobs if j.id not in existing_ids]
            already_indexed = len(jobs) - len(jobs_to_process)
            total_already_indexed += already_indexed
        else:
            jobs_to_process = jobs

        if jobs_to_process:
            # Process batch
            ids, documents, embeddings, metadatas, skipped = process_jobs_batch(
                jobs_to_process,
                embedder,
                args.batch_size_embed,
            )

            # Upsert to vector database
            if ids:
                vdb.upsert_jobs(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                total_indexed += len(ids)

            total_skipped += skipped

        offset += len(jobs)
        logger.info(
            f"Progress: {offset}/{limit} jobs processed, "
            f"{total_indexed} indexed, {total_skipped} skipped"
        )

    # Final summary
    elapsed = time.time() - start_time
    info = vdb.info()

    logger.info("=" * 60)
    logger.info("Vector Index Build Complete!")
    logger.info(f"Time elapsed: {elapsed:.1f}s")
    logger.info(f"Jobs indexed this run: {total_indexed}")
    logger.info(f"Jobs skipped (too short): {total_skipped}")
    logger.info(f"Jobs already in index: {total_already_indexed}")
    logger.info(f"Total vectors in index: {info.count}")
    logger.info(f"Collection: {info.collection_name}")
    logger.info(f"Embedding version: {info.embedding_version}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
