"""Integration tests for the search pipeline.

These tests verify the end-to-end flow from resume input to scored job results.
They test how multiple components work together.

Marked as slow tests since they may load ML models.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.data_collection.schema import Job
from src.db.metadata_db import MetadataDB
from src.db.vector_db import VectorDB, build_job_metadata_for_chroma
from src.matching.evidence import EvidenceExtractor, EvidenceResult
from src.matching.scorer import HybridScorer, ResumeProfile, ScoredJob
from src.processing.text_cleaner import build_job_document, clean_job_text, extract_skills_simple


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def integration_temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for integration test files."""
    return tmp_path


@pytest.fixture
def metadata_db(integration_temp_dir: Path) -> Generator[MetadataDB, None, None]:
    """Create a temporary MetadataDB for testing."""
    db_path = integration_temp_dir / "test_jobs.db"
    db = MetadataDB(db_path=db_path)
    yield db


@pytest.fixture
def sample_jobs_for_integration() -> list[Job]:
    """Create a diverse set of jobs for integration testing."""
    base_time = datetime.now(timezone.utc)
    
    return [
        Job(
            id="job_python_1",
            source="test",
            source_id="py1",
            title="Senior Python Developer",
            company="TechCorp",
            location="San Francisco, CA",
            description="""
            We are looking for a Senior Python Developer to join our team.
            
            Requirements:
            - 5+ years of Python experience
            - Experience with Django or FastAPI
            - Knowledge of PostgreSQL and Redis
            - Docker and Kubernetes experience
            - AWS or cloud experience preferred
            
            You'll work on building scalable microservices.
            """,
            url="https://example.com/job/py1",
            salary_min=150000.0,
            salary_max=200000.0,
            posted_at=base_time - timedelta(days=2),
        ),
        Job(
            id="job_ml_1",
            source="test",
            source_id="ml1",
            title="Machine Learning Engineer",
            company="AI Startup",
            location="Remote",
            description="""
            ML Engineer needed for NLP projects.
            
            Requirements:
            - Python and machine learning experience
            - PyTorch or TensorFlow
            - Experience with deep learning and NLP
            - Knowledge of scikit-learn and pandas
            - Computer vision experience is a plus
            """,
            url="https://example.com/job/ml1",
            salary_min=160000.0,
            salary_max=220000.0,
            posted_at=base_time - timedelta(days=5),
        ),
        Job(
            id="job_frontend_1",
            source="test",
            source_id="fe1",
            title="Frontend Developer",
            company="Web Agency",
            location="Austin, TX",
            description="""
            React developer needed.
            
            Requirements:
            - JavaScript and TypeScript
            - React and Redux experience
            - HTML, CSS knowledge
            - Node.js experience helpful
            """,
            url="https://example.com/job/fe1",
            salary_min=100000.0,
            salary_max=140000.0,
            posted_at=base_time - timedelta(days=10),
        ),
        Job(
            id="job_devops_1",
            source="test",
            source_id="do1",
            title="DevOps Engineer",
            company="CloudCo",
            location="New York, NY",
            description="""
            DevOps engineer for cloud infrastructure.
            
            Requirements:
            - AWS or Azure or GCP experience
            - Docker and Kubernetes
            - Terraform and CI/CD
            - Python or Go scripting
            - Linux administration
            """,
            url="https://example.com/job/do1",
            salary_min=140000.0,
            salary_max=180000.0,
            posted_at=base_time - timedelta(days=1),
        ),
    ]


@pytest.fixture
def python_developer_resume() -> str:
    """Create a Python developer resume for testing."""
    return """
    Jane Smith
    Senior Software Engineer
    
    Summary:
    Experienced backend developer with 7 years of Python expertise.
    Specializing in web development, APIs, and cloud infrastructure.
    
    Skills:
    - Python, Django, FastAPI, Flask
    - PostgreSQL, Redis, MongoDB
    - Docker, Kubernetes, AWS
    - Git, CI/CD, Agile
    - REST APIs, GraphQL
    
    Experience:
    
    Senior Backend Engineer at TechStartup (2019-Present)
    - Built microservices architecture using Python and FastAPI
    - Deployed applications on AWS using Docker and Kubernetes
    - Optimized PostgreSQL queries for high-traffic systems
    
    Software Engineer at WebCompany (2016-2019)
    - Developed Django applications
    - Implemented REST APIs for mobile clients
    - Worked with Redis for caching
    
    Education:
    BS Computer Science, University of Technology, 2016
    """


