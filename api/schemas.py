"""Pydantic schemas for API request/response models.

These schemas map to the frontend TypeScript types in jobhunt/types.ts
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Enums (matching TypeScript types)
# ============================================================================


class JobType(str, Enum):
    """Job employment type."""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class ExperienceLevel(str, Enum):
    """Experience level required."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    LEAD = "lead"


class ApplicationStatus(str, Enum):
    """Application tracking status."""
    SAVED = "saved"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


# ============================================================================
# Company
# ============================================================================


class CompanyResponse(BaseModel):
    """Company information in job response."""
    name: str
    logo: str = ""
    location: str
    size: str = ""
    website: str = ""


# ============================================================================
# Skills
# ============================================================================


class MatchedSkill(BaseModel):
    """Skill with match status."""
    name: str
    match: bool
    years: int | None = None


# ============================================================================
# Job Schemas
# ============================================================================


class JobResponse(BaseModel):
    """Job response matching frontend Job interface."""
    id: str
    title: str
    company: CompanyResponse
    location: str
    type: JobType = JobType.FULL_TIME
    salaryMin: float = 0
    salaryMax: float = 0
    postedAt: str  # ISO date string
    matchScore: float = 0
    skills: list[str] = Field(default_factory=list)
    matchedSkills: list[MatchedSkill] = Field(default_factory=list)
    description: str
    requirements: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    isRemote: bool = False
    status: Literal["new", "viewed"] | None = None
    
    # Extra fields for detail view
    url: str | None = None
    category: str | None = None
    explanation: str | None = None  # Match explanation
    breakdown: dict[str, float] | None = None  # Score breakdown


class JobSearchParams(BaseModel):
    """Query parameters for job search."""
    query: str | None = None
    location: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None
    job_types: list[JobType] | None = None
    remote_only: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class JobSearchResponse(BaseModel):
    """Paginated job search results."""
    jobs: list[JobResponse]
    total: int
    limit: int
    offset: int
    hasMore: bool


class JobLabelRequest(BaseModel):
    """Request to label a job (save/reject)."""
    label: Literal[0, 1]  # 0 = rejected, 1 = saved/interested


# ============================================================================
# Resume Schemas
# ============================================================================


class ExperienceEntry(BaseModel):
    """Work experience entry."""
    role: str
    company: str
    duration: str


class EducationEntry(BaseModel):
    """Education entry."""
    degree: str
    school: str
    year: str


class ResumeProfileResponse(BaseModel):
    """Resume profile data for frontend."""
    fileName: str | None = None
    uploadedAt: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    preferredLocation: str | None = None
    minSalary: float | None = None


class ResumeUploadResponse(BaseModel):
    """Response after resume upload."""
    success: bool
    message: str
    profile: ResumeProfileResponse | None = None


class ResumeUploadSettings(BaseModel):
    """Optional settings for resume upload."""
    preferredLocation: str | None = None
    minSalary: float | None = None


# ============================================================================
# Application Schemas
# ============================================================================


class ApplicationResponse(BaseModel):
    """Application tracking entry."""
    id: str
    jobId: str
    job: JobResponse
    status: ApplicationStatus
    appliedAt: str  # ISO date
    updatedAt: str  # ISO date
    notes: str = ""
    nextStep: str | None = None
    nextStepDate: str | None = None


class ApplicationUpdateRequest(BaseModel):
    """Request to update application status."""
    status: ApplicationStatus | None = None
    notes: str | None = None
    nextStep: str | None = None
    nextStepDate: str | None = None


class ApplicationsResponse(BaseModel):
    """List of applications."""
    applications: list[ApplicationResponse]
    total: int


# ============================================================================
# Analytics Schemas
# ============================================================================


class TimeSeriesPoint(BaseModel):
    """Single point in time series data."""
    date: str
    count: int


class FunnelStage(BaseModel):
    """Funnel visualization stage."""
    stage: str
    count: int
    fill: str


class SkillMatchScore(BaseModel):
    """Skill match percentage."""
    name: str
    score: float  # 0-100


class AnalyticsResponse(BaseModel):
    """Analytics data for dashboard."""
    applicationsOverTime: list[TimeSeriesPoint] = Field(default_factory=list)
    funnel: list[FunnelStage] = Field(default_factory=list)
    skillsMatch: list[SkillMatchScore] = Field(default_factory=list)
    totalJobs: int = 0
    totalApplications: int = 0
    avgMatchScore: float = 0
