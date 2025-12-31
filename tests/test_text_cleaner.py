"""Unit tests for the text cleaning module."""

from __future__ import annotations

import pytest

from src.processing.text_cleaner import (
    BOILERPLATE_PATTERNS,
    CLEANING_VERSION,
    CleanTextResult,
    build_job_document,
    clean_job_text,
    clean_resume_text,
    extract_skills_simple,
    is_text_too_short,
)


# =============================================================================
# Tests for CleanTextResult
# =============================================================================


class TestCleanTextResult:
    """Tests for the CleanTextResult dataclass."""

    def test_compression_ratio_normal(self):
        """Test compression ratio calculation."""
        result = CleanTextResult(
            text="cleaned",
            was_html=False,
            removed_chars=50,
            original_length=100,
        )
        assert result.compression_ratio == 0.5

    def test_compression_ratio_no_removal(self):
        """Test compression ratio when nothing removed."""
        result = CleanTextResult(
            text="same",
            was_html=False,
            removed_chars=0,
            original_length=100,
        )
        assert result.compression_ratio == 0.0

    def test_compression_ratio_empty_original(self):
        """Test compression ratio with zero original length."""
        result = CleanTextResult(
            text="",
            was_html=False,
            removed_chars=0,
            original_length=0,
        )
        assert result.compression_ratio == 0.0

    def test_immutable(self):
        """Test that CleanTextResult is frozen (immutable)."""
        result = CleanTextResult(
            text="test",
            was_html=False,
            removed_chars=0,
            original_length=4,
        )
        with pytest.raises(AttributeError):
            result.text = "modified"  # type: ignore


# =============================================================================
# Tests for clean_job_text
# =============================================================================


class TestCleanJobText:
    """Tests for the clean_job_text function."""

    def test_empty_text(self):
        """Test with empty text."""
        result = clean_job_text("")
        assert result.text == ""
        assert result.was_html is False
        assert result.removed_chars == 0
        assert result.original_length == 0

    def test_plain_text_preserved(self):
        """Test that plain text is preserved."""
        text = "This is a normal job description."
        result = clean_job_text(text)
        assert result.text == text
        assert result.was_html is False

    def test_html_tag_removal(self):
        """Test HTML tag removal."""
        text = "<p>Job description</p><br/><strong>Requirements</strong>"
        result = clean_job_text(text)
        assert "<p>" not in result.text
        assert "</p>" not in result.text
        assert "<br/>" not in result.text
        assert "<strong>" not in result.text
        assert "Job description" in result.text
        assert "Requirements" in result.text
        assert result.was_html is True

    def test_html_entity_decoding(self):
        """Test HTML entity decoding."""
        text = "R&amp;D department &amp; engineering &lt;team&gt;"
        result = clean_job_text(text)
        assert "R&D department & engineering <team>" in result.text

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        text = "Multiple   spaces    and\t\ttabs"
        result = clean_job_text(text)
        assert "  " not in result.text  # No multiple spaces
        assert "\t" not in result.text  # No tabs

    def test_newline_normalization(self):
        """Test that excessive newlines are collapsed."""
        text = "Line 1\n\n\n\n\nLine 2"
        result = clean_job_text(text)
        assert "\n\n\n" not in result.text

    def test_crlf_normalization(self):
        """Test CRLF to LF normalization."""
        text = "Line 1\r\nLine 2\rLine 3"
        result = clean_job_text(text)
        assert "\r" not in result.text
        assert "Line 1" in result.text
        assert "Line 2" in result.text
        assert "Line 3" in result.text

    def test_boilerplate_removal_eoe(self):
        """Test Equal Opportunity Employer boilerplate removal."""
        text = "Great job opportunity.\nWe are an Equal Opportunity Employer.\nApply today."
        result = clean_job_text(text)
        assert "equal opportunity employer" not in result.text.lower()
        assert "Great job opportunity" in result.text

    def test_boilerplate_removal_apply_now(self):
        """Test 'Apply now' boilerplate removal."""
        text = "Great job.\nApply now\nMore details."
        result = clean_job_text(text)
        assert "apply now" not in result.text.lower()

    def test_boilerplate_removal_click_to_apply(self):
        """Test 'Click to apply' boilerplate removal."""
        text = "Requirements listed.\nClick here to apply\nContact us."
        result = clean_job_text(text)
        assert "click here to apply" not in result.text.lower()

    def test_strips_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        text = "   Job description   "
        result = clean_job_text(text)
        assert result.text == "Job description"

    def test_removed_chars_tracked(self):
        """Test that removed characters are tracked."""
        text = "<p>Short</p>"
        result = clean_job_text(text)
        assert result.removed_chars > 0
        assert result.original_length == len(text)

    def test_complex_html_document(self):
        """Test with complex HTML document."""
        text = """
        <div class="job-posting">
            <h1>Senior Developer</h1>
            <p>We are looking for a developer.</p>
            <ul>
                <li>Python</li>
                <li>Django</li>
            </ul>
            <p>We are an equal opportunity employer.</p>
        </div>
        """
        result = clean_job_text(text)
        assert "<div>" not in result.text
        assert "Senior Developer" in result.text
        assert "Python" in result.text
        assert "equal opportunity employer" not in result.text.lower()
        assert result.was_html is True