@pytest.fixture
def python_resume_profile(python_developer_resume: str) -> ResumeProfile:
    """Create a ResumeProfile from the Python developer resume."""
    cleaned = clean_job_text(python_developer_resume).text
    skills = set(extract_skills_simple(cleaned))
    
    return ResumeProfile(
        raw_text=python_developer_resume,
        clean_text=cleaned,
        skills=skills,
        embedding=[0.1] * 384,  # Mock embedding
        preferred_location="San Francisco, CA",
        min_salary=140000.0,
    )


# =============================================================================
# Integration Tests: MetadataDB + Jobs
# =============================================================================


class TestMetadataDBIntegration:
    """Integration tests for MetadataDB with real job data."""

    def test_store_and_retrieve_jobs(
        self,
        metadata_db: MetadataDB,
        sample_jobs_for_integration: list[Job],
    ):
        """Test storing and retrieving jobs from MetadataDB."""
        # Store jobs
        inserted, duplicates = metadata_db.insert_jobs(sample_jobs_for_integration)
        assert inserted == len(sample_jobs_for_integration)
        assert duplicates == 0

        # Retrieve all jobs
        retrieved = metadata_db.get_all_jobs()
        assert len(retrieved) == len(sample_jobs_for_integration)

        # Verify job data integrity
        for original in sample_jobs_for_integration:
            fetched = metadata_db.get_job(original.id)
            assert fetched is not None
            assert fetched.title == original.title
            assert fetched.company == original.company
            assert fetched.description == original.description

    def test_bulk_fetch_by_ids(
        self,
        metadata_db: MetadataDB,
        sample_jobs_for_integration: list[Job],
    ):
        """Test bulk fetching jobs by IDs."""
        metadata_db.insert_jobs(sample_jobs_for_integration)

        # Fetch subset
        ids_to_fetch = ["job_python_1", "job_ml_1"]
        jobs = metadata_db.get_jobs_by_ids(ids_to_fetch)

        assert len(jobs) == 2
        assert jobs["job_python_1"].title == "Senior Python Developer"
        assert jobs["job_ml_1"].title == "Machine Learning Engineer"

    def test_labeling_workflow(
        self,
        metadata_db: MetadataDB,
        sample_jobs_for_integration: list[Job],
    ):
        """Test the save/reject labeling workflow."""
        metadata_db.insert_jobs(sample_jobs_for_integration)

        # Save a job (1 = interested/saved)
        metadata_db.update_label("job_python_1", 1)
        saved_job = metadata_db.get_job("job_python_1")
        assert saved_job is not None
        assert saved_job.label == 1

        # Reject a job (0 = not interested/rejected)
        metadata_db.update_label("job_frontend_1", 0)
        rejected_job = metadata_db.get_job("job_frontend_1")
        assert rejected_job is not None
        assert rejected_job.label == 0

        # Clear label (None = no label)
        metadata_db.update_label("job_python_1", None)
        cleared_job = metadata_db.get_job("job_python_1")
        assert cleared_job is not None
        assert cleared_job.label is None


# =============================================================================
# Integration Tests: Scorer Pipeline
# =============================================================================


