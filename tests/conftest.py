"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest

from src.data_collection.schema import Job


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test_jobs.db"


@pytest.fixture
def temp_chroma_dir(temp_dir: Path) -> Path:
    """Create a temporary ChromaDB directory."""
    chroma_dir = temp_dir / "chromadb"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chroma_dir


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_job() -> Job:
    """Create a sample job for testing."""
    return Job(
        id="test_123",
        source="test",
        source_id="123",
        title="Senior Python Developer",
        company="TechCorp",
        location="San Francisco, CA",
        description="""
        We are looking for a Senior Python Developer to join our team.
        
        Requirements:
        - 5+ years of Python experience
        - Experience with Django or FastAPI
        - Knowledge of PostgreSQL and Redis
        - Familiarity with Docker and Kubernetes
        - Strong problem-solving skills
        
        Nice to have:
        - Experience with machine learning
        - AWS or GCP experience
        """,
        url="https://example.com/job/123",
        salary_min=150000.0,
        salary_max=200000.0,
        contract_type="permanent",
        contract_time="full_time",
        category="IT Jobs",
        latitude=37.7749,
        longitude=-122.4194,
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_jobs() -> list[Job]:
    """Create multiple sample jobs for testing."""
    base_time = datetime.now(timezone.utc)
    
    return [
        Job(
            id="job_1",
            source="test",
            source_id="1",
            title="Python Developer",
            company="Company A",
            location="New York, NY",
            description="Python developer needed. Experience with Django required. Must know SQL.",
            url="https://example.com/job/1",
            salary_min=100000.0,
            salary_max=130000.0,
            posted_at=base_time,
        ),
        Job(
            id="job_2",
            source="test",
            source_id="2",
            title="Data Scientist",
            company="Company B",
            location="Remote",
            description="Data scientist role. Python, machine learning, pandas, scikit-learn required.",
            url="https://example.com/job/2",
            salary_min=120000.0,
            salary_max=160000.0,
            posted_at=base_time,
        ),
        Job(
            id="job_3",
            source="test",
            source_id="3",
            title="Frontend Developer",
            company="Company C",
            location="Austin, TX",
            description="React and TypeScript developer. Experience with Node.js a plus.",
            url="https://example.com/job/3",
            salary_min=90000.0,
            salary_max=120000.0,
            posted_at=base_time,
        ),
    ]


@pytest.fixture
def sample_resume_text() -> str:
    """Create sample resume text for testing."""
    return """
    John Doe
    Senior Software Engineer
    
    Summary:
    Experienced software engineer with 8 years of Python development experience.
    Strong background in web development, machine learning, and cloud infrastructure.
    
    Skills:
    - Python, JavaScript, TypeScript
    - Django, FastAPI, Flask
    - PostgreSQL, MongoDB, Redis
    - Docker, Kubernetes, AWS
    - Machine Learning, TensorFlow, PyTorch
    - Git, CI/CD, Agile
    
    Experience:
    
    Senior Software Engineer at TechStartup (2020-Present)
    - Led development of microservices architecture using Python and FastAPI
    - Implemented machine learning pipeline for recommendation system
    - Managed AWS infrastructure using Terraform
    
    Software Engineer at BigCorp (2016-2020)
    - Developed web applications using Django and React
    - Optimized database queries reducing response time by 50%
    - Mentored junior developers and conducted code reviews
    
    Education:
    BS in Computer Science, University of Technology, 2016
    """


@pytest.fixture
def sample_job_description() -> str:
    """Create sample job description for testing."""
    return """
    Senior Python Developer
    
    About the Role:
    We are seeking a talented Senior Python Developer to join our growing team.
    You will work on challenging projects involving web development and machine learning.
    
    Requirements:
    - 5+ years of experience with Python
    - Strong experience with Django or FastAPI frameworks
    - Experience with PostgreSQL or MySQL databases
    - Familiarity with Docker and container orchestration
    - Knowledge of RESTful API design
    
    Nice to Have:
    - Experience with machine learning libraries (TensorFlow, PyTorch)
    - AWS or GCP cloud experience
    - Kubernetes experience
    
    Benefits:
    - Competitive salary ($150,000 - $200,000)
    - Remote work options
    - Health insurance
    - 401k matching
    
    Apply now to join our team!
    """