# =============================================================================
# Tests for clean_resume_text
# =============================================================================


class TestCleanResumeText:
    """Tests for the clean_resume_text function."""

    def test_empty_text(self):
        """Test with empty text."""
        result = clean_resume_text("")
        assert result.text == ""
        assert result.was_html is False
        assert result.removed_chars == 0

    def test_plain_text_preserved(self):
        """Test that plain text is preserved."""
        text = "John Doe\nSoftware Engineer\nExperience: 5 years"
        result = clean_resume_text(text)
        assert "John Doe" in result.text
        assert "Software Engineer" in result.text

    def test_html_removed(self):
        """Test HTML is removed from resumes."""
        text = "<h1>John Doe</h1><p>Developer</p>"
        result = clean_resume_text(text)
        assert "<h1>" not in result.text
        assert "John Doe" in result.text
        assert result.was_html is True

    def test_no_boilerplate_removal(self):
        """Test that boilerplate patterns are NOT removed from resumes."""
        # Resume might legitimately mention "equal opportunity" or "apply"
        text = "Ensured equal opportunity in hiring. Click here for portfolio."
        result = clean_resume_text(text)
        # These should NOT be removed from resumes
        assert "equal opportunity" in result.text.lower()
        assert "click here" in result.text.lower()

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        text = "Skills:   Python    JavaScript"
        result = clean_resume_text(text)
        assert "  " not in result.text


# =============================================================================
# Tests for build_job_document
# =============================================================================


class TestBuildJobDocument:
    """Tests for the build_job_document function."""

    def test_basic_document(self):
        """Test basic document building."""
        doc = build_job_document(
            title="Software Engineer",
            company="TechCorp",
            location="New York, NY",
            description="We are looking for a developer.",
        )
        assert "Title: Software Engineer" in doc
        assert "Company: TechCorp" in doc
        assert "Location: New York, NY" in doc
        assert "Description:" in doc
        assert "We are looking for a developer." in doc

    def test_strips_field_whitespace(self):
        """Test that field values are stripped."""
        doc = build_job_document(
            title="  Engineer  ",
            company="  Corp  ",
            location="  NYC  ",
            description="  Description  ",
        )
        assert "Title: Engineer" in doc
        assert "Company: Corp" in doc
        assert "Location: NYC" in doc

    def test_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        long_description = "Word " * 2000  # Very long description
        doc = build_job_document(
            title="Engineer",
            company="Corp",
            location="NYC",
            description=long_description,
            max_description_chars=100,
        )
        # Should be truncated and end with ...
        assert len(doc) < len(long_description)
        assert "..." in doc

    def test_cleans_html_in_description(self):
        """Test that HTML in description is cleaned."""
        doc = build_job_document(
            title="Engineer",
            company="Corp",
            location="NYC",
            description="<p>Looking for developer</p>",
        )
        assert "<p>" not in doc
        assert "Looking for developer" in doc


# =============================================================================
# Tests for is_text_too_short
# =============================================================================


class TestIsTextTooShort:
    """Tests for the is_text_too_short function."""

    def test_empty_text(self):
        """Test empty text is too short."""
        assert is_text_too_short("") is True

    def test_none_like_behavior(self):
        """Test with whitespace-only text."""
        assert is_text_too_short("   ") is True

    def test_short_text(self):
        """Test text below threshold."""
        short = "Hello world"
        assert is_text_too_short(short, min_chars=200) is True

    def test_sufficient_text(self):
        """Test text above threshold."""
        long = "x" * 300
        assert is_text_too_short(long, min_chars=200) is False

    def test_counts_non_whitespace(self):
        """Test that only non-whitespace chars are counted."""
        # 100 chars + lots of whitespace
        text = "a " * 100
        assert is_text_too_short(text, min_chars=150) is True  # Only 100 meaningful chars

    def test_custom_threshold(self):
        """Test custom minimum threshold."""
        text = "Short text"
        assert is_text_too_short(text, min_chars=5) is False
        assert is_text_too_short(text, min_chars=100) is True