class TestScorerPipeline:
    """Integration tests for the scoring pipeline."""

    def test_score_jobs_end_to_end(
        self,
        sample_jobs_for_integration: list[Job],
        python_resume_profile: ResumeProfile,
    ):
        """Test scoring jobs end-to-end."""
        scorer = HybridScorer()

        # Simulate distances from vector search (lower = more similar)
        # Python job should be most similar
        distances = [0.2, 0.3, 0.6, 0.4]

        scored_jobs = scorer.score_jobs(
            sample_jobs_for_integration,
            distances,
            python_resume_profile,
        )

        assert len(scored_jobs) == 4

        # All should be ScoredJob instances
        for scored in scored_jobs:
            assert isinstance(scored, ScoredJob)
            assert 0.0 <= scored.total_score <= 1.0
            assert scored.explanation
            assert isinstance(scored.matched_skills, list)

    def test_python_job_ranks_highest(
        self,
        sample_jobs_for_integration: list[Job],
        python_resume_profile: ResumeProfile,
    ):
        """Test that Python job ranks highest for Python developer profile."""
        scorer = HybridScorer()

        # Python job has lowest distance (most similar)
        distances = [0.15, 0.35, 0.7, 0.45]

        scored_jobs = scorer.score_jobs(
            sample_jobs_for_integration,
            distances,
            python_resume_profile,
        )

        # First result should be the Python job (sorted by score)
        assert scored_jobs[0].job.id == "job_python_1"

        # Python job should have matched skills
        assert len(scored_jobs[0].matched_skills) > 0
        assert "python" in scored_jobs[0].matched_skills

    def test_skill_matching_accuracy(
        self,
        sample_jobs_for_integration: list[Job],
        python_resume_profile: ResumeProfile,
    ):
        """Test that skill matching is accurate."""
        scorer = HybridScorer()

        # Score just the Python job
        python_job = sample_jobs_for_integration[0]
        scored = scorer.score_job(
            python_job,
            chroma_distance=0.2,
            resume_profile=python_resume_profile,
        )

        # Should match these skills (in both resume and job)
        expected_matches = {"python", "django", "fastapi", "postgresql", "redis", "docker", "kubernetes", "aws"}
        actual_matches = set(scored.matched_skills)

        # At least some expected skills should match
        assert len(actual_matches & expected_matches) >= 4

    def test_location_preference_affects_score(
        self,
        sample_jobs_for_integration: list[Job],
    ):
        """Test that location preference affects scoring."""
        scorer = HybridScorer()

        # Profile preferring San Francisco
        sf_profile = ResumeProfile(
            raw_text="test",
            clean_text="Python developer",
            skills={"python"},
            preferred_location="San Francisco, CA",
        )

        # Profile preferring Remote
        remote_profile = ResumeProfile(
            raw_text="test",
            clean_text="Python developer",
            skills={"python"},
            preferred_location="Remote",
        )

        python_job = sample_jobs_for_integration[0]  # SF location
        ml_job = sample_jobs_for_integration[1]  # Remote location

        # Score SF job for SF preference
        sf_scored = scorer.score_job(python_job, 0.3, sf_profile)

        # Score Remote job for Remote preference  
        remote_scored = scorer.score_job(ml_job, 0.3, remote_profile)

        # Both should have high location scores (1.0 for exact/remote match)
        assert sf_scored.breakdown["location"] == 1.0
        assert remote_scored.breakdown["location"] == 1.0

    def test_salary_matching(
        self,
        sample_jobs_for_integration: list[Job],
    ):
        """Test salary matching logic."""
        scorer = HybridScorer()

        # Profile with high salary requirement
        high_salary_profile = ResumeProfile(
            raw_text="test",
            clean_text="Developer",
            skills={"python"},
            min_salary=200000.0,
        )

        python_job = sample_jobs_for_integration[0]  # 150k-200k
        frontend_job = sample_jobs_for_integration[2]  # 100k-140k

        high_scored = scorer.score_job(python_job, 0.3, high_salary_profile)
        low_scored = scorer.score_job(frontend_job, 0.3, high_salary_profile)

        # Python job meets salary (mid=175k, close to 200k)
        # Frontend job doesn't (mid=120k vs 200k required)
        assert high_scored.breakdown["salary"] > low_scored.breakdown["salary"]


# =============================================================================
# Integration Tests: Evidence Extraction
# =============================================================================


