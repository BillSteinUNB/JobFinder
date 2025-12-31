"""Hybrid scoring algorithm for job recommendations."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.data_collection.schema import Job
from src.processing.text_cleaner import extract_skills_simple
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ScoringWeights:
    """Weights for hybrid scoring components."""

    embedding_sim: float = 0.55
    skill_overlap: float = 0.25
    recency: float = 0.10
    location: float = 0.07
    salary: float = 0.03

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "embedding_sim": self.embedding_sim,
            "skill_overlap": self.skill_overlap,
            "recency": self.recency,
            "location": self.location,
            "salary": self.salary,
        }

    def renormalize(self, exclude: set[str]) -> dict[str, float]:
        """Renormalize weights excluding specified components."""
        weights = self.to_dict()
        available = {k: v for k, v in weights.items() if k not in exclude}
        total = sum(available.values())
        if total == 0:
            return {k: 1.0 / len(available) for k in available}
        return {k: v / total for k, v in available.items()}


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a job's score."""

    embedding_sim: float = 0.0
    skill_overlap: float = 0.0
    recency: float = 0.0
    location: float = 0.0
    salary: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "embedding_sim": self.embedding_sim,
            "skill_overlap": self.skill_overlap,
            "recency": self.recency,
            "location": self.location,
            "salary": self.salary,
        }


@dataclass
class ScoredJob:
    """A job with computed match score and explainability data."""

    job: Job
    total_score: float
    breakdown: dict[str, float]
    weights: dict[str, float]
    contributions: dict[str, float]
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str
    chroma_distance: float = 0.0

    def __post_init__(self):
        # Ensure skills are sorted
        self.matched_skills = sorted(self.matched_skills)
        self.missing_skills = sorted(self.missing_skills)[:10]  # Cap for display


@dataclass
class ResumeProfile:
    """Parsed and processed resume data."""

    raw_text: str
    clean_text: str
    skills: set[str]
    embedding: list[float] = field(default_factory=list)
    preferred_location: str | None = None
    min_salary: float | None = None


