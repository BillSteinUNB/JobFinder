"""ChromaDB vector database operations for job embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence, TYPE_CHECKING

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.data_collection.schema import Job
from src.utils.config import get_settings
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from chromadb import Collection

logger = get_logger(__name__)


@dataclass(frozen=True)
class VectorIndexInfo:
    """Information about the vector index."""

    collection_name: str
    persist_dir: str
    embedding_version: str
    count: int

    def __str__(self) -> str:
        return (
            f"VectorIndex(collection={self.collection_name}, "
            f"version={self.embedding_version}, count={self.count})"
        )


def build_job_metadata_for_chroma(job: Job) -> dict[str, Any]:
    """
    Build metadata dict for storing a job in ChromaDB.

    Only includes JSON-serializable types (str, int, float, bool).

    Args:
        job: Job model

    Returns:
        Metadata dictionary
    """
    metadata = {
        "job_id": job.id,
        "source": job.source,
        "source_id": job.source_id,
        "company": job.company,
        "location": job.location,
        "category": job.category or "",
        "posted_at": job.posted_at.isoformat(),
    }

    # Add optional numeric fields
    if job.salary_min is not None:
        metadata["salary_min"] = float(job.salary_min)
    if job.salary_max is not None:
        metadata["salary_max"] = float(job.salary_max)

    return metadata


class VectorDB:
    """
    ChromaDB wrapper for job vector storage and search.

    Uses collection-per-embedding-version strategy to avoid
    mixing incompatible vectors.
    """

    def __init__(
        self,
        *,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None,
        embedding_version: str,
    ):
        """
        Initialize the vector database.

        Args:
            persist_dir: Directory for ChromaDB persistence (defaults to config)
            collection_name: Base collection name (defaults to config)
            embedding_version: Version ID for embeddings (required)
        """
        settings = get_settings()

        self._persist_dir = Path(persist_dir or settings.chroma_persist_dir)
        self._base_collection_name = collection_name or settings.chroma_collection
        self._embedding_version = embedding_version

        # Full collection name includes version
        self._collection_name = f"{self._base_collection_name}__{embedding_version}"

        # Ensure directory exists
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self._collection: "Collection | None" = None

        logger.info(
            f"VectorDB initialized: persist_dir={self._persist_dir}, "
            f"collection={self._collection_name}"
        )

    def get_or_create_collection(self) -> "Collection":
        """Get or create the vector collection."""
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={
                    "embedding_version": self._embedding_version,
                    "description": "Job embeddings for semantic search",
                    "hnsw:space": "cosine",
                },
            )
            logger.debug(f"Collection '{self._collection_name}' ready")
        return self._collection

    @property
    def collection(self) -> "Collection":
        """Get the collection (creates if needed)."""
        return self.get_or_create_collection()

    def info(self) -> VectorIndexInfo:
        """Get information about the vector index."""
        collection = self.get_or_create_collection()
        return VectorIndexInfo(
            collection_name=self._collection_name,
            persist_dir=str(self._persist_dir),
            embedding_version=self._embedding_version,
            count=collection.count(),
        )

    def upsert_jobs(
        self,
        *,
        ids: Sequence[str],
        documents: Sequence[str],
        embeddings: Sequence[Sequence[float]] | None = None,
        metadatas: Sequence[dict[str, Any]],
        batch_size: int = 256,
    ) -> int:
        """
        Upsert jobs into the vector database.

        Args:
            ids: Job IDs (must match length of other sequences)
            documents: Document texts (for storage/display)
            embeddings: Pre-computed embeddings (optional if using Chroma's embedding)
            metadatas: Metadata dicts for each job
            batch_size: Number of items per batch

        Returns:
            Number of jobs upserted
        """
        if not ids:
            return 0

        n_items = len(ids)
        if len(documents) != n_items or len(metadatas) != n_items:
            raise ValueError("ids, documents, and metadatas must have same length")

        if embeddings is not None and len(embeddings) != n_items:
            raise ValueError("embeddings must have same length as ids")

        collection = self.get_or_create_collection()
        total_upserted = 0

        # Process in batches
        for i in range(0, n_items, batch_size):
            batch_end = min(i + batch_size, n_items)

            batch_ids = list(ids[i:batch_end])
            batch_docs = list(documents[i:batch_end])
            batch_meta = list(metadatas[i:batch_end])

            upsert_kwargs: dict[str, Any] = {
                "ids": batch_ids,
                "documents": batch_docs,
                "metadatas": batch_meta,
            }

            if embeddings is not None:
                batch_embeddings = [list(e) for e in embeddings[i:batch_end]]
                upsert_kwargs["embeddings"] = batch_embeddings

            collection.upsert(**upsert_kwargs)

            batch_count = len(batch_ids)
            total_upserted += batch_count
            logger.debug(f"Upserted batch {i // batch_size + 1}: {batch_count} items")

        logger.info(f"Upserted {total_upserted} jobs to vector index")
        return total_upserted

    def query(
        self,
        *,
        query_embedding: Sequence[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Query the vector database for similar jobs.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            where: Optional metadata filter (ChromaDB where clause)
            include: Fields to include in results (default: all)

        Returns:
            ChromaDB query results dict with keys:
            - ids: List of job IDs
            - distances: List of distances
            - metadatas: List of metadata dicts
            - documents: List of document texts
        """
        collection = self.get_or_create_collection()

        if include is None:
            include = ["metadatas", "documents", "distances"]

        results = collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=n_results,
            where=where,
            include=include,
        )

        return results

    def query_by_text(
        self,
        *,
        query_text: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query using text (requires collection to have embedding function).

        Note: This only works if the collection was created with an
        embedding function. For our use case, prefer query() with
        pre-computed embeddings.
        """
        collection = self.get_or_create_collection()

        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["metadatas", "documents", "distances"],
        )

        return results

    def get_by_ids(self, ids: Sequence[str]) -> dict[str, Any]:
        """Get jobs by their IDs."""
        collection = self.get_or_create_collection()
        return collection.get(
            ids=list(ids),
            include=["metadatas", "documents"],
        )

    def delete_by_ids(self, ids: Sequence[str]) -> None:
        """Delete jobs by their IDs."""
        if not ids:
            return

        collection = self.get_or_create_collection()
        collection.delete(ids=list(ids))
        logger.info(f"Deleted {len(ids)} jobs from vector index")

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            self._client.delete_collection(self._collection_name)
            self._collection = None
            logger.info(f"Deleted collection '{self._collection_name}'")
        except ValueError:
            logger.warning(f"Collection '{self._collection_name}' does not exist")

    def get_all_ids(self) -> set[str]:
        """Get all job IDs in the collection."""
        collection = self.get_or_create_collection()
        result = collection.get(include=[])
        return set(result["ids"])

    def list_collections(self) -> list[str]:
        """List all collections in the database."""
        collections = self._client.list_collections()
        return [c.name for c in collections]