class TestEvidenceExtraction:
    """Integration tests for evidence extraction."""

    def test_extract_evidence_for_match(
        self,
        python_developer_resume: str,
        sample_jobs_for_integration: list[Job],
    ):
        """Test evidence extraction for a job match."""
        extractor = EvidenceExtractor()

        python_job = sample_jobs_for_integration[0]
        cleaned_resume = clean_job_text(python_developer_resume).text
        cleaned_job = clean_job_text(python_job.description).text

        result = extractor.extract_evidence(
            job_id=python_job.id,
            resume_text=cleaned_resume,
            job_text=cleaned_job,
        )

        assert isinstance(result, EvidenceResult)
        assert result.job_id == python_job.id

        # Should find skill matches
        assert len(result.skill_matches) > 0
        assert "python" in result.skill_matches

        # Should find keyword matches
        assert len(result.keyword_matches) > 0

    def test_evidence_batch_extraction(
        self,
        python_developer_resume: str,
        sample_jobs_for_integration: list[Job],
    ):
        """Test batch evidence extraction."""
        extractor = EvidenceExtractor()

        cleaned_resume = clean_job_text(python_developer_resume).text

        job_ids = [job.id for job in sample_jobs_for_integration]
        job_texts = [
            clean_job_text(job.description).text
            for job in sample_jobs_for_integration
        ]

        results = extractor.extract_evidence_batch(
            job_ids=job_ids,
            resume_text=cleaned_resume,
            job_texts=job_texts,
        )

        assert len(results) == len(sample_jobs_for_integration)

        for job_id in job_ids:
            assert job_id in results
            assert isinstance(results[job_id], EvidenceResult)


# =============================================================================
# Integration Tests: Full Search Pipeline
# =============================================================================


class TestFullSearchPipeline:
    """Integration tests for the complete search pipeline."""

    def test_resume_to_scored_results_pipeline(
        self,
        metadata_db: MetadataDB,
        sample_jobs_for_integration: list[Job],
        python_developer_resume: str,
    ):
        """Test full pipeline: resume → query → scored results."""
        # Step 1: Store jobs in metadata DB
        metadata_db.insert_jobs(sample_jobs_for_integration)

        # Step 2: Process resume
        cleaned_resume = clean_job_text(python_developer_resume).text
        resume_skills = set(extract_skills_simple(cleaned_resume))

        resume_profile = ResumeProfile(
            raw_text=python_developer_resume,
            clean_text=cleaned_resume,
            skills=resume_skills,
            embedding=[0.1] * 384,
            preferred_location="San Francisco, CA",
            min_salary=140000.0,
        )

        # Step 3: Simulate vector search results
        # In real scenario, this would come from VectorDB
        job_ids = [job.id for job in sample_jobs_for_integration]
        mock_distances = [0.2, 0.35, 0.65, 0.4]

        # Step 4: Fetch jobs from metadata DB
        jobs_dict = metadata_db.get_jobs_by_ids(job_ids)
        jobs = [jobs_dict[jid] for jid in job_ids if jid in jobs_dict]

        # Step 5: Score jobs
        scorer = HybridScorer()
        scored_jobs = scorer.score_jobs(jobs, mock_distances, resume_profile)

        # Step 6: Extract evidence for top results
        extractor = EvidenceExtractor()
        top_3 = scored_jobs[:3]

        for scored in top_3:
            evidence = extractor.extract_evidence(
                job_id=scored.job.id,
                resume_text=cleaned_resume,
                job_text=scored.job.description,
            )
            assert evidence.job_id == scored.job.id

        # Verify pipeline results
        assert len(scored_jobs) == 4
        assert scored_jobs[0].total_score >= scored_jobs[-1].total_score

    def test_pipeline_with_user_feedback(
        self,
        metadata_db: MetadataDB,
        sample_jobs_for_integration: list[Job],
        python_resume_profile: ResumeProfile,
    ):
        """Test pipeline with user feedback (save/reject)."""
        # Store jobs
        metadata_db.insert_jobs(sample_jobs_for_integration)

        # Score jobs
        scorer = HybridScorer()
        distances = [0.2, 0.3, 0.5, 0.4]
        scored_jobs = scorer.score_jobs(
            sample_jobs_for_integration,
            distances,
            python_resume_profile,
        )

        # User saves top job (1 = interested)
        top_job_id = scored_jobs[0].job.id
        metadata_db.update_label(top_job_id, 1)

        # User rejects last job (0 = not interested)
        last_job_id = scored_jobs[-1].job.id
        metadata_db.update_label(last_job_id, 0)

        # Verify feedback persisted
        saved = metadata_db.get_job(top_job_id)
        assert saved is not None
        assert saved.label == 1

        rejected = metadata_db.get_job(last_job_id)
        assert rejected is not None
        assert rejected.label == 0

        # Unlabeled jobs should have None label
        unlabeled = metadata_db.get_job(scored_jobs[1].job.id)
        assert unlabeled is not None
        assert unlabeled.label is None