class HybridScorer:
    """
    Computes hybrid match scores for jobs against a resume profile.

    Combines embedding similarity with structured features like
    skill overlap, recency, location match, and salary fit.
    """

    DEFAULT_WEIGHTS = ScoringWeights()
    RECENCY_HALF_LIFE_DAYS = 30  # Days until recency score is halved

    def __init__(self, weights: ScoringWeights | None = None):
        """
        Initialize the scorer.

        Args:
            weights: Custom scoring weights (defaults to DEFAULT_WEIGHTS)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

    def distance_to_similarity(self, distance: float) -> float:
        """
        Convert Chroma distance to similarity score.

        Assumes cosine distance (1 - cosine_similarity).
        """
        return max(0.0, min(1.0, 1.0 - distance))

    def compute_skill_overlap(
        self,
        resume_skills: set[str],
        job_text: str,
    ) -> tuple[float, list[str], list[str]]:
        """
        Compute skill overlap between resume and job.

        Returns:
            Tuple of (overlap_score, matched_skills, missing_skills)
        """
        job_skills = set(extract_skills_simple(job_text))

        if not job_skills:
            # No skills extracted from job - return neutral score
            return 0.5, [], []

        matched = resume_skills & job_skills
        missing = job_skills - resume_skills

        # Recall-style: how many job skills does the resume cover
        overlap_score = len(matched) / len(job_skills)

        return overlap_score, list(matched), list(missing)

    def compute_recency(self, posted_at: datetime) -> float:
        """
        Compute recency score using exponential decay.

        Args:
            posted_at: Job posting date

        Returns:
            Recency score (0-1, where 1 is today)
        """
        now = datetime.now(timezone.utc)

        # Handle timezone-naive datetimes
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)

        delta = now - posted_at
        days_ago = max(0, delta.days)

        # Exponential decay
        decay_rate = math.log(2) / self.RECENCY_HALF_LIFE_DAYS
        recency = math.exp(-decay_rate * days_ago)

        return max(0.0, min(1.0, recency))

    def compute_location_match(
        self,
        job_location: str,
        preferred_location: str | None,
    ) -> float:
        """
        Compute location match score using string matching.

        Args:
            job_location: Job's location string
            preferred_location: User's preferred location (or None)

        Returns:
            Location match score (0-1)
        """
        if not preferred_location:
            return 0.5  # Neutral if no preference

        job_loc_lower = job_location.lower()
        pref_lower = preferred_location.lower()

        # Check for remote
        if "remote" in pref_lower and "remote" in job_loc_lower:
            return 1.0

        # Exact match
        if pref_lower in job_loc_lower or job_loc_lower in pref_lower:
            return 1.0

        # Partial match (any word overlap)
        pref_words = set(pref_lower.split())
        job_words = set(job_loc_lower.replace(",", " ").split())
        if pref_words & job_words:
            return 0.7

        return 0.3  # No match

    def compute_salary_match(
        self,
        job_salary_min: float | None,
        job_salary_max: float | None,
        user_min_salary: float | None,
    ) -> float:
        """
        Compute salary match score.

        Args:
            job_salary_min: Job's minimum salary
            job_salary_max: Job's maximum salary
            user_min_salary: User's minimum desired salary

        Returns:
            Salary match score (0-1)
        """
        if user_min_salary is None:
            return 0.5  # Neutral if no preference

        # Calculate job's mid salary
        if job_salary_min is not None and job_salary_max is not None:
            job_salary_mid = (job_salary_min + job_salary_max) / 2
        elif job_salary_max is not None:
            job_salary_mid = job_salary_max
        elif job_salary_min is not None:
            job_salary_mid = job_salary_min
        else:
            return 0.5  # Neutral if no job salary data

        ratio = job_salary_mid / user_min_salary

        if ratio >= 1.0:
            return 1.0
        elif ratio >= 0.8:
            # Linear scale from 0.6 to 1.0
            return 0.6 + (ratio - 0.8) * (0.4 / 0.2)
        else:
            # Below 80% - poor match
            return max(0.0, ratio * 0.75)

    def generate_explanation(
        self,
        breakdown: dict[str, float],
        contributions: dict[str, float],
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        """Generate a human-readable explanation of the match."""
        parts = []

        # Semantic match
        embed_score = breakdown.get("embedding_sim", 0)
        if embed_score >= 0.7:
            parts.append(f"Strong semantic match ({embed_score:.0%})")
        elif embed_score >= 0.5:
            parts.append(f"Good semantic match ({embed_score:.0%})")

        # Skills
        if matched_skills:
            parts.append(f"covers {len(matched_skills)} required skills")
        if len(missing_skills) > 3:
            parts.append(f"missing {len(missing_skills)} skills")

        # Recency
        recency_score = breakdown.get("recency", 0)
        if recency_score >= 0.8:
            parts.append("posted recently")

        if not parts:
            parts.append("Moderate match")

        return ", ".join(parts) + "."

    def score_job(
        self,
        job: Job,
        chroma_distance: float,
        resume_profile: ResumeProfile,
    ) -> ScoredJob:
        """
        Score a single job against a resume profile.

        Args:
            job: Job to score
            chroma_distance: Distance from Chroma query
            resume_profile: Parsed resume with skills and preferences

        Returns:
            ScoredJob with score breakdown and explanation
        """
        # Component scores
        breakdown = ScoreBreakdown()

        # 1. Embedding similarity
        breakdown.embedding_sim = self.distance_to_similarity(chroma_distance)

        # 2. Skill overlap
        skill_score, matched, missing = self.compute_skill_overlap(
            resume_profile.skills,
            job.description,
        )
        breakdown.skill_overlap = skill_score

        # 3. Recency
        breakdown.recency = self.compute_recency(job.posted_at)

        # 4. Location match
        breakdown.location = self.compute_location_match(
            job.location,
            resume_profile.preferred_location,
        )

        # 5. Salary match
        breakdown.salary = self.compute_salary_match(
            job.salary_min,
            job.salary_max,
            resume_profile.min_salary,
        )

        # Determine which components are missing/neutral
        exclude = set()
        if resume_profile.preferred_location is None:
            exclude.add("location")
        if resume_profile.min_salary is None and job.salary_min is None:
            exclude.add("salary")

        # Get renormalized weights
        weights = self.weights.renormalize(exclude)

        # Compute weighted score
        breakdown_dict = breakdown.to_dict()
        contributions = {
            k: breakdown_dict.get(k, 0) * weights.get(k, 0)
            for k in weights
        }
        total_score = sum(contributions.values())

        # Generate explanation
        explanation = self.generate_explanation(
            breakdown_dict,
            contributions,
            matched,
            missing,
        )

        return ScoredJob(
            job=job,
            total_score=total_score,
            breakdown=breakdown_dict,
            weights=weights,
            contributions=contributions,
            matched_skills=matched,
            missing_skills=missing,
            explanation=explanation,
            chroma_distance=chroma_distance,
        )

    def score_jobs(
        self,
        jobs: list[Job],
        distances: list[float],
        resume_profile: ResumeProfile,
    ) -> list[ScoredJob]:
        """
        Score multiple jobs against a resume profile.

        Args:
            jobs: List of jobs to score
            distances: Corresponding Chroma distances
            resume_profile: Parsed resume with skills and preferences

        Returns:
            List of ScoredJob, sorted by total_score descending
        """
        if len(jobs) != len(distances):
            raise ValueError("jobs and distances must have same length")

        scored = []
        for job, distance in zip(jobs, distances):
            scored.append(self.score_job(job, distance, resume_profile))

        # Sort by score descending
        scored.sort(key=lambda x: x.total_score, reverse=True)

        return scored
