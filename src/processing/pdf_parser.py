"""PDF parsing utilities for resume extraction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pdfplumber

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from pdfplumber.page import Page

logger = get_logger(__name__)


class PDFParseError(Exception):
    """Exception raised when PDF parsing fails."""

    pass


@dataclass(frozen=True)
class ParsedResume:
    """Result of resume PDF parsing."""

    text: str
    page_count: int
    used_strategy: str  # "simple", "column_aware", "fallback"
    source_path: Path

    @property
    def char_count(self) -> int:
        """Number of characters in extracted text."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Approximate word count."""
        return len(self.text.split())


def _compute_cache_key(pdf_path: Path) -> str:
    """Compute a cache key based on file path, size, and mtime."""
    stat = pdf_path.stat()
    key_data = f"{pdf_path.absolute()}|{stat.st_size}|{stat.st_mtime}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:16]


def _extract_simple(page: "Page") -> str:
    """Simple text extraction from a page."""
    text = page.extract_text()
    return text or ""


def _extract_column_aware(page: "Page") -> str:
    """
    Column-aware text extraction for multi-column layouts.

    Uses word clustering by x-position to detect columns.
    """
    words = page.extract_words(x_tolerance=1.5, y_tolerance=3)
    if not words:
        return ""

    # Get page width to determine column threshold
    page_width = page.width
    mid_x = page_width / 2

    # Separate words into left and right columns
    left_words = []
    right_words = []

    for word in words:
        # Use the center of the word to determine column
        word_center = (word["x0"] + word["x1"]) / 2
        if word_center < mid_x:
            left_words.append(word)
        else:
            right_words.append(word)

    # Sort each column by vertical position
    left_words.sort(key=lambda w: (w["top"], w["x0"]))
    right_words.sort(key=lambda w: (w["top"], w["x0"]))

    # Build text from left column first, then right
    def words_to_text(word_list: list[dict]) -> str:
        if not word_list:
            return ""

        lines = []
        current_line = []
        current_top = None
        tolerance = 3  # pixels

        for word in word_list:
            if current_top is None:
                current_top = word["top"]
                current_line.append(word["text"])
            elif abs(word["top"] - current_top) <= tolerance:
                current_line.append(word["text"])
            else:
                lines.append(" ".join(current_line))
                current_line = [word["text"]]
                current_top = word["top"]

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    left_text = words_to_text(left_words)
    right_text = words_to_text(right_words)

    # Combine columns
    if left_text and right_text:
        return left_text + "\n\n" + right_text
    return left_text or right_text


def _is_text_garbled(text: str) -> bool:
    """
    Heuristic to detect if extracted text is garbled.

    Returns True if text appears to be poorly extracted.
    """
    if not text or len(text) < 50:
        return True

    # Check for excessive single characters (sign of broken extraction)
    words = text.split()
    if not words:
        return True

    single_char_ratio = sum(1 for w in words if len(w) == 1) / len(words)
    if single_char_ratio > 0.3:
        return True

    # Check for excessive whitespace
    whitespace_ratio = text.count(" ") / len(text)
    if whitespace_ratio > 0.5:
        return True

    return False


def parse_resume_pdf(
    pdf_path: str | Path,
    *,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
) -> ParsedResume:
    """
    Parse a resume PDF and extract text.

    Attempts simple extraction first, falls back to column-aware
    extraction if the result appears garbled.

    Args:
        pdf_path: Path to the PDF file
        cache_dir: Optional directory for caching parsed results
        use_cache: Whether to use caching (default True)

    Returns:
        ParsedResume with extracted text and metadata

    Raises:
        PDFParseError: If PDF cannot be parsed
        FileNotFoundError: If PDF file doesn't exist
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.suffix.lower() == ".pdf":
        raise PDFParseError(f"File is not a PDF: {pdf_path}")

    # Check cache
    if use_cache and cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = _compute_cache_key(pdf_path)
        cache_file = cache_dir / f"{cache_key}.txt"

        if cache_file.exists():
            logger.debug(f"Loading cached resume text from {cache_file}")
            cached_text = cache_file.read_text(encoding="utf-8")
            # We don't cache page_count/strategy, so use defaults
            return ParsedResume(
                text=cached_text,
                page_count=0,  # Unknown from cache
                used_strategy="cached",
                source_path=pdf_path,
            )

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            all_text_parts = []
            used_strategy = "simple"

            for i, page in enumerate(pdf.pages):
                # Try simple extraction first
                text = _extract_simple(page)

                # If garbled, try column-aware extraction
                if _is_text_garbled(text):
                    logger.debug(f"Page {i + 1}: Simple extraction garbled, trying column-aware")
                    text = _extract_column_aware(page)
                    if text:
                        used_strategy = "column_aware"

                if text:
                    all_text_parts.append(text)

            full_text = "\n\n".join(all_text_parts)

            # Final cleanup
            full_text = full_text.strip()

            if not full_text:
                raise PDFParseError(f"No text could be extracted from {pdf_path}")

            result = ParsedResume(
                text=full_text,
                page_count=page_count,
                used_strategy=used_strategy,
                source_path=pdf_path,
            )

            # Save to cache
            if use_cache and cache_dir:
                cache_dir = Path(cache_dir)
                cache_key = _compute_cache_key(pdf_path)
                cache_file = cache_dir / f"{cache_key}.txt"
                cache_file.write_text(full_text, encoding="utf-8")
                logger.debug(f"Cached resume text to {cache_file}")

            logger.info(
                f"Parsed resume: {page_count} pages, {result.word_count} words, "
                f"strategy={used_strategy}"
            )

            return result

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
        raise PDFParseError(f"Invalid PDF syntax: {e}") from e
    except Exception as e:
        if isinstance(e, (PDFParseError, FileNotFoundError)):
            raise
        raise PDFParseError(f"Failed to parse PDF: {e}") from e


def parse_resume_text(text: str, source_name: str = "manual_input") -> ParsedResume:
    """
    Create a ParsedResume from raw text (for manual input).

    Args:
        text: Resume text
        source_name: Name to identify the source

    Returns:
        ParsedResume object
    """
    return ParsedResume(
        text=text.strip(),
        page_count=1,
        used_strategy="text_input",
        source_path=Path(source_name),
    )
