"""Unit tests for HybridScorer."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from src.data_collection.schema import Job
from src.matching.scorer import (
    HybridScorer,
    ResumeProfile,
    ScoreBreakdown,
    ScoredJob,
    ScoringWeights,
)


# =============================================================================
# ScoringWeights Tests
# =============================================================================


class TestScoringWeights:
    """Tests for ScoringWeights dataclass."""

    def test_default_weights_sum_to_one(self):
        """Default weights should sum to 1.0."""
        weights = ScoringWeights()
        total = (
            weights.embedding_sim
            + weights.skill_overlap
            + weights.recency
            + weights.location
            + weights.salary
        )
        assert abs(total - 1.0) < 0.001

    def test_to_dict(self):
        """to_dict should return all weight components."""
        weights = ScoringWeights()
        d = weights.to_dict()
        assert "embedding_sim" in d
        assert "skill_overlap" in d
        assert "recency" in d
        assert "location" in d
        assert "salary" in d
        assert len(d) == 5

    def test_renormalize_excludes_components(self):
        """renormalize should redistribute weights when components are excluded."""
        weights = ScoringWeights()
        renorm = weights.renormalize({"location", "salary"})

        # Should not contain excluded keys
        assert "location" not in renorm
        assert "salary" not in renorm

        # Remaining weights should sum to 1.0
        assert abs(sum(renorm.values()) - 1.0) < 0.001

    def test_renormalize_all_excluded(self):
        """renormalize with all components excluded should return equal weights."""
        weights = ScoringWeights()
        renorm = weights.renormalize(
            {"embedding_sim", "skill_overlap", "recency", "location", "salary"}
        )
        # Empty dict since all excluded
        assert len(renorm) == 0


# =============================================================================
# HybridScorer Individual Method Tests
# =============================================================================


class TestDistanceToSimilarity:
    """Tests for distance_to_similarity conversion."""

    def test_zero_distance_is_perfect_similarity(self):
        """Distance 0 should give similarity 1.0."""
        scorer = HybridScorer()
        assert scorer.distance_to_similarity(0.0) == 1.0

    def test_one_distance_is_zero_similarity(self):
        """Distance 1.0 should give similarity 0.0."""
        scorer = HybridScorer()
        assert scorer.distance_to_similarity(1.0) == 0.0

    def test_mid_distance(self):
        """Distance 0.5 should give similarity 0.5."""
        scorer = HybridScorer()
        assert scorer.distance_to_similarity(0.5) == 0.5

    def test_clamps_negative_distance(self):
        """Negative distance should clamp to 1.0 similarity."""
        scorer = HybridScorer()
        assert scorer.distance_to_similarity(-0.5) == 1.0

    def test_clamps_large_distance(self):
        """Distance > 1.0 should clamp to 0.0 similarity."""
        scorer = HybridScorer()
        assert scorer.distance_to_similarity(1.5) == 0.0


class TestSkillOverlap:
    """Tests for skill overlap computation."""

    def test_full_overlap(self):
        """All job skills present in resume should give 1.0."""
        scorer = HybridScorer()
        resume_skills = {"python", "django", "sql", "docker"}
        job_text = "We need python and django experience. SQL knowledge required."

        score, matched, missing = scorer.compute_skill_overlap(resume_skills, job_text)

        assert score == 1.0
        assert set(matched) == {"python", "django", "sql"}
        assert missing == []

    def test_partial_overlap(self):
        """Partial skill match should give proportional score."""
        scorer = HybridScorer()
        resume_skills = {"python", "javascript"}
        job_text = "Need Python, Django, and PostgreSQL experience."

        score, matched, missing = scorer.compute_skill_overlap(resume_skills, job_text)

        assert 0.0 < score < 1.0
        assert "python" in matched
        assert "django" in missing
        assert "postgresql" in missing

    def test_no_overlap(self):
        """No matching skills should give 0.0."""
        scorer = HybridScorer()
        resume_skills = {"rust", "go"}
        job_text = "Need Python and Django experience."

        score, matched, missing = scorer.compute_skill_overlap(resume_skills, job_text)

        assert score == 0.0
        assert matched == []

    def test_no_job_skills(self):
        """Job with no extractable skills should return 0.5 (neutral)."""
        scorer = HybridScorer()
        resume_skills = {"python", "django"}
        job_text = "Looking for a great team player with enthusiasm."

        score, matched, missing = scorer.compute_skill_overlap(resume_skills, job_text)

        assert score == 0.5
        assert matched == []
        assert missing == []


class TestRecencyScore:
    """Tests for recency computation."""

    def test_today_is_full_score(self):
        """Job posted today should have score ~1.0."""
        scorer = HybridScorer()
        now = datetime.now(timezone.utc)
        score = scorer.compute_recency(now)
        assert score > 0.99

    def test_half_life_is_half_score(self):
        """Job posted at half-life days ago should have score ~0.5."""
        scorer = HybridScorer()
        half_life_ago = datetime.now(timezone.utc) - timedelta(
            days=scorer.RECENCY_HALF_LIFE_DAYS
        )
        score = scorer.compute_recency(half_life_ago)
        assert 0.45 < score < 0.55

    def test_old_job_low_score(self):
        """Job posted long ago should have low score."""
        scorer = HybridScorer()
        old_date = datetime.now(timezone.utc) - timedelta(days=180)
        score = scorer.compute_recency(old_date)
        assert score < 0.1

    def test_handles_naive_datetime(self):
        """Should handle timezone-naive datetime by assuming UTC."""
        scorer = HybridScorer()
        naive_now = datetime.utcnow()
        score = scorer.compute_recency(naive_now)
        assert score > 0.99


class TestLocationMatch:
    """Tests for location matching."""

    def test_no_preference_is_neutral(self):
        """No location preference should return 0.5."""
        scorer = HybridScorer()
        score = scorer.compute_location_match("San Francisco, CA", None)
        assert score == 0.5

    def test_exact_match(self):
        """Exact location match should return 1.0."""
        scorer = HybridScorer()
        score = scorer.compute_location_match("San Francisco, CA", "San Francisco")
        assert score == 1.0

    def test_remote_match(self):
        """Remote preference matching remote job should return 1.0."""
        scorer = HybridScorer()
        score = scorer.compute_location_match("Remote (US)", "Remote")
        assert score == 1.0

    def test_partial_match(self):
        """City in same state should give partial score."""
        scorer = HybridScorer()
        score = scorer.compute_location_match("San Jose, CA", "CA")
        assert score == 0.7

    def test_no_match(self):
        """Completely different location should give low score."""
        scorer = HybridScorer()
        score = scorer.compute_location_match("London, UK", "New York")
        assert score == 0.3


class TestSalaryMatch:
    """Tests for salary matching."""

    def test_no_preference_is_neutral(self):
        """No salary preference should return 0.5."""
        scorer = HybridScorer()
        score = scorer.compute_salary_match(100000, 150000, None)
        assert score == 0.5

    def test_no_job_salary_is_neutral(self):
        """No job salary data should return 0.5."""
        scorer = HybridScorer()
        score = scorer.compute_salary_match(None, None, 100000)
        assert score == 0.5

    def test_salary_meets_expectation(self):
        """Job salary >= user minimum should return 1.0."""
        scorer = HybridScorer()
        score = scorer.compute_salary_match(120000, 150000, 100000)
        assert score == 1.0

    def test_salary_slightly_below(self):
        """Job salary 80-100% of minimum should give partial score."""
        scorer = HybridScorer()
        # Job mid = 90k, user min = 100k, ratio = 0.9
        score = scorer.compute_salary_match(80000, 100000, 100000)
        assert 0.6 < score < 1.0

    def test_salary_well_below(self):
        """Job salary well below minimum should give low score."""
        scorer = HybridScorer()
        score = scorer.compute_salary_match(50000, 60000, 100000)
        assert score < 0.5


# =============================================================================
# Full Scoring Integration Tests
# =============================================================================


class TestScoreJob:
    """Tests for the full score_job method."""

    @pytest.fixture
    def scorer(self):
        """Create a HybridScorer instance."""
        return HybridScorer()

    @pytest.fixture
    def resume_profile(self):
        """Create a sample resume profile."""
        return ResumeProfile(
            raw_text="Sample resume",
            clean_text="Senior Python Developer with Django and AWS experience",
            skills={"python", "django", "aws", "docker", "sql"},
            embedding=[0.1] * 384,
            preferred_location="San Francisco",
            min_salary=120000,
        )

    def test_score_job_returns_scored_job(self, scorer, sample_job, resume_profile):
        """score_job should return a ScoredJob instance."""
        result = scorer.score_job(sample_job, 0.3, resume_profile)

        assert isinstance(result, ScoredJob)
        assert result.job == sample_job
        assert 0.0 <= result.total_score <= 1.0
        assert isinstance(result.breakdown, dict)
        assert isinstance(result.weights, dict)
        assert isinstance(result.matched_skills, list)
        assert isinstance(result.missing_skills, list)
        assert isinstance(result.explanation, str)

    def test_perfect_match_high_score(self, scorer, resume_profile):
        """A job that matches resume perfectly should have high score."""
        perfect_job = Job(
            id="perfect_1",
            source="test",
            source_id="1",
            title="Senior Python Developer",
            company="TechCorp",
            location="San Francisco, CA",
            description="Need Python, Django, AWS, Docker experience. SQL required.",
            url="https://example.com/job/1",
            salary_min=140000,
            salary_max=180000,
            posted_at=datetime.now(timezone.utc),
        )

        result = scorer.score_job(perfect_job, 0.1, resume_profile)

        # Should have high score (> 0.7)
        assert result.total_score > 0.7
        assert len(result.matched_skills) >= 4

    def test_poor_match_low_score(self, scorer, resume_profile):
        """A job that doesn't match resume should have low score."""
        poor_job = Job(
            id="poor_1",
            source="test",
            source_id="1",
            title="Java Developer",
            company="OtherCorp",
            location="London, UK",
            description="Need Java, Spring Boot, Oracle experience.",
            url="https://example.com/job/1",
            salary_min=50000,
            salary_max=60000,
            posted_at=datetime.now(timezone.utc) - timedelta(days=90),
        )

        result = scorer.score_job(poor_job, 0.8, resume_profile)

        # Should have lower score
        assert result.total_score < 0.5
        assert len(result.matched_skills) == 0

    def test_score_job_excludes_missing_preferences(self, scorer, sample_job):
        """score_job should renormalize weights when preferences are missing."""
        # Resume with no location/salary preferences
        minimal_profile = ResumeProfile(
            raw_text="Sample",
            clean_text="Python developer",
            skills={"python"},
            embedding=[0.1] * 384,
            preferred_location=None,
            min_salary=None,
        )

        result = scorer.score_job(sample_job, 0.3, minimal_profile)

        # Location and salary should be excluded from weights
        assert "location" not in result.weights or result.weights.get("location", 0) == 0
        # Remaining weights should still sum to ~1.0
        assert abs(sum(result.weights.values()) - 1.0) < 0.01