# =============================================================================
# Tests for extract_skills_simple
# =============================================================================


class TestExtractSkillsSimple:
    """Tests for the extract_skills_simple function."""

    def test_default_skills_extraction(self):
        """Test extraction with default skills list."""
        text = "Experience with Python, Django, and PostgreSQL"
        skills = extract_skills_simple(text)
        assert "python" in skills
        assert "django" in skills
        assert "postgresql" in skills

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        text = "PYTHON python Python PyThOn"
        skills = extract_skills_simple(text)
        assert "python" in skills
        assert len([s for s in skills if s == "python"]) == 1  # No duplicates

    def test_word_boundary_matching(self):
        """Test that partial words don't match."""
        text = "pythonic code and javanese script"
        skills = extract_skills_simple(text)
        # "python" shouldn't match "pythonic"
        # "java" shouldn't match "javanese"
        assert "python" not in skills
        assert "java" not in skills

    def test_custom_skills_list(self):
        """Test with custom skills list."""
        text = "I know CustomSkill and AnotherSkill"
        skills = extract_skills_simple(text, skills_list=["customskill", "anotherskill", "missing"])
        assert "customskill" in skills
        assert "anotherskill" in skills
        assert "missing" not in skills

    def test_returns_sorted_list(self):
        """Test that results are sorted."""
        text = "Python Django AWS Kubernetes"
        skills = extract_skills_simple(text)
        assert skills == sorted(skills)

    def test_no_duplicates(self):
        """Test no duplicates in results."""
        text = "Python Python Python Django Django"
        skills = extract_skills_simple(text)
        assert len(skills) == len(set(skills))

    def test_multi_word_skills(self):
        """Test multi-word skills like 'machine learning'."""
        text = "Experience with machine learning and deep learning"
        skills = extract_skills_simple(text)
        assert "machine learning" in skills
        assert "deep learning" in skills

    def test_empty_text(self):
        """Test with empty text."""
        skills = extract_skills_simple("")
        assert skills == []

    def test_no_matching_skills(self):
        """Test when no skills match."""
        text = "I like to cook and garden"
        skills = extract_skills_simple(text)
        assert skills == []

    def test_special_characters_in_skills(self):
        """Test skills with special characters like 'c++'."""
        text = "Proficient in C++ and C# programming"
        skills = extract_skills_simple(text)
        assert "c++" in skills
        assert "c#" in skills

    def test_skills_with_dots(self):
        """Test skills with dots like 'node.js'."""
        text = "Backend development with Node.js"
        skills = extract_skills_simple(text)
        assert "node.js" in skills

    def test_all_default_skills_lowercase(self):
        """Test that all skills in default list are found as lowercase."""
        text = """
        Python JavaScript TypeScript Java C++ C# Go Rust
        SQL NoSQL MongoDB PostgreSQL MySQL Redis
        AWS Azure GCP Docker Kubernetes Terraform
        React Angular Vue Node.js Django Flask FastAPI
        Machine Learning Deep Learning NLP Computer Vision
        TensorFlow PyTorch scikit-learn Pandas NumPy
        Git CI/CD Agile Scrum Jira
        REST GraphQL Microservices API
        """
        skills = extract_skills_simple(text)
        # All should be lowercase
        for skill in skills:
            assert skill == skill.lower()


# =============================================================================
# Tests for CLEANING_VERSION
# =============================================================================


class TestCleaningVersion:
    """Tests for the cleaning version constant."""

    def test_version_exists(self):
        """Test that CLEANING_VERSION is defined."""
        assert CLEANING_VERSION is not None

    def test_version_is_string(self):
        """Test that CLEANING_VERSION is a string."""
        assert isinstance(CLEANING_VERSION, str)

    def test_version_not_empty(self):
        """Test that CLEANING_VERSION is not empty."""
        assert len(CLEANING_VERSION) > 0


# =============================================================================
# Tests for BOILERPLATE_PATTERNS
# =============================================================================


class TestBoilerplatePatterns:
    """Tests for the boilerplate patterns."""

    def test_patterns_exist(self):
        """Test that patterns are defined."""
        assert len(BOILERPLATE_PATTERNS) > 0

    def test_eoe_pattern_matches(self):
        """Test EOE pattern matching."""
        eoe_pattern = BOILERPLATE_PATTERNS[0]
        assert eoe_pattern.search("We are an equal opportunity employer")
        assert eoe_pattern.search("EOE M/F/D/V")

    def test_patterns_are_case_insensitive(self):
        """Test that all patterns are case insensitive."""
        for pattern in BOILERPLATE_PATTERNS:
            # All patterns should have IGNORECASE flag
            import re
            assert pattern.flags & re.IGNORECASE