# =============================================================================
# Integration Tests: Text Processing Pipeline
# =============================================================================


class TestTextProcessingPipeline:
    """Integration tests for text processing pipeline."""

    def test_job_document_building(
        self,
        sample_jobs_for_integration: list[Job],
    ):
        """Test building job documents for embedding."""
        for job in sample_jobs_for_integration:
            # Clean description
            cleaned = clean_job_text(job.description)

            # Build document
            doc = build_job_document(
                title=job.title,
                company=job.company,
                location=job.location,
                description=cleaned.text,
            )

            # Verify structure
            assert f"Title: {job.title}" in doc
            assert f"Company: {job.company}" in doc
            assert f"Location: {job.location}" in doc
            assert "Description:" in doc

            # Verify content cleaned
            assert "<" not in doc  # No HTML tags

    def test_skill_extraction_consistency(
        self,
        python_developer_resume: str,
        sample_jobs_for_integration: list[Job],
    ):
        """Test that skill extraction is consistent across pipeline."""
        # Extract from resume
        resume_skills = set(extract_skills_simple(python_developer_resume))

        # Extract from Python job
        python_job = sample_jobs_for_integration[0]
        job_skills = set(extract_skills_simple(python_job.description))

        # Both should find Python
        assert "python" in resume_skills
        assert "python" in job_skills

        # Resume should have these skills
        assert "django" in resume_skills or "fastapi" in resume_skills
        assert "postgresql" in resume_skills
        assert "docker" in resume_skills


# =============================================================================
# Integration Tests: VectorDB (with mocked ChromaDB)
# =============================================================================


@pytest.mark.slow
class TestVectorDBIntegration:
    """Integration tests for VectorDB.
    
    These tests use a real ChromaDB instance but with temporary storage.
    Marked as slow since they involve disk I/O.
    """

    def test_upsert_and_query_workflow(
        self,
        integration_temp_dir: Path,
        sample_jobs_for_integration: list[Job],
    ):
        """Test upserting jobs and querying them."""
        # Create VectorDB
        vector_db = VectorDB(
            persist_dir=integration_temp_dir / "chroma",
            embedding_version="test_v1",
        )

        # Prepare data
        job_ids = [job.id for job in sample_jobs_for_integration]
        documents = [
            build_job_document(
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
            )
            for job in sample_jobs_for_integration
        ]
        metadatas = [
            build_job_metadata_for_chroma(job)
            for job in sample_jobs_for_integration
        ]

        # Create mock embeddings (384 dimensions like all-MiniLM-L6-v2)
        embeddings = [
            [float(i) / 384 for i in range(384)]  # Simple gradient embedding
            for _ in sample_jobs_for_integration
        ]

        # Upsert
        count = vector_db.upsert_jobs(
            ids=job_ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        assert count == len(sample_jobs_for_integration)

        # Verify count
        info = vector_db.info()
        assert info.count == len(sample_jobs_for_integration)

        # Query
        query_embedding = [float(i) / 384 for i in range(384)]
        results = vector_db.query(
            query_embedding=query_embedding,
            n_results=4,
        )

        assert len(results["ids"][0]) == 4
        assert len(results["distances"][0]) == 4

    def test_collection_per_version(
        self,
        integration_temp_dir: Path,
    ):
        """Test that different versions create different collections."""
        # Create two VectorDBs with different versions
        v1_db = VectorDB(
            persist_dir=integration_temp_dir / "chroma",
            embedding_version="version_1",
        )
        v2_db = VectorDB(
            persist_dir=integration_temp_dir / "chroma",
            embedding_version="version_2",
        )

        # They should have different collection names
        assert v1_db._collection_name != v2_db._collection_name
        assert "version_1" in v1_db._collection_name
        assert "version_2" in v2_db._collection_name
