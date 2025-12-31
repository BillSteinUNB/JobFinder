"""Unit tests for MetadataDB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.data_collection.schema import Job
from src.db.metadata_db import MetadataDB


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db(temp_db_path: Path) -> MetadataDB:
    """Create a fresh MetadataDB instance with temp database."""
    return MetadataDB(db_path=temp_db_path)


@pytest.fixture
def populated_db(db: MetadataDB, sample_jobs: list[Job]) -> MetadataDB:
    """Create a MetadataDB with sample jobs inserted."""
    db.insert_jobs(sample_jobs)
    return db


# =============================================================================
# Schema Initialization Tests
# =============================================================================


class TestSchemaInit:
    """Tests for database schema initialization."""

    def test_creates_database_file(self, temp_db_path: Path):
        """Database file should be created on init."""
        db = MetadataDB(db_path=temp_db_path)
        assert temp_db_path.exists()

    def test_creates_parent_directories(self, temp_dir: Path):
        """Should create parent directories if they don't exist."""
        nested_path = temp_dir / "nested" / "path" / "test.db"
        db = MetadataDB(db_path=nested_path)
        assert nested_path.exists()

    def test_schema_is_idempotent(self, temp_db_path: Path):
        """Initializing schema multiple times should not fail."""
        db1 = MetadataDB(db_path=temp_db_path)
        db2 = MetadataDB(db_path=temp_db_path)  # Re-init same path
        assert temp_db_path.exists()


# =============================================================================
# Insert Tests
# =============================================================================


class TestInsertJob:
    """Tests for single job insertion."""

    def test_insert_single_job(self, db: MetadataDB, sample_job: Job):
        """Should insert a single job successfully."""
        result = db.insert_job(sample_job)
        assert result is True

        # Verify it exists
        retrieved = db.get_job(sample_job.id)
        assert retrieved is not None
        assert retrieved.id == sample_job.id
        assert retrieved.title == sample_job.title

    def test_insert_duplicate_returns_false(self, db: MetadataDB, sample_job: Job):
        """Inserting duplicate job should return False."""
        db.insert_job(sample_job)
        result = db.insert_job(sample_job)
        assert result is False

    def test_insert_preserves_all_fields(self, db: MetadataDB, sample_job: Job):
        """All job fields should be preserved after insert/retrieve."""
        db.insert_job(sample_job)
        retrieved = db.get_job(sample_job.id)

        assert retrieved.source == sample_job.source
        assert retrieved.source_id == sample_job.source_id
        assert retrieved.title == sample_job.title
        assert retrieved.company == sample_job.company
        assert retrieved.location == sample_job.location
        assert retrieved.description == sample_job.description
        assert retrieved.url == sample_job.url
        assert retrieved.salary_min == sample_job.salary_min
        assert retrieved.salary_max == sample_job.salary_max
        assert retrieved.contract_type == sample_job.contract_type
        assert retrieved.contract_time == sample_job.contract_time
        assert retrieved.category == sample_job.category
        assert retrieved.latitude == sample_job.latitude
        assert retrieved.longitude == sample_job.longitude


class TestInsertJobs:
    """Tests for bulk job insertion."""

    def test_insert_multiple_jobs(self, db: MetadataDB, sample_jobs: list[Job]):
        """Should insert multiple jobs and return correct counts."""
        inserted, duplicates = db.insert_jobs(sample_jobs)

        assert inserted == len(sample_jobs)
        assert duplicates == 0
        assert db.get_job_count() == len(sample_jobs)

    def test_insert_with_duplicates(self, db: MetadataDB, sample_jobs: list[Job]):
        """Should handle duplicates correctly in bulk insert."""
        # Insert once
        db.insert_jobs(sample_jobs)

        # Insert again with some new jobs
        new_job = Job(
            id="new_job",
            source="test",
            source_id="new",
            title="New Job",
            company="New Corp",
            location="Remote",
            description="New job description",
            url="https://example.com/new",
            posted_at=datetime.now(timezone.utc),
        )
        mixed_jobs = sample_jobs + [new_job]

        inserted, duplicates = db.insert_jobs(mixed_jobs)

        assert inserted == 1  # Only new job
        assert duplicates == len(sample_jobs)

    def test_insert_empty_list(self, db: MetadataDB):
        """Inserting empty list should return zeros."""
        inserted, duplicates = db.insert_jobs([])
        assert inserted == 0
        assert duplicates == 0


# =============================================================================
# Retrieval Tests
# =============================================================================


