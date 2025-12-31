"""SQLite database handler for job metadata storage."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from src.data_collection.schema import Job
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataDB:
    """
    SQLite database handler for storing job metadata.

    Handles schema creation, CRUD operations, and deduplication.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT NOT NULL,
        url TEXT NOT NULL,
        salary_min REAL,
        salary_max REAL,
        contract_type TEXT,
        contract_time TEXT,
        category TEXT,
        latitude REAL,
        longitude REAL,
        posted_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        label INTEGER,
        UNIQUE(source, source_id)
    );

    CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
    CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at);
    CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
    CREATE INDEX IF NOT EXISTS idx_jobs_label ON jobs(label);
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize the database connection.

        Args:
            db_path: Path to SQLite database file (defaults to config)
        """
        settings = get_settings()
        self.db_path = db_path or settings.metadata_db_path

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
        logger.info(f"Database initialized at {self.db_path}")

    def insert_job(self, job: Job) -> bool:
        """
        Insert a single job into the database.

        Args:
            job: Job model to insert

        Returns:
            True if inserted, False if duplicate (already exists)
        """
        sql = """
        INSERT OR IGNORE INTO jobs (
            id, source, source_id, title, company, location, description,
            url, salary_min, salary_max, contract_type, contract_time,
            category, latitude, longitude, posted_at, created_at, label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    job.id,
                    job.source,
                    job.source_id,
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    job.salary_min,
                    job.salary_max,
                    job.contract_type,
                    job.contract_time,
                    job.category,
                    job.latitude,
                    job.longitude,
                    job.posted_at.isoformat(),
                    job.created_at.isoformat(),
                    job.label,
                ),
            )
            return cursor.rowcount > 0

    def insert_jobs(self, jobs: list[Job]) -> tuple[int, int]:
        """
        Bulk insert jobs with deduplication.

        Args:
            jobs: List of Job models to insert

        Returns:
            Tuple of (inserted_count, duplicate_count)
        """
        inserted = 0
        duplicates = 0

        sql = """
        INSERT OR IGNORE INTO jobs (
            id, source, source_id, title, company, location, description,
            url, salary_min, salary_max, contract_type, contract_time,
            category, latitude, longitude, posted_at, created_at, label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self._get_connection() as conn:
            for job in jobs:
                cursor = conn.execute(
                    sql,
                    (
                        job.id,
                        job.source,
                        job.source_id,
                        job.title,
                        job.company,
                        job.location,
                        job.description,
                        job.url,
                        job.salary_min,
                        job.salary_max,
                        job.contract_type,
                        job.contract_time,
                        job.category,
                        job.latitude,
                        job.longitude,
                        job.posted_at.isoformat(),
                        job.created_at.isoformat(),
                        job.label,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    duplicates += 1

        logger.info(f"Inserted {inserted} jobs, skipped {duplicates} duplicates")
        return inserted, duplicates

    def get_job(self, job_id: str) -> Job | None:
        """Get a single job by ID."""
        sql = "SELECT * FROM jobs WHERE id = ?"
        with self._get_connection() as conn:
            row = conn.execute(sql, (job_id,)).fetchone()
            if row:
                return self._row_to_job(row)
            return None

    def get_jobs_by_ids(self, job_ids: list[str]) -> dict[str, Job]:
        """
        Bulk fetch jobs by IDs.

        Args:
            job_ids: List of job IDs to fetch

        Returns:
            Dict mapping job_id -> Job for rows found
        """
        if not job_ids:
            return {}

        placeholders = ",".join(["?"] * len(job_ids))
        sql = f"SELECT * FROM jobs WHERE id IN ({placeholders})"

        with self._get_connection() as conn:
            rows = conn.execute(sql, job_ids).fetchall()
            jobs = [self._row_to_job(row) for row in rows]
            return {job.id: job for job in jobs}

    def get_all_jobs(
        self,
        limit: int | None = None,
        offset: int = 0,
        source: str | None = None,
        label: int | None = None,
    ) -> list[Job]:
        """
        Get jobs with optional filtering.

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            source: Filter by source (e.g., 'adzuna')
            label: Filter by user label (1=interested, 0=not)

        Returns:
            List of Job models
        """
        conditions = []
        params: list = []

        if source:
            conditions.append("source = ?")
            params.append(source)
        if label is not None:
            conditions.append("label = ?")
            params.append(label)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM jobs WHERE {where_clause} ORDER BY posted_at DESC"

        if limit:
            sql += f" LIMIT {limit} OFFSET {offset}"

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_job(row) for row in rows]

    def get_job_count(self, source: str | None = None) -> int:
        """Get total number of jobs in database."""
        if source:
            sql = "SELECT COUNT(*) FROM jobs WHERE source = ?"
            params = (source,)
        else:
            sql = "SELECT COUNT(*) FROM jobs"
            params = ()

        with self._get_connection() as conn:
            result = conn.execute(sql, params).fetchone()
            return result[0] if result else 0

    def update_label(self, job_id: str, label: int | None) -> bool:
        """
        Update the user label for a job.

        Args:
            job_id: Job ID to update
            label: New label value (1=interested, 0=not interested, None=clear)

        Returns:
            True if updated, False if job not found
        """
        sql = "UPDATE jobs SET label = ? WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (label, job_id))
            return cursor.rowcount > 0

    def delete_old_jobs(self, days: int = 30) -> int:
        """
        Delete jobs older than specified days.

        Args:
            days: Delete jobs posted more than this many days ago

        Returns:
            Number of deleted jobs
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        sql = "DELETE FROM jobs WHERE posted_at < ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (cutoff.isoformat(),))
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} jobs older than {days} days")
            return deleted

    def job_exists(self, source: str, source_id: str) -> bool:
        """Check if a job already exists by source and source_id."""
        sql = "SELECT 1 FROM jobs WHERE source = ? AND source_id = ? LIMIT 1"
        with self._get_connection() as conn:
            result = conn.execute(sql, (source, source_id)).fetchone()
            return result is not None

    def get_job_ids(self, source: str | None = None) -> set[str]:
        """Get all job IDs (useful for deduplication checks)."""
        if source:
            sql = "SELECT id FROM jobs WHERE source = ?"
            params = (source,)
        else:
            sql = "SELECT id FROM jobs"
            params = ()

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return {row[0] for row in rows}

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        """Ensure datetime is UTC-aware."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        """Convert a database row to a Job model."""
        posted = datetime.fromisoformat(row["posted_at"])
        created = datetime.fromisoformat(row["created_at"])
        return Job(
            id=row["id"],
            source=row["source"],
            source_id=row["source_id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            url=row["url"],
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            contract_type=row["contract_type"],
            contract_time=row["contract_time"],
            category=row["category"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            posted_at=MetadataDB._ensure_utc(posted),
            created_at=MetadataDB._ensure_utc(created),
            label=row["label"],
        )
