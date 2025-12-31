"""Pydantic models for job data validation."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Adzuna API Response Models (mirrors exact API structure)
# ============================================================================


class AdzunaCompany(BaseModel):
    """Company information from Adzuna API."""

    display_name: str


class AdzunaLocation(BaseModel):
    """Location information from Adzuna API."""

    display_name: str
    area: list[str] = Field(default_factory=list)


class AdzunaCategory(BaseModel):
    """Job category from Adzuna API."""

    label: str
    tag: str


class AdzunaJob(BaseModel):
    """Single job posting from Adzuna API response."""

    id: str
    created: datetime
    title: str
    description: str
    redirect_url: str
    company: AdzunaCompany
    location: AdzunaLocation
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_is_predicted: int = 0
    category: AdzunaCategory
    contract_type: Optional[str] = None  # "permanent", "contract"
    contract_time: Optional[str] = None  # "full_time", "part_time"


class AdzunaSearchResponse(BaseModel):
    """Top-level response from Adzuna job search API."""

    count: int
    mean: Optional[float] = None
    results: list[AdzunaJob]


# ============================================================================
# Internal Job Model (normalized for our database)
# ============================================================================


class Job(BaseModel):
    """Normalized job model for internal storage."""

    id: str = Field(description="Unique ID: source + source_id (e.g., 'adzuna_123456')")
    source: str = Field(description="Data source (e.g., 'adzuna')")
    source_id: str = Field(description="Original ID from the source")
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    contract_type: Optional[str] = None
    contract_time: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    posted_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    label: Optional[int] = Field(default=None, description="User label: 1=interested, 0=not")

    @classmethod
    def from_adzuna(cls, adzuna_job: AdzunaJob) -> "Job":
        """Convert an Adzuna API job to our internal Job model."""
        return cls(
            id=f"adzuna_{adzuna_job.id}",
            source="adzuna",
            source_id=adzuna_job.id,
            title=adzuna_job.title,
            company=adzuna_job.company.display_name,
            location=adzuna_job.location.display_name,
            description=adzuna_job.description,
            url=adzuna_job.redirect_url,
            salary_min=adzuna_job.salary_min,
            salary_max=adzuna_job.salary_max,
            contract_type=adzuna_job.contract_type,
            contract_time=adzuna_job.contract_time,
            category=adzuna_job.category.label,
            latitude=adzuna_job.latitude,
            longitude=adzuna_job.longitude,
            posted_at=adzuna_job.created,
        )
