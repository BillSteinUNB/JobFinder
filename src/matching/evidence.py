"""Evidence extraction for explainable job matching."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

import numpy as np

from src.processing.text_cleaner import extract_skills_simple
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.matching.embeddings import EmbeddingManager

logger = get_logger(__name__)


@dataclass
class EvidenceMatch:
    """A single piece of evidence linking resume to job."""
    
    resume_sentence: str
    job_sentence: str
    similarity: float
    match_type: str  # "semantic", "skill", "keyword"
    matched_terms: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.matched_terms = sorted(set(self.matched_terms))


@dataclass
class EvidenceResult:
    """Complete evidence extraction result for a job match."""
    
    job_id: str
    matches: list[EvidenceMatch]
    top_resume_sentences: list[str]
    top_job_sentences: list[str]
    skill_matches: list[str]
    keyword_matches: list[str]
    
    @property
    def match_count(self) -> int:
        """Total number of evidence matches."""
        return len(self.matches)
    
    @property
    def avg_similarity(self) -> float:
        """Average similarity across all matches."""
        if not self.matches:
            return 0.0
        return sum(m.similarity for m in self.matches) / len(self.matches)


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences.
    
    Uses simple regex-based splitting with cleanup.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Split on sentence boundaries
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(pattern, text)
    
    # Clean up and filter
    cleaned = []
    for sent in sentences:
        sent = sent.strip()
        # Skip very short sentences
        if len(sent) < 20:
            continue
        # Skip sentences that are just bullet points or headers
        if sent.startswith(('-', '*', '•', '–')) and len(sent) < 50:
            continue
        cleaned.append(sent)
    
    return cleaned


def extract_keywords(text: str, min_length: int = 4) -> set[str]:
    """
    Extract meaningful keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum word length to include
        
    Returns:
        Set of lowercase keywords
    """
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
        'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every',
        'both', 'few', 'more', 'most', 'other', 'some', 'such', 'than',
        'too', 'very', 'just', 'also', 'only', 'own', 'same', 'into',
        'over', 'after', 'before', 'between', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'about', 'through', 'during',
        'above', 'below', 'your', 'you', 'their', 'they', 'our', 'we',
        'work', 'working', 'experience', 'team', 'ability', 'skills',
        'strong', 'excellent', 'good', 'great', 'best', 'well', 'new',
        'years', 'year', 'role', 'position', 'company', 'looking',
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter
    keywords = {
        word for word in words
        if len(word) >= min_length and word not in stop_words
    }
    
    return keywords


class EvidenceExtractor:
    """
    Extracts evidence explaining why a job matches a resume.
    
    Uses a combination of:
    1. Semantic similarity between sentences
    2. Skill term matching
    3. Keyword overlap
    """
    
    def __init__(
        self,
        embedding_manager: "EmbeddingManager | None" = None,
        top_k_sentences: int = 5,
        similarity_threshold: float = 0.5,
    ):
        """
        Initialize the evidence extractor.
        
        Args:
            embedding_manager: Optional embedding manager for semantic matching
            top_k_sentences: Number of top matching sentences to return
            similarity_threshold: Minimum similarity for a match
        """
        self._embedding_manager = embedding_manager
        self._top_k = top_k_sentences
        self._threshold = similarity_threshold
    
    def extract_skill_evidence(
        self,
        resume_text: str,
        job_text: str,
    ) -> tuple[list[str], list[str]]:
        """
        Extract skill-based evidence.
        
        Returns:
            Tuple of (matched_skills, job_only_skills)
        """
        resume_skills = set(extract_skills_simple(resume_text))
        job_skills = set(extract_skills_simple(job_text))
        
        matched = sorted(resume_skills & job_skills)
        job_only = sorted(job_skills - resume_skills)
        
        return matched, job_only
    
    def extract_keyword_evidence(
        self,
        resume_text: str,
        job_text: str,
    ) -> list[str]:
        """
        Extract keyword-based evidence.
        
        Returns:
            List of overlapping keywords
        """
        resume_keywords = extract_keywords(resume_text)
        job_keywords = extract_keywords(job_text)
        
        # Find overlap (prioritize longer/more specific terms)
        overlap = resume_keywords & job_keywords
        
        # Sort by length (longer = more specific) then alphabetically
        return sorted(overlap, key=lambda x: (-len(x), x))[:20]
    
    def extract_semantic_evidence(
        self,
        resume_text: str,
        job_text: str,
    ) -> list[EvidenceMatch]:
        """
        Extract semantic evidence using sentence embeddings.
        
        Returns:
            List of EvidenceMatch objects
        """
        if self._embedding_manager is None:
            return []
        
        # Split into sentences
        resume_sentences = split_into_sentences(resume_text)
        job_sentences = split_into_sentences(job_text)
        
        if not resume_sentences or not job_sentences:
            return []
        
        # Limit sentences for performance
        resume_sentences = resume_sentences[:30]
        job_sentences = job_sentences[:30]
        
        # Embed all sentences
        try:
            resume_embeddings = self._embedding_manager.embed_texts(resume_sentences)
            job_embeddings = self._embedding_manager.embed_texts(job_sentences)
        except Exception as e:
            logger.warning(f"Failed to embed sentences: {e}")
            return []
        
        # Compute similarity matrix
        # Embeddings are normalized, so dot product = cosine similarity
        similarity_matrix = np.dot(resume_embeddings, job_embeddings.T)
        
        # Find top matches
        matches = []
        
        # For each job sentence, find best matching resume sentence
        for j, job_sent in enumerate(job_sentences):
            similarities = similarity_matrix[:, j]
            best_i = int(np.argmax(similarities))
            best_sim = float(similarities[best_i])
            
            if best_sim >= self._threshold:
                matches.append(EvidenceMatch(
                    resume_sentence=resume_sentences[best_i],
                    job_sentence=job_sent,
                    similarity=best_sim,
                    match_type="semantic",
                ))
        
        # Sort by similarity and take top K
        matches.sort(key=lambda x: x.similarity, reverse=True)
        return matches[:self._top_k]
    
    def extract_evidence(
        self,
        job_id: str,
        resume_text: str,
        job_text: str,
    ) -> EvidenceResult:
        """
        Extract all types of evidence for a job match.
        
        Args:
            job_id: Job identifier
            resume_text: Cleaned resume text
            job_text: Cleaned job description text
            
        Returns:
            EvidenceResult with all evidence types
        """
        # Skill evidence
        skill_matches, _ = self.extract_skill_evidence(resume_text, job_text)
        
        # Keyword evidence
        keyword_matches = self.extract_keyword_evidence(resume_text, job_text)
        
        # Semantic evidence
        semantic_matches = self.extract_semantic_evidence(resume_text, job_text)
        
        # Create skill-based matches
        all_matches = list(semantic_matches)
        
        # Add skill matches as evidence
        resume_sentences = split_into_sentences(resume_text)
        job_sentences = split_into_sentences(job_text)
        
        for skill in skill_matches[:5]:  # Top 5 skills
            # Find sentences containing this skill
            resume_sent = next(
                (s for s in resume_sentences if skill.lower() in s.lower()),
                f"Resume mentions: {skill}"
            )
            job_sent = next(
                (s for s in job_sentences if skill.lower() in s.lower()),
                f"Job requires: {skill}"
            )
            
            all_matches.append(EvidenceMatch(
                resume_sentence=resume_sent,
                job_sentence=job_sent,
                similarity=1.0,  # Exact skill match
                match_type="skill",
                matched_terms=[skill],
            ))
        
        # Get top sentences
        top_resume = [m.resume_sentence for m in all_matches[:self._top_k]]
        top_job = [m.job_sentence for m in all_matches[:self._top_k]]
        
        return EvidenceResult(
            job_id=job_id,
            matches=all_matches,
            top_resume_sentences=list(dict.fromkeys(top_resume)),  # Dedupe
            top_job_sentences=list(dict.fromkeys(top_job)),
            skill_matches=skill_matches,
            keyword_matches=keyword_matches,
        )
    
    def extract_evidence_batch(
        self,
        job_ids: Sequence[str],
        resume_text: str,
        job_texts: Sequence[str],
    ) -> dict[str, EvidenceResult]:
        """
        Extract evidence for multiple jobs.
        
        Args:
            job_ids: Job identifiers
            resume_text: Cleaned resume text
            job_texts: Cleaned job description texts
            
        Returns:
            Dictionary mapping job_id to EvidenceResult
        """
        results = {}
        
        for job_id, job_text in zip(job_ids, job_texts):
            results[job_id] = self.extract_evidence(job_id, resume_text, job_text)
        
        return results


def highlight_text(text: str, terms: list[str], highlight_class: str = "highlight") -> str:
    """
    Add HTML highlighting to matching terms in text.
    
    Args:
        text: Text to highlight
        terms: Terms to highlight
        highlight_class: CSS class for highlight spans
        
    Returns:
        HTML string with highlighted terms
    """
    if not terms:
        return html.escape(text)
    
    # Escape HTML in source text first to prevent XSS
    safe_text = html.escape(text)
    
    for term in terms:
        # Escape the term for safe regex and HTML
        safe_term = html.escape(term)
        # Case-insensitive replacement with highlighting
        pattern = re.compile(re.escape(safe_term), re.IGNORECASE)
        safe_text = pattern.sub(
            f'<span class="{html.escape(highlight_class)}" style="background-color: #fff3cd; '
            f'padding: 1px 3px; border-radius: 3px; font-weight: 500;">'
            f'\\g<0></span>',
            safe_text
        )
    
    return safe_text
