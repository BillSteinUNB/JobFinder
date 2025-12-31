"""Unit tests for the evidence extraction module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.matching.evidence import (
    EvidenceExtractor,
    EvidenceMatch,
    EvidenceResult,
    extract_keywords,
    highlight_text,
    split_into_sentences,
)


# =============================================================================
# Tests for EvidenceMatch dataclass
# =============================================================================


class TestEvidenceMatch:
    """Tests for the EvidenceMatch dataclass."""

    def test_basic_creation(self):
        """Test basic EvidenceMatch creation."""
        match = EvidenceMatch(
            resume_sentence="I have experience with Python.",
            job_sentence="Python experience required.",
            similarity=0.85,
            match_type="semantic",
        )
        assert match.resume_sentence == "I have experience with Python."
        assert match.job_sentence == "Python experience required."
        assert match.similarity == 0.85
        assert match.match_type == "semantic"
        assert match.matched_terms == []

    def test_with_matched_terms(self):
        """Test EvidenceMatch with matched terms."""
        match = EvidenceMatch(
            resume_sentence="Python developer",
            job_sentence="Need Python skills",
            similarity=1.0,
            match_type="skill",
            matched_terms=["python"],
        )
        assert match.matched_terms == ["python"]

    def test_matched_terms_deduped_and_sorted(self):
        """Test that matched_terms are deduplicated and sorted in __post_init__."""
        match = EvidenceMatch(
            resume_sentence="Test",
            job_sentence="Test",
            similarity=1.0,
            match_type="skill",
            matched_terms=["python", "django", "python", "aws", "django"],
        )
        assert match.matched_terms == ["aws", "django", "python"]


# =============================================================================
# Tests for EvidenceResult dataclass
# =============================================================================


class TestEvidenceResult:
    """Tests for the EvidenceResult dataclass."""

    def test_match_count(self):
        """Test match_count property."""
        matches = [
            EvidenceMatch("a", "b", 0.9, "semantic"),
            EvidenceMatch("c", "d", 0.8, "skill"),
        ]
        result = EvidenceResult(
            job_id="job_1",
            matches=matches,
            top_resume_sentences=["a", "c"],
            top_job_sentences=["b", "d"],
            skill_matches=["python"],
            keyword_matches=["data"],
        )
        assert result.match_count == 2

    def test_avg_similarity(self):
        """Test avg_similarity property."""
        matches = [
            EvidenceMatch("a", "b", 0.9, "semantic"),
            EvidenceMatch("c", "d", 0.7, "skill"),
        ]
        result = EvidenceResult(
            job_id="job_1",
            matches=matches,
            top_resume_sentences=[],
            top_job_sentences=[],
            skill_matches=[],
            keyword_matches=[],
        )
        assert result.avg_similarity == 0.8

    def test_avg_similarity_empty(self):
        """Test avg_similarity with no matches returns 0."""
        result = EvidenceResult(
            job_id="job_1",
            matches=[],
            top_resume_sentences=[],
            top_job_sentences=[],
            skill_matches=[],
            keyword_matches=[],
        )
        assert result.avg_similarity == 0.0


# =============================================================================
# Tests for split_into_sentences
# =============================================================================


class TestSplitIntoSentences:
    """Tests for the split_into_sentences function."""

    def test_basic_split(self):
        """Test basic sentence splitting."""
        text = "This is sentence one. This is sentence two. And this is sentence three."
        sentences = split_into_sentences(text)
        assert len(sentences) == 3
        assert "This is sentence one." in sentences
        assert "This is sentence two." in sentences
        assert "And this is sentence three." in sentences

    def test_filters_short_sentences(self):
        """Test that very short sentences are filtered out."""
        text = "Hi. This is a much longer sentence that should be kept. Yes."
        sentences = split_into_sentences(text)
        # Only the longer sentence should remain
        assert len(sentences) == 1
        assert "This is a much longer sentence that should be kept." in sentences

    def test_filters_bullet_points(self):
        """Test that short bullet-point lines are filtered."""
        text = "- Short bullet. This is a longer sentence that should definitely be kept."
        sentences = split_into_sentences(text)
        assert len(sentences) == 1

    def test_empty_text(self):
        """Test with empty text."""
        assert split_into_sentences("") == []

    def test_whitespace_only(self):
        """Test with whitespace only."""
        assert split_into_sentences("   \n  \t  ") == []

    def test_single_sentence(self):
        """Test with a single sentence."""
        text = "This is a single sentence that is long enough to be included in the results."
        sentences = split_into_sentences(text)
        assert len(sentences) == 1


# =============================================================================
# Tests for extract_keywords
# =============================================================================


class TestExtractKeywords:
    """Tests for the extract_keywords function."""

    def test_basic_extraction(self):
        """Test basic keyword extraction."""
        text = "Python developer with Django experience and PostgreSQL knowledge"
        keywords = extract_keywords(text)
        assert "python" in keywords
        assert "developer" in keywords
        assert "django" in keywords
        assert "postgresql" in keywords

    def test_filters_stop_words(self):
        """Test that stop words are filtered."""
        text = "The developer has good experience with the team"
        keywords = extract_keywords(text)
        assert "the" not in keywords
        assert "has" not in keywords
        assert "with" not in keywords
        assert "good" not in keywords  # "good" is in our stop words
        assert "developer" in keywords

    def test_filters_short_words(self):
        """Test that short words are filtered by default."""
        text = "Go is a programming language for web development"
        keywords = extract_keywords(text, min_length=4)
        assert "go" not in keywords  # Too short
        assert "is" not in keywords  # Too short and stop word
        assert "programming" in keywords
        assert "language" in keywords

    def test_custom_min_length(self):
        """Test custom minimum length."""
        text = "Python and Go are languages"
        keywords = extract_keywords(text, min_length=2)
        assert "go" in keywords  # Now included with lower min_length

    def test_empty_text(self):
        """Test with empty text."""
        assert extract_keywords("") == set()

    def test_returns_set(self):
        """Test that result is a set (no duplicates)."""
        text = "Python Python Python developer developer"
        keywords = extract_keywords(text)
        assert isinstance(keywords, set)
        assert "python" in keywords
        assert "developer" in keywords


# =============================================================================
# Tests for highlight_text
# =============================================================================


class TestHighlightText:
    """Tests for the highlight_text function."""

    def test_basic_highlight(self):
        """Test basic term highlighting."""
        text = "Python is great"
        result = highlight_text(text, ["Python"])
        assert '<span class="highlight"' in result
        assert "Python" in result
        assert "background-color:" in result

    def test_no_terms(self):
        """Test with empty terms list."""
        text = "Python is great"
        result = highlight_text(text, [])
        # Should be HTML-escaped but no highlighting
        assert result == "Python is great"
        assert "<span" not in result

    def test_xss_prevention(self):
        """Test XSS prevention - script tags should be escaped."""
        text = "<script>alert('xss')</script>"
        result = highlight_text(text, [])
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_xss_prevention_in_terms(self):
        """Test XSS prevention in terms."""
        text = "Normal text"
        result = highlight_text(text, ["<script>"])
        # The term should not inject HTML
        assert "<script>" not in result

    def test_case_insensitive(self):
        """Test case-insensitive highlighting."""
        text = "Python and PYTHON and python"
        result = highlight_text(text, ["python"])
        # All variations should be highlighted
        assert result.count('<span class="highlight"') == 3

    def test_multiple_terms(self):
        """Test highlighting multiple terms."""
        text = "Python and Django are great"
        result = highlight_text(text, ["Python", "Django"])
        assert result.count('<span class="highlight"') == 2

    def test_custom_class(self):
        """Test custom highlight class."""
        text = "Python is great"
        result = highlight_text(text, ["Python"], highlight_class="my-highlight")
        assert 'class="my-highlight"' in result

    def test_html_in_text_escaped(self):
        """Test that HTML entities in text are properly escaped."""
        text = "Use &amp; for 'and' in HTML"
        result = highlight_text(text, ["HTML"])
        assert "&amp;amp;" in result  # & is escaped
        assert '<span class="highlight"' in result


# =============================================================================
# Tests for EvidenceExtractor
# =============================================================================


class TestEvidenceExtractor:
    """Tests for the EvidenceExtractor class."""

    def test_init_defaults(self):
        """Test default initialization."""
        extractor = EvidenceExtractor()
        assert extractor._embedding_manager is None
        assert extractor._top_k == 5
        assert extractor._threshold == 0.5

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        mock_manager = MagicMock()
        extractor = EvidenceExtractor(
            embedding_manager=mock_manager,
            top_k_sentences=10,
            similarity_threshold=0.7,
        )
        assert extractor._embedding_manager is mock_manager
        assert extractor._top_k == 10
        assert extractor._threshold == 0.7


class TestExtractSkillEvidence:
    """Tests for skill evidence extraction."""

    def test_matching_skills(self):
        """Test extraction of matching skills."""
        extractor = EvidenceExtractor()
        resume = "I have experience with Python, Django, and PostgreSQL"
        job = "We need Python and Django experience. PostgreSQL is a plus."

        matched, job_only = extractor.extract_skill_evidence(resume, job)

        assert "python" in matched
        assert "django" in matched
        assert "postgresql" in matched

    def test_job_only_skills(self):
        """Test detection of skills only in job description."""
        extractor = EvidenceExtractor()
        resume = "I have experience with Python"
        job = "We need Python, Kubernetes, and AWS experience"

        matched, job_only = extractor.extract_skill_evidence(resume, job)

        assert "python" in matched
        assert "kubernetes" in job_only
        assert "aws" in job_only

    def test_no_overlap(self):
        """Test when no skills overlap."""
        extractor = EvidenceExtractor()
        resume = "I have experience with JavaScript and React"
        job = "We need Python and Django experience"

        matched, job_only = extractor.extract_skill_evidence(resume, job)

        assert len(matched) == 0
        assert "python" in job_only
        assert "django" in job_only

    def test_results_sorted(self):
        """Test that results are sorted alphabetically."""
        extractor = EvidenceExtractor()
        resume = "Python Django PostgreSQL AWS"
        job = "PostgreSQL Python Django AWS"

        matched, _ = extractor.extract_skill_evidence(resume, job)

        assert matched == sorted(matched)


class TestExtractKeywordEvidence:
    """Tests for keyword evidence extraction."""

    def test_overlapping_keywords(self):
        """Test extraction of overlapping keywords."""
        extractor = EvidenceExtractor()
        resume = "Developed scalable microservices architecture using Python"
        job = "Build scalable microservices with Python"

        keywords = extractor.extract_keyword_evidence(resume, job)

        assert "microservices" in keywords
        assert "python" in keywords
        assert "scalable" in keywords

    def test_max_20_keywords(self):
        """Test that maximum 20 keywords are returned."""
        extractor = EvidenceExtractor()
        # Create text with many overlapping keywords
        words = [f"keyword{i}" for i in range(30)]
        resume = " ".join(words)
        job = " ".join(words)

        keywords = extractor.extract_keyword_evidence(resume, job)

        assert len(keywords) <= 20

    def test_sorted_by_length(self):
        """Test that keywords are sorted by length (longest first)."""
        extractor = EvidenceExtractor()
        resume = "microservices architecture development"
        job = "microservices architecture development"

        keywords = extractor.extract_keyword_evidence(resume, job)

        # Verify sorted by length descending
        for i in range(len(keywords) - 1):
            assert len(keywords[i]) >= len(keywords[i + 1])


class TestExtractSemanticEvidence:
    """Tests for semantic evidence extraction."""

    def test_no_embedding_manager(self):
        """Test returns empty when no embedding manager."""
        extractor = EvidenceExtractor(embedding_manager=None)

        matches = extractor.extract_semantic_evidence(
            "Resume text here",
            "Job description here",
        )

        assert matches == []

    def test_empty_resume(self):
        """Test with empty resume text."""
        mock_manager = MagicMock()
        extractor = EvidenceExtractor(embedding_manager=mock_manager)

        matches = extractor.extract_semantic_evidence("", "Job description")

        assert matches == []

    def test_empty_job(self):
        """Test with empty job text."""
        mock_manager = MagicMock()
        extractor = EvidenceExtractor(embedding_manager=mock_manager)

        # Resume needs actual sentences (>20 chars)
        resume = "This is a resume sentence that is long enough to be included."
        matches = extractor.extract_semantic_evidence(resume, "")

        assert matches == []

    def test_semantic_matching_with_mock(self):
        """Test semantic matching with mocked embeddings."""
        mock_manager = MagicMock()
        # Create mock embeddings that will have high similarity
        mock_manager.embed_texts.side_effect = [
            np.array([[0.9, 0.1, 0.0]]),  # Resume embedding
            np.array([[0.85, 0.15, 0.0]]),  # Job embedding
        ]

        extractor = EvidenceExtractor(
            embedding_manager=mock_manager,
            similarity_threshold=0.5,
        )

        resume = "This is a resume sentence that is definitely long enough to be included in results."
        job = "This is a job description sentence that is definitely long enough to be included."

        matches = extractor.extract_semantic_evidence(resume, job)

        # Should have found matches with high similarity
        assert mock_manager.embed_texts.called

    def test_embedding_failure_handled(self):
        """Test that embedding failures are handled gracefully."""
        mock_manager = MagicMock()
        mock_manager.embed_texts.side_effect = Exception("Embedding failed")

        extractor = EvidenceExtractor(embedding_manager=mock_manager)

        resume = "This is a long enough resume sentence to be processed."
        job = "This is a long enough job description to be processed."

        # Should not raise, just return empty
        matches = extractor.extract_semantic_evidence(resume, job)
        assert matches == []


class TestExtractEvidence:
    """Tests for the main extract_evidence method."""

    def test_complete_extraction(self, sample_resume_text: str, sample_job_description: str):
        """Test complete evidence extraction."""
        extractor = EvidenceExtractor()

        result = extractor.extract_evidence(
            job_id="job_123",
            resume_text=sample_resume_text,
            job_text=sample_job_description,
        )

        assert isinstance(result, EvidenceResult)
        assert result.job_id == "job_123"
        assert len(result.skill_matches) > 0
        assert len(result.keyword_matches) > 0

    def test_skill_matches_found(self, sample_resume_text: str, sample_job_description: str):
        """Test that skill matches are found correctly."""
        extractor = EvidenceExtractor()

        result = extractor.extract_evidence(
            job_id="job_123",
            resume_text=sample_resume_text,
            job_text=sample_job_description,
        )

        # Both resume and job mention Python, Django/FastAPI, PostgreSQL
        assert "python" in result.skill_matches
        assert "fastapi" in result.skill_matches or "django" in result.skill_matches

    def test_empty_inputs(self):
        """Test with empty inputs."""
        extractor = EvidenceExtractor()

        result = extractor.extract_evidence(
            job_id="job_123",
            resume_text="",
            job_text="",
        )

        assert result.job_id == "job_123"
        assert result.skill_matches == []
        assert result.keyword_matches == []
        assert result.matches == []


class TestExtractEvidenceBatch:
    """Tests for batch evidence extraction."""

    def test_batch_extraction(self, sample_resume_text: str):
        """Test batch extraction for multiple jobs."""
        extractor = EvidenceExtractor()

        job_ids = ["job_1", "job_2"]
        job_texts = [
            "Python developer needed with Django experience",
            "Data scientist with machine learning skills required",
        ]

        results = extractor.extract_evidence_batch(job_ids, sample_resume_text, job_texts)

        assert len(results) == 2
        assert "job_1" in results
        assert "job_2" in results
        assert isinstance(results["job_1"], EvidenceResult)
        assert isinstance(results["job_2"], EvidenceResult)

    def test_batch_empty_list(self, sample_resume_text: str):
        """Test batch extraction with empty list."""
        extractor = EvidenceExtractor()

        results = extractor.extract_evidence_batch([], sample_resume_text, [])

        assert results == {}