class TestScoreJobs:
    """Tests for scoring multiple jobs."""

    def test_score_jobs_returns_sorted_list(self, sample_jobs):
        """score_jobs should return jobs sorted by score descending."""
        scorer = HybridScorer()
        profile = ResumeProfile(
            raw_text="Sample",
            clean_text="Python developer with SQL experience",
            skills={"python", "sql"},
            embedding=[0.1] * 384,
        )

        distances = [0.3, 0.2, 0.5]  # Different distances for each job
        results = scorer.score_jobs(sample_jobs, distances, profile)

        assert len(results) == len(sample_jobs)
        # Verify sorted descending
        for i in range(len(results) - 1):
            assert results[i].total_score >= results[i + 1].total_score

    def test_score_jobs_length_mismatch_raises(self, sample_jobs):
        """score_jobs should raise if jobs and distances have different lengths."""
        scorer = HybridScorer()
        profile = ResumeProfile(
            raw_text="Sample",
            clean_text="Python developer",
            skills={"python"},
            embedding=[0.1] * 384,
        )

        with pytest.raises(ValueError, match="same length"):
            scorer.score_jobs(sample_jobs, [0.3, 0.2], profile)  # Wrong length

    def test_score_jobs_empty_list(self):
        """score_jobs with empty list should return empty list."""
        scorer = HybridScorer()
        profile = ResumeProfile(
            raw_text="Sample",
            clean_text="Python developer",
            skills={"python"},
            embedding=[0.1] * 384,
        )

        results = scorer.score_jobs([], [], profile)
        assert results == []


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_resume_skills(self, sample_job):
        """Scoring should work with empty resume skills."""
        scorer = HybridScorer()
        profile = ResumeProfile(
            raw_text="",
            clean_text="",
            skills=set(),
            embedding=[0.1] * 384,
        )

        result = scorer.score_job(sample_job, 0.3, profile)
        assert 0.0 <= result.total_score <= 1.0
        assert result.matched_skills == []

    def test_empty_job_description(self):
        """Scoring should work with empty job description."""
        scorer = HybridScorer()
        empty_job = Job(
            id="empty_1",
            source="test",
            source_id="1",
            title="Developer",
            company="Corp",
            location="NYC",
            description="",
            url="https://example.com",
            posted_at=datetime.now(timezone.utc),
        )
        profile = ResumeProfile(
            raw_text="Python dev",
            clean_text="Python dev",
            skills={"python"},
            embedding=[0.1] * 384,
        )

        result = scorer.score_job(empty_job, 0.5, profile)
        assert 0.0 <= result.total_score <= 1.0

    def test_future_posted_date(self):
        """Job with future date should still work (recency capped at 1.0)."""
        scorer = HybridScorer()
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        score = scorer.compute_recency(future_date)
        assert score == 1.0

    def test_custom_weights(self, sample_job):
        """Custom weights should be applied correctly."""
        custom_weights = ScoringWeights(
            embedding_sim=0.8,
            skill_overlap=0.2,
            recency=0.0,
            location=0.0,
            salary=0.0,
        )
        scorer = HybridScorer(weights=custom_weights)
        profile = ResumeProfile(
            raw_text="Python dev",
            clean_text="Python dev",
            skills={"python"},
            embedding=[0.1] * 384,
        )

        result = scorer.score_job(sample_job, 0.3, profile)

        # With no location/salary preferences, weights get renormalized
        # but embedding should still dominate
        assert result.breakdown["embedding_sim"] == 0.7  # 1.0 - 0.3