class TestGetJob:
    """Tests for single job retrieval."""

    def test_get_existing_job(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should retrieve existing job by ID."""
        job_id = sample_jobs[0].id
        job = populated_db.get_job(job_id)

        assert job is not None
        assert job.id == job_id

    def test_get_nonexistent_job(self, populated_db: MetadataDB):
        """Should return None for nonexistent job."""
        job = populated_db.get_job("nonexistent_id")
        assert job is None


class TestGetJobsByIds:
    """Tests for bulk job retrieval."""

    def test_get_multiple_jobs(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should retrieve multiple jobs by IDs."""
        job_ids = [j.id for j in sample_jobs]
        result = populated_db.get_jobs_by_ids(job_ids)

        assert len(result) == len(sample_jobs)
        for job_id in job_ids:
            assert job_id in result
            assert result[job_id].id == job_id

    def test_get_partial_ids(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should return only found jobs when some IDs don't exist."""
        job_ids = [sample_jobs[0].id, "nonexistent_1", "nonexistent_2"]
        result = populated_db.get_jobs_by_ids(job_ids)

        assert len(result) == 1
        assert sample_jobs[0].id in result

    def test_get_empty_ids(self, populated_db: MetadataDB):
        """Should return empty dict for empty ID list."""
        result = populated_db.get_jobs_by_ids([])
        assert result == {}

    def test_preserves_job_data(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Bulk fetch should preserve all job data."""
        job_ids = [j.id for j in sample_jobs]
        result = populated_db.get_jobs_by_ids(job_ids)

        for original in sample_jobs:
            retrieved = result[original.id]
            assert retrieved.title == original.title
            assert retrieved.company == original.company


class TestGetAllJobs:
    """Tests for get_all_jobs with filtering."""

    def test_get_all_jobs(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should return all jobs."""
        jobs = populated_db.get_all_jobs()
        assert len(jobs) == len(sample_jobs)

    def test_get_all_with_limit(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should respect limit parameter."""
        jobs = populated_db.get_all_jobs(limit=1)
        assert len(jobs) == 1

    def test_get_all_with_offset(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should respect offset parameter."""
        all_jobs = populated_db.get_all_jobs()
        offset_jobs = populated_db.get_all_jobs(limit=10, offset=1)

        assert len(offset_jobs) == len(all_jobs) - 1

    def test_get_all_with_source_filter(self, db: MetadataDB):
        """Should filter by source."""
        job1 = Job(
            id="adzuna_1",
            source="adzuna",
            source_id="1",
            title="Job 1",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/1",
            posted_at=datetime.now(timezone.utc),
        )
        job2 = Job(
            id="linkedin_1",
            source="linkedin",
            source_id="1",
            title="Job 2",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/2",
            posted_at=datetime.now(timezone.utc),
        )
        db.insert_jobs([job1, job2])

        adzuna_jobs = db.get_all_jobs(source="adzuna")
        assert len(adzuna_jobs) == 1
        assert adzuna_jobs[0].source == "adzuna"

    def test_get_all_with_label_filter(self, db: MetadataDB, sample_job: Job):
        """Should filter by label."""
        db.insert_job(sample_job)
        db.update_label(sample_job.id, 1)

        labeled = db.get_all_jobs(label=1)
        unlabeled = db.get_all_jobs(label=0)

        assert len(labeled) == 1
        assert len(unlabeled) == 0


# =============================================================================
# Update Tests
# =============================================================================


class TestUpdateLabel:
    """Tests for updating job labels."""

    def test_update_label_to_interested(
        self, populated_db: MetadataDB, sample_jobs: list[Job]
    ):
        """Should update label to interested (1)."""
        job_id = sample_jobs[0].id
        result = populated_db.update_label(job_id, 1)

        assert result is True
        job = populated_db.get_job(job_id)
        assert job.label == 1

    def test_update_label_to_not_interested(
        self, populated_db: MetadataDB, sample_jobs: list[Job]
    ):
        """Should update label to not interested (0)."""
        job_id = sample_jobs[0].id
        result = populated_db.update_label(job_id, 0)

        assert result is True
        job = populated_db.get_job(job_id)
        assert job.label == 0

    def test_clear_label(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should clear label by setting to None."""
        job_id = sample_jobs[0].id
        populated_db.update_label(job_id, 1)
        result = populated_db.update_label(job_id, None)

        assert result is True
        job = populated_db.get_job(job_id)
        assert job.label is None

    def test_update_nonexistent_returns_false(self, populated_db: MetadataDB):
        """Updating nonexistent job should return False."""
        result = populated_db.update_label("nonexistent", 1)
        assert result is False


# =============================================================================
# Delete Tests
# =============================================================================


class TestDeleteOldJobs:
    """Tests for deleting old jobs."""

    def test_delete_old_jobs(self, db: MetadataDB):
        """Should delete jobs older than specified days."""
        now = datetime.now(timezone.utc)
        old_job = Job(
            id="old_job",
            source="test",
            source_id="old",
            title="Old Job",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/old",
            posted_at=now - timedelta(days=60),
        )
        new_job = Job(
            id="new_job",
            source="test",
            source_id="new",
            title="New Job",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/new",
            posted_at=now - timedelta(days=5),
        )
        db.insert_jobs([old_job, new_job])

        deleted = db.delete_old_jobs(days=30)

        assert deleted == 1
        assert db.get_job("old_job") is None
        assert db.get_job("new_job") is not None

    def test_delete_old_jobs_none_to_delete(
        self, populated_db: MetadataDB, sample_jobs: list[Job]
    ):
        """Should return 0 when no old jobs exist."""
        deleted = populated_db.delete_old_jobs(days=30)
        assert deleted == 0


# =============================================================================
# Utility Method Tests
# =============================================================================


class TestJobExists:
    """Tests for job_exists method."""

    def test_job_exists_true(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should return True for existing job."""
        job = sample_jobs[0]
        assert populated_db.job_exists(job.source, job.source_id) is True

    def test_job_exists_false(self, populated_db: MetadataDB):
        """Should return False for nonexistent job."""
        assert populated_db.job_exists("fake", "fake_id") is False


class TestGetJobIds:
    """Tests for get_job_ids method."""

    def test_get_all_ids(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should return all job IDs."""
        ids = populated_db.get_job_ids()
        assert len(ids) == len(sample_jobs)
        for job in sample_jobs:
            assert job.id in ids

    def test_get_ids_by_source(self, db: MetadataDB):
        """Should filter IDs by source."""
        job1 = Job(
            id="adzuna_1",
            source="adzuna",
            source_id="1",
            title="Job 1",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/1",
            posted_at=datetime.now(timezone.utc),
        )
        job2 = Job(
            id="linkedin_1",
            source="linkedin",
            source_id="1",
            title="Job 2",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/2",
            posted_at=datetime.now(timezone.utc),
        )
        db.insert_jobs([job1, job2])

        adzuna_ids = db.get_job_ids(source="adzuna")
        assert len(adzuna_ids) == 1
        assert "adzuna_1" in adzuna_ids


class TestGetJobCount:
    """Tests for get_job_count method."""

    def test_count_all_jobs(self, populated_db: MetadataDB, sample_jobs: list[Job]):
        """Should return total job count."""
        count = populated_db.get_job_count()
        assert count == len(sample_jobs)

    def test_count_by_source(self, db: MetadataDB):
        """Should count jobs by source."""
        job1 = Job(
            id="adzuna_1",
            source="adzuna",
            source_id="1",
            title="Job 1",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/1",
            posted_at=datetime.now(timezone.utc),
        )
        job2 = Job(
            id="linkedin_1",
            source="linkedin",
            source_id="1",
            title="Job 2",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/2",
            posted_at=datetime.now(timezone.utc),
        )
        db.insert_jobs([job1, job2])

        assert db.get_job_count(source="adzuna") == 1
        assert db.get_job_count(source="linkedin") == 1
        assert db.get_job_count() == 2

    def test_count_empty_db(self, db: MetadataDB):
        """Should return 0 for empty database."""
        assert db.get_job_count() == 0


# =============================================================================
# Timezone Handling Tests
# =============================================================================


class TestTimezoneHandling:
    """Tests for timezone-aware datetime handling."""

    def test_preserves_utc_timezone(self, db: MetadataDB):
        """Should preserve UTC timezone on dates."""
        utc_time = datetime.now(timezone.utc)
        job = Job(
            id="tz_test",
            source="test",
            source_id="tz",
            title="TZ Test",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/tz",
            posted_at=utc_time,
            created_at=utc_time,
        )
        db.insert_job(job)

        retrieved = db.get_job("tz_test")

        assert retrieved.posted_at.tzinfo is not None
        assert retrieved.created_at.tzinfo is not None

    def test_handles_naive_datetime(self, db: MetadataDB):
        """Should handle naive datetime by assuming UTC."""
        naive_time = datetime(2024, 1, 15, 12, 0, 0)
        job = Job(
            id="naive_test",
            source="test",
            source_id="naive",
            title="Naive Test",
            company="Corp",
            location="NYC",
            description="Desc",
            url="https://example.com/naive",
            posted_at=naive_time,
        )
        db.insert_job(job)

        retrieved = db.get_job("naive_test")

        # Should now be UTC-aware
        assert retrieved.posted_at.tzinfo is not None
