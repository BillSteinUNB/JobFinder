"""Text cleaning utilities for job descriptions and documents."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

# Version identifier for cleaning logic - increment when logic changes significantly
CLEANING_VERSION = "1"

# Boilerplate patterns to remove (case-insensitive, applied line-wise)
BOILERPLATE_PATTERNS = [
    re.compile(r"\b(equal opportunity employer|eoe|eeo)\b", re.IGNORECASE),
    re.compile(r"\bby applying.*you agree\b", re.IGNORECASE),
    re.compile(r"\baccommodation(s)? available\b", re.IGNORECASE),
    re.compile(r"\bwe are an equal opportunity\b", re.IGNORECASE),
    re.compile(r"\bclick (here )?to apply\b", re.IGNORECASE),
    re.compile(r"\bapply now\b", re.IGNORECASE),
]

# HTML tag pattern
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Whitespace normalization patterns
MULTI_SPACE_PATTERN = re.compile(r"[ \t]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class CleanTextResult:
    """Result of text cleaning operation."""

    text: str
    was_html: bool
    removed_chars: int
    original_length: int

    @property
    def compression_ratio(self) -> float:
        """Ratio of text removed during cleaning."""
        if self.original_length == 0:
            return 0.0
        return self.removed_chars / self.original_length


def clean_job_text(text: str) -> CleanTextResult:
    """
    Clean and normalize job description text.

    Performs:
    - HTML tag removal
    - HTML entity decoding
    - Whitespace normalization
    - Boilerplate removal

    Args:
        text: Raw job description text

    Returns:
        CleanTextResult with cleaned text and metadata
    """
    if not text:
        return CleanTextResult(text="", was_html=False, removed_chars=0, original_length=0)

    original_length = len(text)
    was_html = bool(HTML_TAG_PATTERN.search(text))

    # Step 1: Remove HTML tags
    cleaned = HTML_TAG_PATTERN.sub(" ", text)

    # Step 2: Decode HTML entities (&amp; -> &, etc.)
    cleaned = html.unescape(cleaned)

    # Step 3: Normalize line endings
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Step 4: Normalize whitespace (collapse multiple spaces/tabs)
    cleaned = MULTI_SPACE_PATTERN.sub(" ", cleaned)

    # Step 5: Collapse excessive newlines (3+ -> 2)
    cleaned = MULTI_NEWLINE_PATTERN.sub("\n\n", cleaned)

    # Step 6: Remove boilerplate lines
    lines = cleaned.split("\n")
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered_lines.append("")
            continue

        # Check if line matches boilerplate patterns
        is_boilerplate = any(pattern.search(stripped) for pattern in BOILERPLATE_PATTERNS)
        if not is_boilerplate:
            filtered_lines.append(line)

    cleaned = "\n".join(filtered_lines)

    # Step 7: Final cleanup - strip leading/trailing whitespace
    cleaned = cleaned.strip()

    removed_chars = original_length - len(cleaned)

    return CleanTextResult(
        text=cleaned,
        was_html=was_html,
        removed_chars=removed_chars,
        original_length=original_length,
    )


def clean_resume_text(text: str) -> CleanTextResult:
    """
    Clean and normalize resume text.

    Similar to clean_job_text but WITHOUT boilerplate removal,
    since resumes don't contain job-posting boilerplate patterns
    and we don't want to accidentally remove valid resume content.

    Performs:
    - HTML tag removal
    - HTML entity decoding
    - Whitespace normalization

    Args:
        text: Raw resume text

    Returns:
        CleanTextResult with cleaned text and metadata
    """
    if not text:
        return CleanTextResult(text="", was_html=False, removed_chars=0, original_length=0)

    original_length = len(text)
    was_html = bool(HTML_TAG_PATTERN.search(text))

    # Step 1: Remove HTML tags
    cleaned = HTML_TAG_PATTERN.sub(" ", text)

    # Step 2: Decode HTML entities (&amp; -> &, etc.)
    cleaned = html.unescape(cleaned)

    # Step 3: Normalize line endings
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Step 4: Normalize whitespace (collapse multiple spaces/tabs)
    cleaned = MULTI_SPACE_PATTERN.sub(" ", cleaned)

    # Step 5: Collapse excessive newlines (3+ -> 2)
    cleaned = MULTI_NEWLINE_PATTERN.sub("\n\n", cleaned)

    # Step 6: Final cleanup - strip leading/trailing whitespace
    # NOTE: No boilerplate removal for resumes
    cleaned = cleaned.strip()

    removed_chars = original_length - len(cleaned)

    return CleanTextResult(
        text=cleaned,
        was_html=was_html,
        removed_chars=removed_chars,
        original_length=original_length,
    )


def build_job_document(
    title: str,
    company: str,
    location: str,
    description: str,
    *,
    max_description_chars: int = 6000,
) -> str:
    """
    Build a structured document from job fields for embedding.

    Creates a consistent format that improves embedding quality
    by providing clear structure.

    Args:
        title: Job title
        company: Company name
        location: Job location
        description: Cleaned job description
        max_description_chars: Maximum chars for description (truncate if longer)

    Returns:
        Formatted document string
    """
    # Clean the description if not already cleaned
    if "<" in description and ">" in description:
        clean_result = clean_job_text(description)
        description = clean_result.text

    # Truncate description if too long
    if len(description) > max_description_chars:
        description = description[:max_description_chars].rsplit(" ", 1)[0] + "..."

    # Build structured document
    parts = [
        f"Title: {title.strip()}",
        f"Company: {company.strip()}",
        f"Location: {location.strip()}",
        "",
        "Description:",
        description.strip(),
    ]

    return "\n".join(parts)


def is_text_too_short(text: str, min_chars: int = 200) -> bool:
    """
    Check if text is too short for meaningful embedding.

    Args:
        text: Text to check
        min_chars: Minimum character threshold

    Returns:
        True if text is too short
    """
    if not text:
        return True
    # Count non-whitespace characters
    meaningful_chars = len(text.replace(" ", "").replace("\n", ""))
    return meaningful_chars < min_chars


def extract_skills_simple(text: str, skills_list: list[str] | None = None) -> list[str]:
    """
    Simple keyword-based skill extraction.

    Args:
        text: Text to search for skills
        skills_list: Optional list of skills to search for

    Returns:
        List of found skills (lowercase)
    """
    if skills_list is None:
        # Default common tech skills
        skills_list = [
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
            "machine learning", "deep learning", "nlp", "computer vision",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
            "git", "ci/cd", "agile", "scrum", "jira",
            "rest", "graphql", "microservices", "api",
        ]

    text_lower = text.lower()
    found_skills = []

    for skill in skills_list:
        # Use word boundary matching for more accurate detection
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill.lower())

    return sorted(set(found_skills))
